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

from .model_config import (
    ModelType,
    TaskType,
    ModelConfig,
    WorkflowConfig,
    get_prompted_config,
    get_finetuned_config,
    get_hybrid_config,
    optimize_workflow_order,
    PROMPTED_DEEPSEEK,
    PROMPTED_LLAMA,
    PROMPTED_QWEN,
    FINETUNED_COMMA,
    HYBRID_EXAMPLE,
)

from .model_manager import (
    ModelManager,
    create_manager_from_preset,
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
    # Model Configuration
    'ModelType',
    'TaskType',
    'ModelConfig',
    'WorkflowConfig',
    'get_prompted_config',
    'get_finetuned_config',
    'get_hybrid_config',
    'optimize_workflow_order',
    'PROMPTED_DEEPSEEK',
    'PROMPTED_LLAMA',
    'PROMPTED_QWEN',
    'FINETUNED_COMMA',
    'HYBRID_EXAMPLE',
    # Model Manager
    'ModelManager',
    'create_manager_from_preset',
]
