"""
Model configuration system for Habermas Machine.

Supports two modes:
1. Prompted models: Use instruct/chat-tuned models with explicit prompts
2. Finetuned models: Use base models finetuned for specific tasks

Based on DeepMind's architecture with separate statement and reward models.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ModelType(Enum):
    """Type of model to use for each task."""
    PROMPTED = "prompted"      # Instruct/chat-tuned with prompts
    FINETUNED = "finetuned"    # Base model finetuned for task


class TaskType(Enum):
    """Different tasks in the Habermas Machine workflow."""
    STATEMENT_GENERATION = "statement_generation"  # Generate consensus candidates
    RANKING_PREDICTION = "ranking_prediction"      # Predict participant rankings


@dataclass
class ModelConfig:
    """
    Configuration for a specific model.

    Attributes:
        model_name: Ollama model identifier
        model_type: Whether prompted or finetuned
        task: What task this model performs
        temperature: Default sampling temperature
        description: Human-readable description
    """
    model_name: str
    model_type: ModelType
    task: TaskType
    temperature: float = 0.7
    description: str = ""

    def __repr__(self):
        return f"ModelConfig({self.model_name}, {self.task.value}, {self.model_type.value})"


@dataclass
class WorkflowConfig:
    """
    Complete workflow configuration.

    Defines which models to use for each task and how to batch operations
    to minimize model loading/unloading.
    """
    statement_model: ModelConfig
    ranking_model: ModelConfig
    batch_generations: bool = True    # Generate all candidates before ranking
    batch_rankings: bool = True       # Get all rankings before next phase

    def uses_same_model(self) -> bool:
        """Check if same model used for both tasks (avoid reloading)."""
        return self.statement_model.model_name == self.ranking_model.model_name

    def get_load_order(self) -> list[str]:
        """
        Get optimal model loading order to minimize swaps.

        Returns:
            List of model names in order they should be loaded/used
        """
        if self.uses_same_model():
            # Only one model needed
            return [self.statement_model.model_name]
        else:
            # Load statement model first, then ranking model
            return [
                self.statement_model.model_name,
                self.ranking_model.model_name
            ]

    def __repr__(self):
        return (f"WorkflowConfig(\n"
                f"  statement: {self.statement_model.model_name} ({self.statement_model.model_type.value})\n"
                f"  ranking: {self.ranking_model.model_name} ({self.ranking_model.model_type.value})\n"
                f"  same_model: {self.uses_same_model()}\n"
                f")")


# ============================================================================
# PRESET CONFIGURATIONS
# ============================================================================

def get_prompted_config(
    model_name: str = "deepseek-r1:14b",
    statement_temp: float = 0.6,
    ranking_temp: float = 0.2
) -> WorkflowConfig:
    """
    Configuration for prompted instruct/chat-tuned models.

    Uses the same model for both tasks with different temperatures.
    Best for: deepseek-r1, llama3.1, gemma, qwen, etc.

    Args:
        model_name: Ollama model identifier
        statement_temp: Temperature for consensus generation (higher = more creative)
        ranking_temp: Temperature for ranking prediction (lower = more deterministic)

    Returns:
        WorkflowConfig with prompted models

    Example:
        >>> config = get_prompted_config("deepseek-r1:14b")
        >>> print(config.uses_same_model())  # True
    """
    statement_model = ModelConfig(
        model_name=model_name,
        model_type=ModelType.PROMPTED,
        task=TaskType.STATEMENT_GENERATION,
        temperature=statement_temp,
        description=f"Prompted {model_name} for consensus generation"
    )

    ranking_model = ModelConfig(
        model_name=model_name,
        model_type=ModelType.PROMPTED,
        task=TaskType.RANKING_PREDICTION,
        temperature=ranking_temp,
        description=f"Prompted {model_name} for ranking prediction"
    )

    return WorkflowConfig(
        statement_model=statement_model,
        ranking_model=ranking_model,
        batch_generations=True,
        batch_rankings=True
    )


def get_finetuned_config(
    statement_model: str = "comma-habermas-statement:v1",
    ranking_model: str = "comma-habermas-ranking:v1",
    statement_temp: float = 0.6,
    ranking_temp: float = 0.2
) -> WorkflowConfig:
    """
    Configuration for finetuned base models.

    Uses separate finetuned models for each task.
    Best for: Base models like Comma-v0.1 finetuned on Habermas Machine tasks.

    Args:
        statement_model: Finetuned model for consensus generation
        ranking_model: Finetuned model for ranking prediction
        statement_temp: Temperature for consensus generation
        ranking_temp: Temperature for ranking prediction

    Returns:
        WorkflowConfig with finetuned models

    Example:
        >>> config = get_finetuned_config()
        >>> print(config.uses_same_model())  # False (different tasks need different models)
    """
    statement = ModelConfig(
        model_name=statement_model,
        model_type=ModelType.FINETUNED,
        task=TaskType.STATEMENT_GENERATION,
        temperature=statement_temp,
        description=f"Finetuned {statement_model} for consensus generation"
    )

    ranking = ModelConfig(
        model_name=ranking_model,
        model_type=ModelType.FINETUNED,
        task=TaskType.RANKING_PREDICTION,
        temperature=ranking_temp,
        description=f"Finetuned {ranking_model} for ranking prediction"
    )

    return WorkflowConfig(
        statement_model=statement,
        ranking_model=ranking,
        batch_generations=True,  # Critical: generate ALL candidates with statement model
        batch_rankings=True      # Then get ALL rankings with ranking model
    )


def get_hybrid_config(
    statement_model: str = "deepseek-r1:14b",
    ranking_model: str = "comma-habermas-ranking:v1",
    statement_temp: float = 0.6,
    ranking_temp: float = 0.2
) -> WorkflowConfig:
    """
    Hybrid configuration mixing prompted and finetuned models.

    Useful for experimentation or when only one task is finetuned.

    Args:
        statement_model: Model for consensus generation (prompted or finetuned)
        ranking_model: Model for ranking prediction (prompted or finetuned)
        statement_temp: Temperature for consensus generation
        ranking_temp: Temperature for ranking prediction

    Returns:
        WorkflowConfig with mixed model types
    """
    # Detect if models are finetuned based on naming convention
    statement_is_finetuned = "habermas" in statement_model.lower()
    ranking_is_finetuned = "habermas" in ranking_model.lower()

    statement = ModelConfig(
        model_name=statement_model,
        model_type=ModelType.FINETUNED if statement_is_finetuned else ModelType.PROMPTED,
        task=TaskType.STATEMENT_GENERATION,
        temperature=statement_temp,
        description=f"{'Finetuned' if statement_is_finetuned else 'Prompted'} {statement_model}"
    )

    ranking = ModelConfig(
        model_name=ranking_model,
        model_type=ModelType.FINETUNED if ranking_is_finetuned else ModelType.PROMPTED,
        task=TaskType.RANKING_PREDICTION,
        temperature=ranking_temp,
        description=f"{'Finetuned' if ranking_is_finetuned else 'Prompted'} {ranking_model}"
    )

    return WorkflowConfig(
        statement_model=statement,
        ranking_model=ranking,
        batch_generations=True,
        batch_rankings=True
    )


# ============================================================================
# WORKFLOW OPTIMIZATION
# ============================================================================

class WorkflowPhase(Enum):
    """Phases in the consensus generation workflow."""
    STATEMENT_GENERATION = "statement_generation"
    RANKING_PREDICTION = "ranking_prediction"
    ELECTION = "election"


def optimize_workflow_order(config: WorkflowConfig, num_candidates: int, num_participants: int) -> dict:
    """
    Calculate optimal operation order to minimize model loading.

    Args:
        config: Workflow configuration
        num_candidates: Number of consensus candidates to generate
        num_participants: Number of participants ranking candidates

    Returns:
        Dictionary with workflow phases and operation counts

    Example:
        >>> config = get_finetuned_config()
        >>> order = optimize_workflow_order(config, num_candidates=4, num_participants=5)
        >>> print(order['phases'])
        [
            {'phase': 'statement_generation', 'model': '...', 'operations': 4},
            {'phase': 'ranking_prediction', 'model': '...', 'operations': 5},
            {'phase': 'election', 'model': None, 'operations': 1}
        ]
    """
    phases = []

    # Phase 1: Generate all consensus candidates with statement model
    phases.append({
        'phase': WorkflowPhase.STATEMENT_GENERATION,
        'model': config.statement_model.model_name,
        'operations': num_candidates,
        'estimated_time': f"{num_candidates * 30}s",  # ~30s per candidate
        'note': 'Keep statement model loaded for all candidate generations'
    })

    # Phase 2: Get all rankings with ranking model
    phases.append({
        'phase': WorkflowPhase.RANKING_PREDICTION,
        'model': config.ranking_model.model_name,
        'operations': num_participants,
        'estimated_time': f"{num_participants * 20}s",  # ~20s per ranking
        'note': 'Batch all rankings to avoid model swaps' if not config.uses_same_model() else 'Same model, no reload needed'
    })

    # Phase 3: Election (no model needed)
    phases.append({
        'phase': WorkflowPhase.ELECTION,
        'model': None,
        'operations': 1,
        'estimated_time': '<1s',
        'note': 'Schulze voting on collected rankings'
    })

    return {
        'phases': phases,
        'total_model_loads': 1 if config.uses_same_model() else 2,
        'total_operations': num_candidates + num_participants + 1,
        'estimated_total_time': f"{(num_candidates * 30) + (num_participants * 20)}s"
    }


# ============================================================================
# PRESET EXAMPLES
# ============================================================================

# Common configurations for easy import
PROMPTED_DEEPSEEK = get_prompted_config("deepseek-r1:14b")
PROMPTED_LLAMA = get_prompted_config("llama3.1")
PROMPTED_QWEN = get_prompted_config("qwen2.5:14b")

FINETUNED_COMMA = get_finetuned_config(
    statement_model="comma-habermas-statement:v1",
    ranking_model="comma-habermas-ranking:v1"
)

# Example hybrid: Prompted for generation, finetuned for ranking
HYBRID_EXAMPLE = get_hybrid_config(
    statement_model="deepseek-r1:14b",
    ranking_model="comma-habermas-ranking:v1"
)
