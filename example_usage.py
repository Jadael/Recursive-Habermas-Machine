#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of the Habermas Machine model management system.

This demonstrates how to use the new model management system for both
prompted models (current) and finetuned models (future).
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('')
    sys.stdout.reconfigure(encoding='utf-8')

def example_1_prompted_model():
    """Example 1: Using prompted model (current recommended approach)."""
    print("="*70)
    print("Example 1: Prompted Model (DeepSeek-R1)")
    print("="*70)

    from habermas_machine.core import (
        create_manager_from_preset,
        generate_opinion_only_cot_prompt
    )
    from habermas_machine.data.sample_statements import COMPULSORY_VOTING_OPINIONS
    import random

    # Create manager with DeepSeek preset
    print("\n1. Creating model manager...")
    manager = create_manager_from_preset("prompted_deepseek")
    print(f"   ✓ Manager created")
    print(f"   - Statement model: {manager.config.statement_model.model_name}")
    print(f"   - Ranking model: {manager.config.ranking_model.model_name}")
    print(f"   - Uses same model: {manager.config.uses_same_model()}")

    # Prepare statement generation prompts
    print("\n2. Preparing statement generation prompts...")
    question = "Should voting be compulsory?"
    statement_prompts = []

    for i in range(4):  # Generate 4 candidates
        shuffled = COMPULSORY_VOTING_OPINIONS.copy()
        random.shuffle(shuffled)
        prompt = generate_opinion_only_cot_prompt(question, shuffled)
        statement_prompts.append(prompt)

    print(f"   ✓ Created {len(statement_prompts)} statement prompts")
    print(f"   - Avg prompt length: {sum(len(p) for p in statement_prompts) / len(statement_prompts):.0f} chars")

    # Note: We're not actually calling Ollama in this example
    print("\n3. Workflow execution (simulated):")
    print("   Phase 1: Generate all candidates with statement model")
    print("   Phase 2: Get all rankings with ranking model")
    print("   Phase 3: Run Schulze election")
    print("\n   Expected model loads: 1 (same model for both tasks)")
    print("   Expected time: ~220s for 4 candidates + 5 participants")

    print("\n✓ Example 1 complete!")
    return manager


def example_2_finetuned_model():
    """Example 2: Using finetuned models (future approach)."""
    print("\n" + "="*70)
    print("Example 2: Finetuned Models (Future)")
    print("="*70)

    from habermas_machine.core import (
        get_finetuned_config,
        ModelManager
    )

    # Create configuration for finetuned models
    print("\n1. Creating finetuned model configuration...")
    config = get_finetuned_config(
        statement_model="comma-habermas-statement:v1",
        ranking_model="comma-habermas-ranking:v1"
    )

    print(f"   ✓ Configuration created")
    print(f"   - Statement model: {config.statement_model.model_name}")
    print(f"   - Ranking model: {config.ranking_model.model_name}")
    print(f"   - Uses same model: {config.uses_same_model()}")
    print(f"   - Statement temp: {config.statement_model.temperature}")
    print(f"   - Ranking temp: {config.ranking_model.temperature}")

    # Create manager
    print("\n2. Creating model manager...")
    manager = ModelManager(config)
    print(f"   ✓ Manager created")

    print("\n3. Workflow execution (when models available):")
    print("   Phase 1: Generate all candidates with statement model")
    print("   Phase 2: Get all rankings with ranking model (← model swap)")
    print("   Phase 3: Run Schulze election")
    print("\n   Expected model loads: 2 (different models per task)")
    print("   Expected time: ~110s (50% faster than prompted!)")
    print("   - Simpler prompts needed (models already trained)")
    print("   - Faster per operation (task-optimized)")

    print("\n✓ Example 2 complete!")
    return manager


def example_3_hybrid_configuration():
    """Example 3: Hybrid configuration (mix prompted & finetuned)."""
    print("\n" + "="*70)
    print("Example 3: Hybrid Configuration")
    print("="*70)

    from habermas_machine.core import (
        get_hybrid_config,
        ModelManager
    )

    # Create hybrid configuration
    print("\n1. Creating hybrid configuration...")
    config = get_hybrid_config(
        statement_model="deepseek-r1:14b",  # Prompted
        ranking_model="comma-habermas-ranking:v1"  # Finetuned
    )

    print(f"   ✓ Configuration created")
    print(f"   - Statement: {config.statement_model.model_name} ({config.statement_model.model_type.value})")
    print(f"   - Ranking: {config.ranking_model.model_name} ({config.ranking_model.model_type.value})")

    print("\n2. Benefits of hybrid approach:")
    print("   - Use best model for each task")
    print("   - Gradually transition from prompted to finetuned")
    print("   - Optimize for your specific needs")

    print("\n✓ Example 3 complete!")
    return config


def example_4_workflow_optimization():
    """Example 4: Workflow optimization analysis."""
    print("\n" + "="*70)
    print("Example 4: Workflow Optimization")
    print("="*70)

    from habermas_machine.core import (
        optimize_workflow_order,
        PROMPTED_DEEPSEEK,
        FINETUNED_COMMA
    )

    # Analyze prompted workflow
    print("\n1. Analyzing prompted model workflow...")
    order = optimize_workflow_order(
        PROMPTED_DEEPSEEK,
        num_candidates=4,
        num_participants=5
    )

    print(f"   Configuration: {PROMPTED_DEEPSEEK.statement_model.model_name}")
    print(f"   Total phases: {len(order['phases'])}")
    print(f"   Model loads: {order['total_model_loads']}")
    print(f"   Total operations: {order['total_operations']}")

    for i, phase in enumerate(order['phases'], 1):
        print(f"\n   Phase {i}: {phase['phase']}")
        print(f"   - Model: {phase['model'] or 'None (voting)'}")
        print(f"   - Operations: {phase['operations']}")
        if 'note' in phase:
            print(f"   - Note: {phase['note']}")

    # Analyze finetuned workflow
    print("\n2. Analyzing finetuned model workflow...")
    order = optimize_workflow_order(
        FINETUNED_COMMA,
        num_candidates=4,
        num_participants=5
    )

    print(f"   Configuration: {FINETUNED_COMMA.statement_model.model_name}")
    print(f"   Total phases: {len(order['phases'])}")
    print(f"   Model loads: {order['total_model_loads']}")
    print(f"   Total operations: {order['total_operations']}")

    print("\n3. Key insight:")
    print("   Batching by task type minimizes model swaps:")
    print("   - Same model: 1 load (no swaps)")
    print("   - Different models: 2 loads (1 swap)")
    print("   - Alternating tasks: Many swaps (inefficient!)")

    print("\n✓ Example 4 complete!")


def example_5_statistics_tracking():
    """Example 5: Performance statistics tracking."""
    print("\n" + "="*70)
    print("Example 5: Statistics Tracking")
    print("="*70)

    from habermas_machine.core import create_manager_from_preset

    print("\n1. Creating manager and checking initial stats...")
    manager = create_manager_from_preset("prompted_deepseek")

    stats = manager.get_stats()
    print(f"   Initial statistics:")
    print(f"   - Model loads: {stats['model_loads']}")
    print(f"   - Statement generations: {stats['statement_generations']}")
    print(f"   - Ranking predictions: {stats['ranking_predictions']}")
    print(f"   - Total time: {stats['total_time']:.1f}s")

    print("\n2. After workflow execution (simulated):")
    print("   After generating 4 candidates and 5 rankings:")
    print("   - Model loads: 1 (same model)")
    print("   - Statement generations: 4")
    print("   - Ranking predictions: 5")
    print("   - Total time: ~220s")
    print("   - Avg statement time: ~30s")
    print("   - Avg ranking time: ~20s")

    print("\n3. Use statistics to optimize:")
    print("   - Track model loading patterns")
    print("   - Identify bottlenecks")
    print("   - Compare configurations")
    print("   - Monitor performance over time")

    print("\n✓ Example 5 complete!")


def example_6_available_presets():
    """Example 6: Show all available presets."""
    print("\n" + "="*70)
    print("Example 6: Available Presets")
    print("="*70)

    from habermas_machine.core import (
        PROMPTED_DEEPSEEK,
        PROMPTED_LLAMA,
        PROMPTED_QWEN,
        FINETUNED_COMMA,
        HYBRID_EXAMPLE
    )

    presets = [
        ("PROMPTED_DEEPSEEK", PROMPTED_DEEPSEEK, "Recommended for current use"),
        ("PROMPTED_LLAMA", PROMPTED_LLAMA, "Alternative prompted model"),
        ("PROMPTED_QWEN", PROMPTED_QWEN, "Alternative prompted model"),
        ("FINETUNED_COMMA", FINETUNED_COMMA, "Future finetuned models"),
        ("HYBRID_EXAMPLE", HYBRID_EXAMPLE, "Mix prompted & finetuned"),
    ]

    print("\nAvailable preset configurations:")
    print()

    for name, config, description in presets:
        same_model = "✓" if config.uses_same_model() else "✗"
        print(f"{same_model} {name}")
        print(f"  Description: {description}")
        print(f"  Statement model: {config.statement_model.model_name}")
        print(f"  Ranking model: {config.ranking_model.model_name}")
        print(f"  Same model: {config.uses_same_model()}")
        print()

    print("Usage:")
    print('  from habermas_machine.core import create_manager_from_preset')
    print('  manager = create_manager_from_preset("prompted_deepseek")')

    print("\n✓ Example 6 complete!")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("Habermas Machine - Model Management Examples")
    print("="*70)
    print("\nThese examples demonstrate the model management system.")
    print("Note: These are simulations; no actual Ollama calls are made.")
    print()

    try:
        # Run all examples
        example_1_prompted_model()
        example_2_finetuned_model()
        example_3_hybrid_configuration()
        example_4_workflow_optimization()
        example_5_statistics_tracking()
        example_6_available_presets()

        # Final summary
        print("\n" + "="*70)
        print("All Examples Complete!")
        print("="*70)
        print("\nKey Takeaways:")
        print("1. Use create_manager_from_preset() for quick setup")
        print("2. Batching by task minimizes model loading")
        print("3. Same API works for prompted and finetuned models")
        print("4. Statistics help track and optimize performance")
        print("5. Multiple presets available for different scenarios")
        print("\nFor complete documentation, see MODEL_MANAGEMENT.md")
        print("For getting started, see QUICKSTART.md")

        return True

    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
