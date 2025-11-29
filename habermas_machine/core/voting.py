"""
Voting algorithms for the Habermas Machine.

This module implements the Schulze voting method and related election utilities
for determining consensus from ranked preferences.

Copyright (C) 2025  Habermas Machine Project

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from typing import Dict, List, Tuple, Set
from collections import defaultdict


def schulze_method(
    rankings: Dict[int, List[int]],
    num_candidates: int
) -> Tuple[int, List[List[int]], List[List[int]]]:
    """
    Implementation of the Schulze voting method (Condorcet-compliant).

    The Schulze method is a voting system that:
    - Satisfies the Condorcet criterion (elects the Condorcet winner if one exists)
    - Is clone-independent (adding similar candidates doesn't change results unfairly)
    - Resists strategic voting better than simpler methods

    Algorithm:
    1. Build pairwise preference matrix from individual rankings
    2. Calculate strongest paths using Floyd-Warshall algorithm
    3. Determine winner: candidate i wins if for all j≠i,
       strongest_path[i][j] ≥ strongest_path[j][i]

    Args:
        rankings: Dictionary mapping participant indices to lists of candidate indices
                 in preference order (most preferred first)
                 Example: {0: [2, 0, 1], 1: [1, 2, 0]} means:
                   - Participant 0 prefers candidate 2, then 0, then 1
                   - Participant 1 prefers candidate 1, then 2, then 0
        num_candidates: Total number of candidates in the election

    Returns:
        Tuple of (winner_idx, pairwise_matrix, strongest_paths):
        - winner_idx: Index of the winning candidate
        - pairwise_matrix: 2D list showing pairwise preferences
                          (element [i][j] = how many voters prefer i over j)
        - strongest_paths: 2D list of strongest path strengths between candidates

    Example:
        >>> rankings = {0: [1, 0, 2], 1: [1, 2, 0], 2: [0, 1, 2]}
        >>> winner, pairwise, paths = schulze_method(rankings, 3)
        >>> print(f"Winner: Candidate {winner}")
    """
    # Step 1: Initialize the pairwise preference matrix
    # pairwise_matrix[i][j] = number of voters who prefer candidate i over candidate j
    pairwise_matrix = [[0 for _ in range(num_candidates)] for _ in range(num_candidates)]

    # Step 2: Populate pairwise preferences from individual rankings
    for participant_idx, ranking in rankings.items():
        # For each pair of candidates in this voter's ranking
        for i in range(len(ranking)):
            for j in range(i + 1, len(ranking)):
                # Candidate at ranking[i] is preferred over candidate at ranking[j]
                preferred_candidate = ranking[i]
                less_preferred_candidate = ranking[j]
                pairwise_matrix[preferred_candidate][less_preferred_candidate] += 1

    # Step 3: Calculate strongest paths using Floyd-Warshall algorithm
    # strongest_paths[i][j] = strength of the strongest path from candidate i to j
    strongest_paths = [[0 for _ in range(num_candidates)] for _ in range(num_candidates)]

    # Initialize with direct pairwise preferences
    for i in range(num_candidates):
        for j in range(num_candidates):
            if i != j:
                strongest_paths[i][j] = pairwise_matrix[i][j]

    # Floyd-Warshall: find strongest indirect paths
    # For each intermediate candidate i
    for i in range(num_candidates):
        # For each source candidate j
        for j in range(num_candidates):
            if i != j:
                # For each destination candidate k
                for k in range(num_candidates):
                    if i != k and j != k:
                        # The strongest path from j to k is either:
                        # 1. The current path from j to k, OR
                        # 2. The path j→i→k (taking the minimum strength link)
                        strongest_paths[j][k] = max(
                            strongest_paths[j][k],
                            min(strongest_paths[j][i], strongest_paths[i][k])
                        )

    # Step 4: Determine the winner
    # A candidate wins if their strongest path to every other candidate
    # is ≥ the strongest path from that candidate back to them
    potential_winners: Set[int] = set(range(num_candidates))

    for i in range(num_candidates):
        for j in range(num_candidates):
            if i != j:
                # If candidate j has a strictly stronger path to i than i has to j,
                # then i cannot be the winner
                if strongest_paths[j][i] > strongest_paths[i][j]:
                    potential_winners.discard(i)

    # Return the winner with the lowest index (deterministic tiebreaker)
    winner_idx = min(potential_winners) if potential_winners else 0

    return winner_idx, pairwise_matrix, strongest_paths


def calculate_victories(
    strongest_paths: List[List[int]],
    num_candidates: int
) -> Dict[int, int]:
    """
    Calculate how many pairwise victories each candidate has.

    A candidate i "defeats" candidate j if the strongest path from i to j
    is stronger than the path from j to i.

    Args:
        strongest_paths: 2D list of strongest path strengths (from schulze_method)
        num_candidates: Total number of candidates

    Returns:
        Dictionary mapping candidate index to number of victories

    Example:
        >>> paths = [[0, 5, 3], [2, 0, 4], [3, 2, 0]]
        >>> victories = calculate_victories(paths, 3)
        >>> sorted(victories.items())
        [(0, 1), (1, 1), (2, 1)]
    """
    victories = defaultdict(int)

    for i in range(num_candidates):
        for j in range(num_candidates):
            if i != j and strongest_paths[i][j] > strongest_paths[j][i]:
                victories[i] += 1

    return victories


def rank_candidates_by_victories(
    strongest_paths: List[List[int]],
    num_candidates: int
) -> List[int]:
    """
    Rank candidates by number of pairwise victories (descending).

    This provides a full ranking of all candidates, not just the winner.
    Useful for displaying results and understanding the preference structure.

    Args:
        strongest_paths: 2D list of strongest path strengths
        num_candidates: Total number of candidates

    Returns:
        List of candidate indices sorted by victories (most victories first)

    Example:
        >>> paths = [[0, 5, 3], [2, 0, 4], [3, 2, 0]]
        >>> rank_candidates_by_victories(paths, 3)
        [0, 1, 2]  # or similar, depending on the actual paths
    """
    victories = calculate_victories(strongest_paths, num_candidates)

    # Sort candidates by victory count (descending), breaking ties by index (ascending)
    ranked = sorted(
        range(num_candidates),
        key=lambda candidate_idx: (-victories[candidate_idx], candidate_idx)
    )

    return ranked


def format_pairwise_matrix(
    pairwise_matrix: List[List[int]],
    num_candidates: int
) -> str:
    """
    Format pairwise preference matrix as a readable markdown table.

    Args:
        pairwise_matrix: 2D list of pairwise preferences
        num_candidates: Total number of candidates

    Returns:
        Markdown-formatted string representing the matrix

    Example:
        >>> matrix = [[0, 5, 3], [2, 0, 4], [3, 2, 0]]
        >>> print(format_pairwise_matrix(matrix, 3))
        |       | S 1 | S 2 | S 3 |
        |-------|-----|-----|-----|
        | S 1   |  0  |  5  |  3  |
        | S 2   |  2  |  0  |  4  |
        | S 3   |  3  |  2  |  0  |
    """
    # Header row
    header = "|       |"
    for i in range(num_candidates):
        header += f" S{i+1:2d} |"

    # Separator row
    separator = "|-------|"
    for _ in range(num_candidates):
        separator += "-----|"

    # Data rows
    rows = [header, separator]
    for i in range(num_candidates):
        row = f"| S{i+1:2d}   |"
        for j in range(num_candidates):
            row += f" {pairwise_matrix[i][j]:3d} |"
        rows.append(row)

    return "\n".join(rows)


def format_strongest_paths_matrix(
    strongest_paths: List[List[int]],
    num_candidates: int
) -> str:
    """
    Format strongest paths matrix as a readable markdown table.

    Args:
        strongest_paths: 2D list of strongest path strengths
        num_candidates: Total number of candidates

    Returns:
        Markdown-formatted string representing the matrix
    """
    # Same format as pairwise matrix
    header = "|       |"
    for i in range(num_candidates):
        header += f" S{i+1:2d} |"

    separator = "|-------|"
    for _ in range(num_candidates):
        separator += "-----|"

    rows = [header, separator]
    for i in range(num_candidates):
        row = f"| S{i+1:2d}   |"
        for j in range(num_candidates):
            row += f" {strongest_paths[i][j]:3d} |"
        rows.append(row)

    return "\n".join(rows)
