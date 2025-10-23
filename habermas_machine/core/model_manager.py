"""
Model manager for optimized model loading and task batching.

Handles both prompted and finetuned models, minimizing model swaps
by batching operations by task type.
"""

from typing import List, Callable, Optional, Any
from dataclasses import dataclass
import time

from .model_config import WorkflowConfig, ModelType, TaskType
from ..utils.ollama_client import OllamaClient


@dataclass
class TaskBatch:
    """A batch of operations for a specific task."""
    task_type: TaskType
    model_name: str
    operations: List[dict]  # List of {prompt, params} dicts

    def __len__(self):
        return len(self.operations)


class ModelManager:
    """
    Manages model loading and task batching for optimal performance.

    Key principles:
    1. Batch all operations of the same type together
    2. Minimize model loading/unloading
    3. Support both prompted and finetuned workflows
    """

    def __init__(self, config: WorkflowConfig, ollama_base_url: str = "http://localhost:11434"):
        """
        Initialize model manager.

        Args:
            config: Workflow configuration defining models for each task
            ollama_base_url: Ollama API URL
        """
        self.config = config
        self.client = OllamaClient(base_url=ollama_base_url)

        # Track which model is currently loaded (Ollama caches)
        self.current_model = None

        # Statistics
        self.stats = {
            'model_loads': 0,
            'statement_generations': 0,
            'ranking_predictions': 0,
            'total_time': 0.0
        }

    def _ensure_model_loaded(self, model_name: str):
        """
        Ensure the specified model is ready.

        Ollama handles caching, but we track for statistics.
        """
        if self.current_model != model_name:
            self.current_model = model_name
            self.stats['model_loads'] += 1

    def generate_statements_batch(
        self,
        prompts: List[str],
        callback: Optional[Callable[[int, str], None]] = None
    ) -> List[str]:
        """
        Generate multiple consensus candidate statements.

        Batches all generations together using statement model.

        Args:
            prompts: List of prompts for generating candidates
            callback: Optional callback(index, text) for progress updates

        Returns:
            List of generated statements

        Example:
            >>> manager = ModelManager(PROMPTED_DEEPSEEK)
            >>> prompts = [prompt1, prompt2, prompt3, prompt4]
            >>> candidates = manager.generate_statements_batch(prompts)
        """
        start_time = time.time()

        # Ensure statement model is loaded
        model_config = self.config.statement_model
        self._ensure_model_loaded(model_config.model_name)

        statements = []

        for i, prompt in enumerate(prompts):
            # Generate with appropriate parameters
            response = self.client.generate(
                prompt=prompt,
                model=model_config.model_name,
                temperature=model_config.temperature,
                stream=False
            )

            # Clean response if needed (e.g., remove <think> tags)
            cleaned = self.client.clean_response(response, model=model_config.model_name)
            statements.append(cleaned)

            # Update statistics
            self.stats['statement_generations'] += 1

            # Callback for progress
            if callback:
                callback(i, cleaned)

        elapsed = time.time() - start_time
        self.stats['total_time'] += elapsed

        return statements

    def predict_rankings_batch(
        self,
        prompts: List[str],
        callback: Optional[Callable[[int, Any], None]] = None
    ) -> List[Any]:
        """
        Predict rankings for multiple participants.

        Batches all ranking predictions together using ranking model.

        Args:
            prompts: List of prompts for predicting rankings
            callback: Optional callback(index, ranking) for progress updates

        Returns:
            List of rankings (format depends on model type)

        Example:
            >>> manager = ModelManager(FINETUNED_COMMA)
            >>> prompts = [prompt1, prompt2, prompt3]  # One per participant
            >>> rankings = manager.predict_rankings_batch(prompts)
        """
        start_time = time.time()

        # Ensure ranking model is loaded
        model_config = self.config.ranking_model
        self._ensure_model_loaded(model_config.model_name)

        rankings = []

        for i, prompt in enumerate(prompts):
            # For prompted models, we need JSON parsing with retry
            # For finetuned models, output is direct

            if model_config.model_type == ModelType.PROMPTED:
                # Use JSON generation with retry
                ranking = self.client.generate_json(
                    prompt=prompt,
                    model=model_config.model_name,
                    temperature=model_config.temperature,
                    max_retries=3
                )
            else:
                # Finetuned model: simpler output (arrow notation or direct)
                response = self.client.generate(
                    prompt=prompt,
                    model=model_config.model_name,
                    temperature=model_config.temperature,
                    stream=False
                )
                ranking = self._parse_finetuned_ranking(response)

            rankings.append(ranking)

            # Update statistics
            self.stats['ranking_predictions'] += 1

            # Callback for progress
            if callback:
                callback(i, ranking)

        elapsed = time.time() - start_time
        self.stats['total_time'] += elapsed

        return rankings

    def _parse_finetuned_ranking(self, response: str) -> Any:
        """
        Parse output from finetuned ranking model.

        Finetuned models should output arrow notation: A > B > C > D
        This is more reliable than JSON.

        Args:
            response: Raw model output

        Returns:
            Parsed ranking (could be arrow notation string or list of indices)
        """
        from .prompts import extract_arrow_ranking, validate_arrow_ranking

        # Try to extract arrow notation
        arrow_ranking = extract_arrow_ranking(response)

        if arrow_ranking and validate_arrow_ranking(arrow_ranking):
            return arrow_ranking

        # Fallback: return raw response for manual handling
        return response

    def execute_workflow(
        self,
        statement_prompts: List[str],
        ranking_prompts: List[str],
        statement_callback: Optional[Callable] = None,
        ranking_callback: Optional[Callable] = None
    ) -> tuple[List[str], List[Any]]:
        """
        Execute complete workflow with optimal model loading.

        Phase 1: Generate all candidate statements (batched)
        Phase 2: Predict all rankings (batched)

        This minimizes model swaps and is optimal for both same-model
        and different-model configurations.

        Args:
            statement_prompts: Prompts for generating consensus candidates
            ranking_prompts: Prompts for predicting participant rankings
            statement_callback: Progress callback for statements
            ranking_callback: Progress callback for rankings

        Returns:
            Tuple of (candidate_statements, participant_rankings)

        Example:
            >>> manager = ModelManager(config)
            >>> statements, rankings = manager.execute_workflow(
            ...     statement_prompts=[p1, p2, p3, p4],
            ...     ranking_prompts=[r1, r2, r3, r4, r5]
            ... )
        """
        # Phase 1: Generate all statements with statement model
        statements = self.generate_statements_batch(
            prompts=statement_prompts,
            callback=statement_callback
        )

        # Phase 2: Get all rankings with ranking model
        rankings = self.predict_rankings_batch(
            prompts=ranking_prompts,
            callback=ranking_callback
        )

        return statements, rankings

    def get_stats(self) -> dict:
        """
        Get performance statistics.

        Returns:
            Dictionary with model loads, operations, and timing
        """
        return {
            **self.stats,
            'uses_same_model': self.config.uses_same_model(),
            'statement_model': self.config.statement_model.model_name,
            'ranking_model': self.config.ranking_model.model_name,
            'avg_statement_time': (
                self.stats['total_time'] / self.stats['statement_generations']
                if self.stats['statement_generations'] > 0 else 0
            ),
            'avg_ranking_time': (
                self.stats['total_time'] / self.stats['ranking_predictions']
                if self.stats['ranking_predictions'] > 0 else 0
            )
        }

    def reset_stats(self):
        """Reset performance statistics."""
        self.stats = {
            'model_loads': 0,
            'statement_generations': 0,
            'ranking_predictions': 0,
            'total_time': 0.0
        }


def create_manager_from_preset(
    preset: str = "prompted_deepseek",
    ollama_url: str = "http://localhost:11434"
) -> ModelManager:
    """
    Create ModelManager from preset configuration.

    Args:
        preset: One of:
            - "prompted_deepseek": DeepSeek-R1 for both tasks
            - "prompted_llama": Llama 3.1 for both tasks
            - "finetuned_comma": Finetuned Comma models
            - "hybrid": Mixed prompted/finetuned
        ollama_url: Ollama API URL

    Returns:
        Configured ModelManager

    Example:
        >>> manager = create_manager_from_preset("prompted_deepseek")
        >>> # Ready to use
    """
    from .model_config import (
        PROMPTED_DEEPSEEK,
        PROMPTED_LLAMA,
        FINETUNED_COMMA,
        HYBRID_EXAMPLE
    )

    presets = {
        "prompted_deepseek": PROMPTED_DEEPSEEK,
        "prompted_llama": PROMPTED_LLAMA,
        "finetuned_comma": FINETUNED_COMMA,
        "hybrid": HYBRID_EXAMPLE
    }

    if preset not in presets:
        raise ValueError(f"Unknown preset: {preset}. Choose from: {list(presets.keys())}")

    config = presets[preset]
    return ModelManager(config, ollama_base_url=ollama_url)
