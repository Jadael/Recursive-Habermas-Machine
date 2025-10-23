"""Core modules for Habermas Machine and Chorus."""

from .prompts import (
    generate_opinion_only_cot_prompt,
    generate_opinion_critique_cot_prompt,
    generate_opinion_only_ranking_prompt,
    generate_opinion_critique_ranking_prompt,
    generate_simple_consensus_prompt,
    generate_simple_ranking_prompt,
    generate_chorus_feedback_prompt,
    generate_chorus_summary_prompt,
    extract_cot_response,
    extract_arrow_ranking,
    validate_arrow_ranking,
)

from .voting import (
    schulze_method,
    format_ranking_results,
    format_pairwise_matrix,
    format_strongest_paths,
    validate_rankings,
)

__all__ = [
    # Prompts
    'generate_opinion_only_cot_prompt',
    'generate_opinion_critique_cot_prompt',
    'generate_opinion_only_ranking_prompt',
    'generate_opinion_critique_ranking_prompt',
    'generate_simple_consensus_prompt',
    'generate_simple_ranking_prompt',
    'generate_chorus_feedback_prompt',
    'generate_chorus_summary_prompt',
    'extract_cot_response',
    'extract_arrow_ranking',
    'validate_arrow_ranking',
    # Voting
    'schulze_method',
    'format_ranking_results',
    'format_pairwise_matrix',
    'format_strongest_paths',
    'validate_rankings',
]
