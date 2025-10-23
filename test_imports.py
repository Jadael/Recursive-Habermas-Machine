#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify all new modules can be imported correctly.
Run this to check that the reorganization is working.
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('')  # Enable ANSI escape sequences
    sys.stdout.reconfigure(encoding='utf-8')

def test_imports():
    """Test importing all new modules."""
    print("Testing Habermas Machine 2.0 imports...\n")

    # Test core modules
    print("1. Testing core modules...")
    try:
        from habermas_machine.core import (
            generate_opinion_only_cot_prompt,
            generate_opinion_only_ranking_prompt,
            schulze_method,
            format_ranking_results,
        )
        print("   ✓ Core prompts and voting imported successfully")
    except ImportError as e:
        print(f"   ✗ Core import failed: {e}")
        return False

    # Test utils
    print("\n2. Testing utils modules...")
    try:
        from habermas_machine.utils import (
            OllamaClient,
            OllamaEmbeddingHelper,
            HabermasLLMSummarizer,
        )
        print("   ✓ Utils (client, embeddings, summarization) imported successfully")
    except ImportError as e:
        print(f"   ✗ Utils import failed: {e}")
        return False

    # Test data
    print("\n3. Testing data module...")
    try:
        from habermas_machine.data.sample_statements import (
            SAMPLE_VALUE_STATEMENTS,
            COMPULSORY_VOTING_OPINIONS,
            get_filtered_statements,
        )
        print("   ✓ Data module imported successfully")
        print(f"   ✓ Found {len(SAMPLE_VALUE_STATEMENTS)} sample value statements")
        print(f"   ✓ Found {len(COMPULSORY_VOTING_OPINIONS)} voting opinions")
    except ImportError as e:
        print(f"   ✗ Data import failed: {e}")
        return False

    # Test functionality
    print("\n4. Testing basic functionality...")

    # Test prompt generation
    try:
        prompt = generate_opinion_only_cot_prompt(
            question="Test question?",
            opinions=["Opinion 1", "Opinion 2"]
        )
        assert '<answer>' in prompt
        assert '<sep>' in prompt
        print("   ✓ Prompt generation works")
    except Exception as e:
        print(f"   ✗ Prompt generation failed: {e}")
        return False

    # Test voting
    try:
        rankings = {0: [1, 0, 2], 1: [0, 1, 2], 2: [1, 2, 0]}
        winner, pairwise, paths = schulze_method(rankings, 3)
        assert winner in [0, 1, 2]
        print(f"   ✓ Schulze voting works (winner: {winner})")
    except Exception as e:
        print(f"   ✗ Schulze voting failed: {e}")
        return False

    # Test data filtering
    try:
        remote_workers = get_filtered_statements(location="Remote")
        assert len(remote_workers) > 0
        print(f"   ✓ Data filtering works ({len(remote_workers)} remote workers)")
    except Exception as e:
        print(f"   ✗ Data filtering failed: {e}")
        return False

    # Test Ollama client
    print("\n5. Testing Ollama client...")
    try:
        client = OllamaClient()
        models = client.list_models()
        if client.available:
            print(f"   ✓ Ollama connected ({len(models)} models available)")
            if models:
                print(f"   ✓ Available models: {', '.join(models[:3])}{'...' if len(models) > 3 else ''}")
        else:
            print("   ⚠ Ollama not running (this is OK for import testing)")
    except Exception as e:
        print(f"   ✗ Ollama client failed: {e}")
        return False

    print("\n" + "="*60)
    print("✓ All imports and basic tests passed!")
    print("="*60)
    print("\nYou can now run the application with:")
    print("  python main.py")
    print("\nOr use the original GUI with:")
    print("  python habermas_machine.py")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
