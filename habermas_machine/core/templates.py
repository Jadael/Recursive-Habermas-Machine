"""
Prompt templates for the Habermas Machine.

This module contains default prompt templates for:
- Generating candidate consensus statements
- Predicting participant rankings
- Other LLM interactions

Copyright (C) 2025  Habermas Machine Project

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from typing import Dict

# ============================================================================
# Default Prompt Templates
# ============================================================================

DEFAULT_CANDIDATE_GENERATION_TEMPLATE = """Your task is to synthesize a consensus statement from multiple individual opinions on a question. The statement should capture common ground and shared perspectives while respecting each person's viewpoint.

The statement should be written in the voice of the group expressing their collective view (e.g., "We believe...", "Our position is..."), not as an outside description of what they think.

Key requirements:
- The statement must NOT conflict with any individual opinion
- Identify key themes and points of agreement across the opinions
- Include relevant details, concerns, and suggestions that appear across multiple opinions
- Use natural language that reflects the tone and style of the original opinions
- Write as the group, not about the group

Process:
1. Note recurring themes and shared values
2. Identify areas of agreement and how different perspectives relate
3. Synthesize a statement that represents this common ground
4. Ensure no individual opinion is contradicted

Example: If several opinions emphasize accessible public services while others focus on fiscal responsibility, a good synthesis might be "We support expanding public services while maintaining fiscal responsibility" rather than "There is consensus that services and budgets both matter."

Question: {question}

Individual Opinions:
{participant_statements}

You may include reasoning or notes before the final statement if helpful. Provide your response in this format:

---REASONING---
[Optional: Your analysis and reasoning process]

---STATEMENT---
[The actual consensus statement that will be used]"""

DEFAULT_RANKING_PREDICTION_TEMPLATE = """Predict how a person would rank these consensus statements based on their individual opinion. Consider how well each statement aligns with their stated values and priorities.

Process:
1. Identify the key values, priorities, and concerns in their opinion
2. For each statement, assess alignment with those values
3. Consider both what they explicitly support and what might concern them
4. Rank from most to least aligned with their perspective

Example: Someone emphasizing practical action would likely prefer statements with concrete steps over abstract principles, while someone focused on long-term values might rank differently.

Question: {question}

Participant's Opinion: {participant_statement}

Statements to Rank:
{candidate_statements}

Predict their ranking from most preferred (1) to least preferred ({num_candidates}).

You may include reasoning before the final ranking if helpful. Provide your response in this format:

---REASONING---
[Optional: Your analysis of how the participant would view each statement]

---RANKING---
{{
  "ranking": [1, 2, 3, ...]
}}

The ranking array must contain integers 1 through {num_candidates}, ordered from most to least preferred."""


# ============================================================================
# Template Registry
# ============================================================================

def get_default_templates() -> Dict[str, str]:
    """
    Get the default prompt templates.

    Returns:
        Dictionary mapping template names to template strings.
        Templates may contain placeholders like {question}, {participant_statements}, etc.

    Available templates:
        - "candidate_generation": For generating consensus candidate statements
          Placeholders: {question}, {participant_statements}

        - "ranking_prediction": For predicting how participants rank candidates
          Placeholders: {question}, {participant_statement}, {num_candidates},
                       {candidate_statements}

    Example:
        >>> templates = get_default_templates()
        >>> template = templates["candidate_generation"]
        >>> prompt = template.format(
        ...     question="Should voting be compulsory?",
        ...     participant_statements="- Statement 1\\n- Statement 2"
        ... )
    """
    return {
        "candidate_generation": DEFAULT_CANDIDATE_GENERATION_TEMPLATE,
        "ranking_prediction": DEFAULT_RANKING_PREDICTION_TEMPLATE
    }


# ============================================================================
# Response Extraction Utilities
# ============================================================================

def extract_statement_from_response(response: str) -> str:
    """
    Extract the consensus statement from a structured response.

    Looks for content after ---STATEMENT--- marker. If not found,
    falls back to using the entire response (for backwards compatibility
    or when models ignore the structure).

    Args:
        response: Raw LLM response

    Returns:
        Extracted statement string (stripped of whitespace)

    Example:
        >>> response = "---REASONING---\\nSome thoughts\\n---STATEMENT---\\nWe agree."
        >>> extract_statement_from_response(response)
        'We agree.'
        >>> extract_statement_from_response("Just a plain statement")
        'Just a plain statement'
    """
    import re

    # Try to find ---STATEMENT--- section
    match = re.search(r'---STATEMENT---\s*(.+)', response, re.DOTALL | re.IGNORECASE)

    if match:
        statement = match.group(1).strip()
        # Remove any trailing markers or artifacts
        statement = re.sub(r'\s*---\w+---.*$', '', statement, flags=re.DOTALL)
        return statement

    # Fallback: use entire response, but try to clean obvious reasoning sections
    cleaned = re.sub(r'^---REASONING---.*?(?=---STATEMENT---|$)', '', response, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()


def extract_ranking_from_response(response: str) -> tuple[dict | None, str]:
    """
    Extract the JSON ranking from a structured response.

    Looks for content after ---RANKING--- marker first, then falls back
    to searching the entire response for JSON.

    Args:
        response: Raw LLM response

    Returns:
        Tuple of (ranking_dict, reasoning_text)
        - ranking_dict: Parsed JSON object or None if parsing failed
        - reasoning_text: Any reasoning provided before the ranking

    Example:
        >>> response = "---REASONING---\\nThey prefer A\\n---RANKING---\\n{\\"ranking\\": [1,2]}"
        >>> extract_ranking_from_response(response)
        ({'ranking': [1, 2]}, 'They prefer A')
    """
    import re
    import json

    # Try to extract reasoning section
    reasoning_match = re.search(r'---REASONING---\s*(.+?)(?=---RANKING---|$)', response, re.DOTALL | re.IGNORECASE)
    reasoning = reasoning_match.group(1).strip() if reasoning_match else ""

    # Try to find ---RANKING--- section
    ranking_match = re.search(r'---RANKING---\s*(.+)', response, re.DOTALL | re.IGNORECASE)

    if ranking_match:
        json_text = ranking_match.group(1).strip()
    else:
        # Fallback: search entire response
        json_text = response

    # Extract JSON object from the text
    json_match = re.search(r'\{[^}]*"ranking"[^}]*\}', json_text, re.DOTALL)

    if json_match:
        try:
            ranking_dict = json.loads(json_match.group(0))
            return ranking_dict, reasoning
        except json.JSONDecodeError:
            pass

    return None, reasoning


# ============================================================================
# Template Utilities
# ============================================================================

def format_participant_statements(statements: list) -> str:
    """
    Format a list of participant statements for inclusion in a prompt.

    Each statement is formatted as a markdown bullet point.

    Args:
        statements: List of participant statement strings

    Returns:
        Formatted string with each statement as a bullet point

    Example:
        >>> statements = ["I support X", "I oppose Y"]
        >>> print(format_participant_statements(statements))
        - I support X

        - I oppose Y

    """
    return "\n\n".join(f"- {stmt}" for stmt in statements)


def format_candidate_statements(statements: list) -> str:
    """
    Format a list of candidate statements for ranking prediction.

    Each candidate is formatted in a numbered code block for clarity.

    Args:
        statements: List of candidate statement strings

    Returns:
        Formatted string with numbered statements in code blocks

    Example:
        >>> candidates = ["Option A", "Option B"]
        >>> print(format_candidate_statements(candidates))
        ```
        STATEMENT 1:
        Option A
        ```

        ```
        STATEMENT 2:
        Option B
        ```
    """
    formatted = []
    for i, statement in enumerate(statements, 1):
        formatted.append(f"```\nSTATEMENT {i}:\n{statement}\n```")
    return "\n\n".join(formatted)


def create_candidate_generation_prompt(
    question: str,
    participant_statements: list,
    template: str = None
) -> str:
    """
    Create a prompt for generating a consensus candidate statement.

    Args:
        question: The question participants are deliberating on
        participant_statements: List of individual participant statements
        template: Optional custom template (uses default if None)

    Returns:
        Formatted prompt string ready to send to LLM

    Example:
        >>> question = "Should voting be compulsory?"
        >>> statements = ["Yes, civic duty", "No, personal choice"]
        >>> prompt = create_candidate_generation_prompt(question, statements)
        >>> "Should voting be compulsory?" in prompt
        True
    """
    if template is None:
        template = DEFAULT_CANDIDATE_GENERATION_TEMPLATE

    formatted_statements = format_participant_statements(participant_statements)

    return template.format(
        question=question,
        participant_statements=formatted_statements
    )


def create_ranking_prediction_prompt(
    question: str,
    participant_statement: str,
    candidate_statements: list,
    participant_num: int,
    template: str = None
) -> str:
    """
    Create a prompt for predicting how a participant would rank candidates.

    Args:
        question: The question being deliberated
        participant_statement: The participant's original statement
        candidate_statements: List of candidate consensus statements to rank
        participant_num: The participant's number (for logging/tracking)
        template: Optional custom template (uses default if None)

    Returns:
        Formatted prompt string ready to send to LLM

    Example:
        >>> question = "Should voting be compulsory?"
        >>> participant = "I believe in personal freedom"
        >>> candidates = ["Make voting mandatory", "Keep it optional"]
        >>> prompt = create_ranking_prediction_prompt(
        ...     question, participant, candidates, 1
        ... )
        >>> "personal freedom" in prompt
        True
    """
    if template is None:
        template = DEFAULT_RANKING_PREDICTION_TEMPLATE

    formatted_candidates = format_candidate_statements(candidate_statements)

    return template.format(
        question=question,
        participant_num=participant_num,
        participant_statement=participant_statement,
        num_candidates=len(candidate_statements),
        candidate_statements=formatted_candidates
    )


# ============================================================================
# Template Validation
# ============================================================================

def validate_candidate_template(template: str) -> tuple[bool, str]:
    """
    Validate a candidate generation template.

    Checks that the template contains the required placeholders.

    Args:
        template: Template string to validate

    Returns:
        Tuple of (is_valid, error_message)
        If valid: (True, "")
        If invalid: (False, "Missing placeholder: {name}")

    Example:
        >>> valid_template = "Question: {question}\\n{participant_statements}"
        >>> validate_candidate_template(valid_template)
        (True, '')
        >>> invalid_template = "Question: {question}"
        >>> validate_candidate_template(invalid_template)
        (False, 'Missing placeholder: {participant_statements}')
    """
    required_placeholders = ["{question}", "{participant_statements}"]

    for placeholder in required_placeholders:
        if placeholder not in template:
            return False, f"Missing placeholder: {placeholder}"

    return True, ""


def validate_ranking_template(template: str) -> tuple[bool, str]:
    """
    Validate a ranking prediction template.

    Checks that the template contains the required placeholders.

    Args:
        template: Template string to validate

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> template = "{question}\\n{participant_statement}\\n{num_candidates}\\n{candidate_statements}"
        >>> validate_ranking_template(template)
        (True, '')
    """
    required_placeholders = [
        "{question}",
        "{participant_statement}",
        "{num_candidates}",
        "{candidate_statements}"
    ]

    for placeholder in required_placeholders:
        if placeholder not in template:
            return False, f"Missing placeholder: {placeholder}"

    return True, ""
