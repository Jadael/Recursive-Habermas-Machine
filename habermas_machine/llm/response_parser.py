"""
Response parsing utilities for the Habermas Machine.

This module handles parsing LLM responses, including:
- JSON extraction and validation
- Model-specific cleaning (e.g., DeepSeek think tags)
- Retry logic for unreliable outputs

Copyright (C) 2025  Habermas Machine Project

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

import json
import re
import logging
import ast
import random
from typing import Optional, List, Tuple, Dict, Any

logger = logging.getLogger(__name__)


def clean_deepseek_response(response: str) -> str:
    """
    Remove DeepSeek-R1 specific artifacts from response.

    DeepSeek-R1 often wraps its chain-of-thought reasoning in <think> tags.
    These need to be stripped to get the actual response.

    Args:
        response: Raw response from the LLM

    Returns:
        Cleaned response with think tags removed

    Example:
        >>> raw = "<think>Let me consider...</think>Here is my answer"
        >>> clean_deepseek_response(raw)
        'Here is my answer'
    """
    # Remove <think>...</think> tags and their contents
    cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    return cleaned.strip()


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract a JSON object from text that may contain additional content.

    LLMs often generate explanatory text before/after JSON. This function
    attempts to find and extract the JSON object using regex.

    Args:
        text: Text potentially containing a JSON object

    Returns:
        Parsed JSON object as dict, or None if no valid JSON found

    Example:
        >>> text = "Here's the ranking: {'ranking': [1, 2, 3]} - hope that helps!"
        >>> extract_json_from_text(text)
        {'ranking': [1, 2, 3]}
    """
    # Try to find a JSON object pattern in the text
    match = re.search(r'({[\s\S]*?})', text)
    if not match:
        return None

    json_str = match.group(1)

    # Try json.loads first (standard JSON)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Try ast.literal_eval as fallback (Python dict syntax)
    try:
        return ast.literal_eval(json_str)
    except (ValueError, SyntaxError):
        pass

    return None


def validate_ranking(
    ranking: List[int],
    num_candidates: int,
    zero_indexed: bool = True
) -> bool:
    """
    Validate that a ranking is well-formed.

    A valid ranking must:
    1. Contain exactly num_candidates elements
    2. Contain each index exactly once (no duplicates)
    3. Use the correct indexing (0-based or 1-based)

    Args:
        ranking: List of candidate indices in preference order
        num_candidates: Expected number of candidates
        zero_indexed: If True, expects indices 0..n-1; if False, expects 1..n

    Returns:
        True if ranking is valid, False otherwise

    Example:
        >>> validate_ranking([0, 2, 1], 3, zero_indexed=True)
        True
        >>> validate_ranking([1, 3, 2], 3, zero_indexed=True)
        False  # Should be 0-indexed
        >>> validate_ranking([1, 3, 2], 3, zero_indexed=False)
        True
    """
    if len(ranking) != num_candidates:
        return False

    expected_indices = set(range(num_candidates) if zero_indexed else range(1, num_candidates + 1))
    return set(ranking) == expected_indices


def parse_ranking_response(
    response: str,
    num_candidates: int,
    max_retries: int = 1,
    attempt_num: int = 1
) -> Tuple[Optional[List[int]], str]:
    """
    Parse a ranking from LLM response with error handling.

    This function attempts to extract and validate a ranking from the response.
    It handles various edge cases like model-specific artifacts, JSON parsing
    errors, and invalid rankings.

    Args:
        response: Raw response from the LLM
        num_candidates: Expected number of candidates
        max_retries: Maximum retry attempts (for logging context)
        attempt_num: Current attempt number (for logging)

    Returns:
        Tuple of (ranking, log_message):
        - ranking: List of 0-indexed candidate indices, or None if parsing failed
        - log_message: Description of what happened during parsing

    Example:
        >>> response = '{"ranking": [1, 2, 3]}'
        >>> ranking, log = parse_ranking_response(response, 3)
        >>> ranking
        [0, 1, 2]  # Converted from 1-indexed to 0-indexed
    """
    # Clean DeepSeek artifacts
    clean_response = clean_deepseek_response(response)

    # Try to extract JSON
    ranking_data = extract_json_from_text(clean_response)

    if ranking_data is None:
        return None, f"Attempt {attempt_num}/{max_retries}: No valid JSON found in response"

    # Check for 'ranking' field
    if "ranking" not in ranking_data:
        return None, f"Attempt {attempt_num}/{max_retries}: JSON missing 'ranking' field"

    raw_ranking = ranking_data["ranking"]

    # Verify it's a list
    if not isinstance(raw_ranking, list):
        return None, f"Attempt {attempt_num}/{max_retries}: 'ranking' field is not a list"

    # Try to convert elements to integers
    try:
        ranking = [int(x) for x in raw_ranking]
    except (ValueError, TypeError):
        return None, f"Attempt {attempt_num}/{max_retries}: Ranking contains non-integer values"

    # Check if it's 1-indexed (as expected from the prompt)
    if validate_ranking(ranking, num_candidates, zero_indexed=False):
        # Convert from 1-indexed to 0-indexed
        ranking_zero_indexed = [x - 1 for x in ranking]
        return ranking_zero_indexed, f"Attempt {attempt_num}/{max_retries}: Success! Valid ranking: {ranking}"

    # Check if it's already 0-indexed
    if validate_ranking(ranking, num_candidates, zero_indexed=True):
        logger.warning(f"Model returned 0-indexed ranking (expected 1-indexed): {ranking}")
        return ranking, f"Attempt {attempt_num}/{max_retries}: Success (0-indexed ranking): {ranking}"

    # Invalid ranking
    return None, f"Attempt {attempt_num}/{max_retries}: Invalid ranking indices: {ranking}"


def create_random_ranking(num_candidates: int) -> List[int]:
    """
    Create a random ranking as fallback.

    When all parsing attempts fail, we fall back to a random ranking.
    This is logged extensively so users know when it happens.

    Args:
        num_candidates: Number of candidates to rank

    Returns:
        Random permutation of candidate indices (0-indexed)

    Example:
        >>> random.seed(42)
        >>> create_random_ranking(3)
        [1, 0, 2]  # Random order
    """
    ranking = list(range(num_candidates))
    random.shuffle(ranking)
    return ranking


def create_ranking_system_prompt(num_candidates: int) -> str:
    """
    Create a system prompt instructing the model to output JSON rankings.

    This prompt provides clear instructions and a randomized example to
    avoid biasing the model toward any particular ranking.

    Args:
        num_candidates: Number of candidates being ranked

    Returns:
        System prompt string

    Example:
        >>> prompt = create_ranking_system_prompt(4)
        >>> "JSON" in prompt
        True
        >>> "ranking" in prompt
        True
    """
    # Generate a non-biasing example with a different number of candidates
    example_size = max(3, num_candidates - 1)
    example_ranking = list(range(1, example_size + 1))
    random.shuffle(example_ranking)  # Randomize to avoid bias

    prompt = f"""You are a helpful assistant that predicts how a person would rank options based on their stated views.

Your task is to output ONLY a JSON object with this exact format:

{{"ranking": [1, 2, 3, ...]}}

The "ranking" should be a list of {num_candidates} numbers from 1 to {num_candidates}, where:
- The first number is the most preferred option
- The last number is the least preferred option
- Each number from 1 to {num_candidates} appears exactly once

Example (for {example_size} options):
{{"ranking": {example_ranking}}}

Do not include any explanation, just output the JSON object."""

    return prompt


class RankingParser:
    """
    Stateful parser for extracting rankings from LLM responses.

    This class manages the retry logic and logging for ranking predictions.
    """

    def __init__(self, num_candidates: int, max_retries: int = 3):
        """
        Initialize the ranking parser.

        Args:
            num_candidates: Number of candidates being ranked
            max_retries: Maximum number of parsing attempts
        """
        self.num_candidates = num_candidates
        self.max_retries = max_retries
        self.attempts_log: List[str] = []

    def parse(
        self,
        response: str,
        attempt_num: int
    ) -> Optional[List[int]]:
        """
        Parse a ranking from response and log the result.

        Args:
            response: Raw LLM response
            attempt_num: Current attempt number (1-indexed)

        Returns:
            0-indexed ranking list, or None if parsing failed
        """
        ranking, log_msg = parse_ranking_response(
            response,
            self.num_candidates,
            self.max_retries,
            attempt_num
        )

        self.attempts_log.append(log_msg)

        if ranking is not None:
            logger.info(f"Successfully parsed ranking on attempt {attempt_num}")
        else:
            logger.warning(f"Failed to parse ranking on attempt {attempt_num}: {log_msg}")

        return ranking

    def get_fallback_ranking(self) -> Tuple[List[int], List[str]]:
        """
        Get a random fallback ranking when all attempts fail.

        Returns:
            Tuple of (random_ranking, attempts_log)
        """
        fallback_msg = "All parsing attempts failed. Using random ranking as fallback."
        self.attempts_log.append(fallback_msg)
        logger.warning(fallback_msg)

        ranking = create_random_ranking(self.num_candidates)
        return ranking, self.attempts_log

    def get_successful_ranking(
        self,
        ranking: List[int]
    ) -> Tuple[List[int], List[str]]:
        """
        Return a successfully parsed ranking with its log.

        Args:
            ranking: The successfully parsed ranking

        Returns:
            Tuple of (ranking, attempts_log)
        """
        return ranking, self.attempts_log

    def reset(self):
        """Clear the attempts log for a new prediction."""
        self.attempts_log = []
