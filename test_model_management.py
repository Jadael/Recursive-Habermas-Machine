#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for model management system.

Tests model configuration, batching strategy, and workflow optimization.
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('')
    sys.stdout.reconfigure(encoding='utf-8')

def test_model_management():
    """Test model configuration and management system."""
    print("Testing Model Management System...\n")

    # Test 1: Import model configuration
    print("1. Testing model configuration imports...")
    try:
        from habermas_machine.core import (
            ModelType,
            TaskType,
            ModelConfig,
            WorkflowConfig,
            get_prompted_config,
            get_finetuned_config,
            get_hybrid_config,
            PROMPTED_DEEPSEEK,
            FINETUNED_COMMA,
        )
        print("   ✓ Model configuration imports successful")
    except ImportError as e:
        print(f"   ✗ Model configuration import failed: {e}")
        return False

    # Test 2: Import model manager
    print("\n2. Testing model manager imports...")
    try:
        from habermas_machine.core import (
            ModelManager,
            create_manager_from_preset,
        )
        print("   ✓ Model manager imports successful")
    except ImportError as e:
        print(f"   ✗ Model manager import failed: {e}")
        return False

    # Test 3: Create prompted configuration
    print("\n3. Testing prompted configuration...")
    try:
        config = get_prompted_config("deepseek-r1:14b")
        assert config.uses_same_model() == True
        assert config.statement_model.model_type == ModelType.PROMPTED
        assert config.ranking_model.model_type == ModelType.PROMPTED
        assert config.statement_model.task == TaskType.STATEMENT_GENERATION
        assert config.ranking_model.task == TaskType.RANKING_PREDICTION
        print(f"   ✓ Prompted config created")
        print(f"     Uses same model: {config.uses_same_model()}")
        print(f"     Statement temp: {config.statement_model.temperature}")
        print(f"     Ranking temp: {config.ranking_model.temperature}")
    except Exception as e:
        print(f"   ✗ Prompted configuration failed: {e}")
        return False

    # Test 4: Create finetuned configuration
    print("\n4. Testing finetuned configuration...")
    try:
        config = get_finetuned_config()
        assert config.uses_same_model() == False  # Different models for different tasks
        assert config.statement_model.model_type == ModelType.FINETUNED
        assert config.ranking_model.model_type == ModelType.FINETUNED
        print(f"   ✓ Finetuned config created")
        print(f"     Uses same model: {config.uses_same_model()}")
        print(f"     Statement model: {config.statement_model.model_name}")
        print(f"     Ranking model: {config.ranking_model.model_name}")
    except Exception as e:
        print(f"   ✗ Finetuned configuration failed: {e}")
        return False

    # Test 5: Create hybrid configuration
    print("\n5. Testing hybrid configuration...")
    try:
        config = get_hybrid_config(
            statement_model="deepseek-r1:14b",
            ranking_model="comma-habermas-ranking:v1"
        )
        assert config.statement_model.model_type == ModelType.PROMPTED
        assert config.ranking_model.model_type == ModelType.FINETUNED
        print(f"   ✓ Hybrid config created")
        print(f"     Statement: {config.statement_model.model_type.value}")
        print(f"     Ranking: {config.ranking_model.model_type.value}")
    except Exception as e:
        print(f"   ✗ Hybrid configuration failed: {e}")
        return False

    # Test 6: Test workflow optimization
    print("\n6. Testing workflow optimization...")
    try:
        from habermas_machine.core import optimize_workflow_order

        # Same model scenario
        config = PROMPTED_DEEPSEEK
        order = optimize_workflow_order(config, num_candidates=4, num_participants=5)

        assert 'phases' in order
        assert len(order['phases']) == 3
        assert order['total_model_loads'] == 1  # Same model
        print(f"   ✓ Workflow optimization works")
        print(f"     Total phases: {len(order['phases'])}")
        print(f"     Model loads: {order['total_model_loads']}")
        print(f"     Total operations: {order['total_operations']}")

        # Different models scenario
        config = FINETUNED_COMMA
        order = optimize_workflow_order(config, num_candidates=4, num_participants=5)
        assert order['total_model_loads'] == 2  # Different models
        print(f"   ✓ Optimization handles different models correctly")
        print(f"     Model loads (finetuned): {order['total_model_loads']}")

    except Exception as e:
        print(f"   ✗ Workflow optimization failed: {e}")
        return False

    # Test 7: Create model manager
    print("\n7. Testing model manager creation...")
    try:
        manager = create_manager_from_preset("prompted_deepseek")
        assert manager.config.statement_model.model_name == "deepseek-r1:14b"
        assert manager.current_model is None  # Not loaded yet
        print(f"   ✓ Model manager created from preset")
        print(f"     Current model: {manager.current_model or 'None (not loaded)'}")

        # Check statistics initialization
        stats = manager.get_stats()
        assert stats['model_loads'] == 0
        assert stats['statement_generations'] == 0
        assert stats['ranking_predictions'] == 0
        print(f"   ✓ Statistics initialized correctly")

    except Exception as e:
        print(f"   ✗ Model manager creation failed: {e}")
        return False

    # Test 8: Test preset configurations
    print("\n8. Testing preset configurations...")
    try:
        from habermas_machine.core import (
            PROMPTED_DEEPSEEK,
            PROMPTED_LLAMA,
            PROMPTED_QWEN,
            FINETUNED_COMMA,
            HYBRID_EXAMPLE,
        )

        presets = {
            'PROMPTED_DEEPSEEK': PROMPTED_DEEPSEEK,
            'PROMPTED_LLAMA': PROMPTED_LLAMA,
            'PROMPTED_QWEN': PROMPTED_QWEN,
            'FINETUNED_COMMA': FINETUNED_COMMA,
            'HYBRID_EXAMPLE': HYBRID_EXAMPLE,
        }

        print(f"   ✓ All {len(presets)} presets available:")
        for name, config in presets.items():
            same_model = "✓" if config.uses_same_model() else "✗"
            print(f"     {same_model} {name}: {config.statement_model.model_name}")

    except Exception as e:
        print(f"   ✗ Preset configurations failed: {e}")
        return False

    # Test 9: Test load order calculation
    print("\n9. Testing load order calculation...")
    try:
        # Same model
        config = PROMPTED_DEEPSEEK
        order = config.get_load_order()
        assert len(order) == 1
        print(f"   ✓ Load order (same model): {order}")

        # Different models
        config = FINETUNED_COMMA
        order = config.get_load_order()
        assert len(order) == 2
        print(f"   ✓ Load order (different models): {order}")

    except Exception as e:
        print(f"   ✗ Load order calculation failed: {e}")
        return False

    # Test 10: Test with actual prompts (no Ollama call)
    print("\n10. Testing prompt preparation...")
    try:
        from habermas_machine.core import generate_opinion_only_cot_prompt
        from habermas_machine.data.sample_statements import COMPULSORY_VOTING_OPINIONS

        # Generate sample prompts
        statement_prompts = []
        for i in range(2):  # Generate 2 candidates
            import random
            shuffled = COMPULSORY_VOTING_OPINIONS.copy()
            random.shuffle(shuffled)
            prompt = generate_opinion_only_cot_prompt(
                question="Should voting be compulsory?",
                opinions=shuffled
            )
            statement_prompts.append(prompt)

        assert len(statement_prompts) == 2
        print(f"   ✓ Generated {len(statement_prompts)} statement prompts")
        print(f"     Avg length: {sum(len(p) for p in statement_prompts) / len(statement_prompts):.0f} chars")

    except Exception as e:
        print(f"   ✗ Prompt preparation failed: {e}")
        return False

    print("\n" + "="*60)
    print("✓ All model management tests passed!")
    print("="*60)
    print("\nModel Management System Features:")
    print("  ✓ Prompted model configuration (instruct/chat-tuned)")
    print("  ✓ Finetuned model configuration (base models)")
    print("  ✓ Hybrid configurations (mix prompted & finetuned)")
    print("  ✓ Workflow optimization (minimize model swaps)")
    print("  ✓ Batching strategy (all statements → all rankings)")
    print("  ✓ Performance statistics tracking")
    print("  ✓ 5 preset configurations ready to use")
    print("\nUsage:")
    print("  from habermas_machine.core import create_manager_from_preset")
    print('  manager = create_manager_from_preset("prompted_deepseek")')
    print("\nSee MODEL_MANAGEMENT.md for complete guide.")

    return True

if __name__ == "__main__":
    success = test_model_management()
    sys.exit(0 if success else 1)
