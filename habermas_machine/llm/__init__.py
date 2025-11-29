"""
LLM integration for the Habermas Machine.

This package contains:
    - client: Ollama API client for text generation
    - response_parser: Utilities for parsing and validating LLM outputs
"""

from habermas_machine.llm.client import OllamaClient

from habermas_machine.llm.response_parser import (
    RankingParser,
    clean_deepseek_response,
    extract_json_from_text,
    validate_ranking,
    parse_ranking_response,
    create_random_ranking,
    create_ranking_system_prompt
)

__all__ = [
    # Client
    'OllamaClient',

    # Parser
    'RankingParser',
    'clean_deepseek_response',
    'extract_json_from_text',
    'validate_ranking',
    'parse_ranking_response',
    'create_random_ranking',
    'create_ranking_system_prompt',
]
