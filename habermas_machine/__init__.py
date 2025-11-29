"""
Habermas Machine - AI-Assisted Consensus Builder

A modular implementation of Google DeepMind's Habermas Machine research,
enabling AI-assisted consensus-building through simulated deliberation.

Copyright (C) 2025  Habermas Machine Project

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Main modules:
    core: Voting algorithms, consensus logic, and prompt templates
    llm: Ollama API client and response parsing
    utils: File I/O and utility functions

Example:
    >>> from habermas_machine.core import schulze_method
    >>> from habermas_machine.llm import OllamaClient
    >>> from habermas_machine.utils import save_friendly_output
"""

__version__ = "2.0.0"
__author__ = "Habermas Machine Project"
__license__ = "AGPL-3.0"

# Core exports for convenient importing
from habermas_machine.core.voting import (
    schulze_method,
    calculate_victories,
    rank_candidates_by_victories
)

from habermas_machine.core.templates import (
    get_default_templates,
    create_candidate_generation_prompt,
    create_ranking_prediction_prompt
)

from habermas_machine.llm.client import OllamaClient

from habermas_machine.llm.response_parser import (
    RankingParser,
    clean_deepseek_response,
    parse_ranking_response
)

from habermas_machine.utils.file_utils import (
    generate_session_id,
    save_friendly_output,
    save_detailed_output,
    load_participant_statements_from_file
)

__all__ = [
    # Voting
    'schulze_method',
    'calculate_victories',
    'rank_candidates_by_victories',

    # Templates
    'get_default_templates',
    'create_candidate_generation_prompt',
    'create_ranking_prediction_prompt',

    # LLM Client
    'OllamaClient',

    # Response Parsing
    'RankingParser',
    'clean_deepseek_response',
    'parse_ranking_response',

    # File Utils
    'generate_session_id',
    'save_friendly_output',
    'save_detailed_output',
    'load_participant_statements_from_file',
]
