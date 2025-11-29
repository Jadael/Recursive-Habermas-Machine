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

DEFAULT_CANDIDATE_GENERATION_TEMPLATE = """Given these participant statements, please combine these statements into a single group statement that synthesizes their viewpoints and includes all their individual points and concerns. This should represent a fair consensus or position that most participants could accept, and be representative of all details, concerns, suggestions, or questions from all participants, even if that make the combined statement longer. Your response will be used verbatim as the statement, so do not include any preamble or postscript.

---

# {question}

---

{participant_statements}

---

"""

DEFAULT_RANKING_PREDICTION_TEMPLATE = """Given this participant's statement, predict how this participant would rank these group statements from most preferred (1) to least preferred ({num_candidates}).



# {question}

## Participant's original statement: {participant_statement}

## Group Statements to Rank:

{candidate_statements}



Based on the participant's original statement, predict their ranking of these group statements from most preferred to least preferred as a JSON object:

{{
  "ranking": [1, 2, etc.]
}}

Important: Your response MUST contain ONLY a valid JSON object with a list of positive integer rankings under the key "ranking", NOT a list of statements, and must align with how this participant would rank them; e.g. how aligned they are with this participant's stance and priorities. Index starts at 1, not 0."""


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
