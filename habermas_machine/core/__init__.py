"""
Core consensus and voting algorithms for the Habermas Machine.

This package contains:
    - voting: Schulze method and election utilities
    - templates: Prompt templates and formatting
"""

from habermas_machine.core.voting import (
    schulze_method,
    calculate_victories,
    rank_candidates_by_victories,
    format_pairwise_matrix,
    format_strongest_paths_matrix
)

from habermas_machine.core.templates import (
    get_default_templates,
    create_candidate_generation_prompt,
    create_ranking_prediction_prompt,
    format_participant_statements,
    format_candidate_statements,
    validate_candidate_template,
    validate_ranking_template,
    DEFAULT_CANDIDATE_GENERATION_TEMPLATE,
    DEFAULT_RANKING_PREDICTION_TEMPLATE
)

__all__ = [
    # Voting
    'schulze_method',
    'calculate_victories',
    'rank_candidates_by_victories',
    'format_pairwise_matrix',
    'format_strongest_paths_matrix',

    # Templates
    'get_default_templates',
    'create_candidate_generation_prompt',
    'create_ranking_prediction_prompt',
    'format_participant_statements',
    'format_candidate_statements',
    'validate_candidate_template',
    'validate_ranking_template',
    'DEFAULT_CANDIDATE_GENERATION_TEMPLATE',
    'DEFAULT_RANKING_PREDICTION_TEMPLATE',
]
