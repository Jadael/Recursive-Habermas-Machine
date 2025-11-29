"""
Voting and social choice methods for consensus selection.

Implements the Schulze method (Condorcet-compliant, clone-independent) for
selecting consensus statements based on participant preference rankings.
"""

from typing import Dict, List, Tuple, Set


def schulze_method(rankings: Dict[int, List[int]], num_candidates: int) -> Tuple[int, List[List[int]], List[List[int]]]:
    """
    Implementation of the Schulze voting method.

    The Schulze method is a Condorcet-compliant voting system that selects the candidate
    who would win a head-to-head election against every other candidate. It's clone-independent
    and resistant to tactical voting.

    Args:
        rankings: Dictionary where keys are participant indexes and values are lists of candidate indexes
                 in order of preference (most preferred first, e.g., [2, 0, 1, 3] means candidate 2 is
                 most preferred, then 0, then 1, then 3)
        num_candidates: Total number of candidates

    Returns:
        Tuple of (winner_idx, pairwise_matrix, strongest_paths)
        - winner_idx: Index of the winning candidate
        - pairwise_matrix: Matrix where [i][j] is the number of voters who prefer candidate i over j
        - strongest_paths: Matrix of strongest path strengths calculated by Floyd-Warshall algorithm

    Example:
        >>> rankings = {0: [1, 0, 2], 1: [0, 1, 2], 2: [1, 2, 0]}
        >>> winner, pairwise, paths = schulze_method(rankings, 3)
        >>> print(f"Winner: Candidate {winner}")
    """
    # Step 1: Initialize the pairwise preference matrix
    # pairwise_matrix[i][j] = number of voters who prefer candidate i over candidate j
    pairwise_matrix = [[0 for _ in range(num_candidates)] for _ in range(num_candidates)]

    # Step 2: For each voter, count pairwise preferences
    for p_idx, ranking in rankings.items():
        # For each pair of candidates in the voter's ranking
        for i in range(len(ranking)):
            for j in range(i + 1, len(ranking)):
                # The candidate at ranking[i] is preferred over the candidate at ranking[j]
                preferred = ranking[i]
                not_preferred = ranking[j]
                pairwise_matrix[preferred][not_preferred] += 1

    # Step 3: Find the strongest paths using Floyd-Warshall algorithm
    # strongest_paths[i][j] = strength of the strongest path from candidate i to candidate j
    strongest_paths = [[0 for _ in range(num_candidates)] for _ in range(num_candidates)]

    # Initialize with direct pairwise preferences
    for i in range(num_candidates):
        for j in range(num_candidates):
            if i != j:
                strongest_paths[i][j] = pairwise_matrix[i][j]

    # Calculate strongest paths using Floyd-Warshall
    # For each intermediate candidate i
    for i in range(num_candidates):
        # For each starting candidate j
        for j in range(num_candidates):
            if i != j:
                # For each ending candidate k
                for k in range(num_candidates):
                    if i != k and j != k:
                        # Update the strongest path from j to k through i
                        # The strength of a path is the minimum strength along that path
                        strongest_paths[j][k] = max(
                            strongest_paths[j][k],
                            min(strongest_paths[j][i], strongest_paths[i][k])
                        )

    # Step 4: Determine the winner
    # A candidate is a Condorcet winner if their strongest path to every other candidate
    # is stronger than or equal to the strongest path from each other candidate to them
    potential_winners = set(range(num_candidates))

    for i in range(num_candidates):
        for j in range(num_candidates):
            if i != j and strongest_paths[j][i] > strongest_paths[i][j]:
                # Candidate j beats candidate i, so i cannot be the winner
                if i in potential_winners:
                    potential_winners.remove(i)

    # Return the winner with the lowest index (arbitrary tie-breaking if multiple winners)
    winner_idx = min(potential_winners) if potential_winners else 0

    return winner_idx, pairwise_matrix, strongest_paths


def format_ranking_results(winner_idx: int, candidate_statements: List[str],
                          pairwise_matrix: List[List[int]],
                          strongest_paths: List[List[int]]) -> str:
    """
    Format Schulze voting results as a human-readable report.

    Args:
        winner_idx: Index of the winning candidate
        candidate_statements: List of candidate statements
        pairwise_matrix: Pairwise preference matrix
        strongest_paths: Strongest paths matrix

    Returns:
        Formatted markdown string with election results
    """
    num_candidates = len(candidate_statements)

    output = "## Election Results\n\n"
    output += f"**Winner: Candidate {winner_idx + 1}**\n\n"
    output += f"> {candidate_statements[winner_idx]}\n\n"

    output += "### How the Winner Was Determined\n\n"
    output += ("The consensus was determined using the Schulze method, a well-established voting system that "
               "compares how each participant would rank the different statements. This method ensures that "
               "the winning statement is one that is broadly acceptable to all participants, even if it wasn't "
               "everyone's first choice.\n\n")

    # Calculate victories for each candidate
    victories = {}
    for i in range(num_candidates):
        victories[i] = 0
        for j in range(num_candidates):
            if i != j and strongest_paths[i][j] > strongest_paths[j][i]:
                victories[i] += 1

    # Sort candidates by number of victories
    sorted_candidates = sorted(victories.items(), key=lambda x: x[1], reverse=True)

    output += "### Candidate Rankings\n\n"
    output += "Based on the Schulze method, here's how the candidates performed:\n\n"

    for rank, (cand_idx, num_victories) in enumerate(sorted_candidates, 1):
        marker = "🏆 " if cand_idx == winner_idx else "   "
        output += f"{marker}**{rank}. Candidate {cand_idx + 1}** - Won against {num_victories} other candidate(s)\n"
        output += f"   {candidate_statements[cand_idx][:100]}{'...' if len(candidate_statements[cand_idx]) > 100 else ''}\n\n"

    return output


def format_pairwise_matrix(pairwise_matrix: List[List[int]], num_candidates: int) -> str:
    """
    Format the pairwise preference matrix as a markdown table.

    Args:
        pairwise_matrix: Matrix of pairwise preferences
        num_candidates: Number of candidates

    Returns:
        Formatted markdown table
    """
    output = "### Pairwise Preference Matrix\n\n"
    output += "This matrix shows how many participants preferred each candidate over each other candidate.\n\n"
    output += "Row candidate is preferred over column candidate by the number shown:\n\n"

    # Header row
    output += "|     |"
    for j in range(num_candidates):
        output += f" C{j + 1} |"
    output += "\n"

    # Separator row
    output += "|-----|"
    for _ in range(num_candidates):
        output += "----:|"
    output += "\n"

    # Data rows
    for i in range(num_candidates):
        output += f"| **C{i + 1}** |"
        for j in range(num_candidates):
            if i == j:
                output += "  - |"
            else:
                output += f" {pairwise_matrix[i][j]:2d} |"
        output += "\n"

    output += "\n"
    return output


def format_strongest_paths(strongest_paths: List[List[int]], num_candidates: int) -> str:
    """
    Format the strongest paths matrix as a markdown table.

    Args:
        strongest_paths: Matrix of strongest path strengths
        num_candidates: Number of candidates

    Returns:
        Formatted markdown table
    """
    output = "### Strongest Paths Matrix\n\n"
    output += "This matrix shows the strength of the strongest path from each candidate to each other candidate.\n\n"

    # Header row
    output += "|     |"
    for j in range(num_candidates):
        output += f" C{j + 1} |"
    output += "\n"

    # Separator row
    output += "|-----|"
    for _ in range(num_candidates):
        output += "----:|"
    output += "\n"

    # Data rows
    for i in range(num_candidates):
        output += f"| **C{i + 1}** |"
        for j in range(num_candidates):
            if i == j:
                output += "  - |"
            else:
                output += f" {strongest_paths[i][j]:2d} |"
        output += "\n"

    output += "\n"
    return output


def validate_rankings(rankings: Dict[int, List[int]], num_candidates: int) -> bool:
    """
    Validate that rankings dictionary is properly formatted.

    Args:
        rankings: Dictionary of participant rankings
        num_candidates: Expected number of candidates

    Returns:
        True if valid, False otherwise
    """
    for p_idx, ranking in rankings.items():
        # Check that ranking is a list
        if not isinstance(ranking, list):
            return False

        # Check that ranking has the right length
        if len(ranking) != num_candidates:
            return False

        # Check that all candidate indices are present
        if set(ranking) != set(range(num_candidates)):
            return False

    return True


def tie_break_random(potential_winners: Set[int], seed: int = None) -> int:
    """
    Break ties randomly among potential winners.

    Args:
        potential_winners: Set of candidate indices that are tied
        seed: Optional random seed for reproducibility

    Returns:
        Index of randomly selected winner
    """
    import random
    if seed is not None:
        random.seed(seed)
    return random.choice(list(potential_winners))


def tie_break_lowest_index(potential_winners: Set[int]) -> int:
    """
    Break ties by selecting the candidate with the lowest index.

    Args:
        potential_winners: Set of candidate indices that are tied

    Returns:
        Index of winner (lowest index)
    """
    return min(potential_winners) if potential_winners else 0
