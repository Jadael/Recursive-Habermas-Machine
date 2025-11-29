# Habermas Machine - Modular Package

This package contains the refactored, modular components of the Habermas Machine.

## Quick Start

```python
from habermas_machine import (
    schulze_method,          # Voting algorithm
    OllamaClient,            # LLM client
    RankingParser,           # Response parser
    save_friendly_output     # File I/O
)

# Run an election
rankings = {0: [1, 0, 2], 1: [1, 2, 0], 2: [0, 1, 2]}
winner, pairwise, paths = schulze_method(rankings, 3)
print(f"Winner: Candidate {winner}")

# Generate text with LLM
client = OllamaClient()
response = client.generate(
    model="deepseek-r1:14b",
    prompt="Write a consensus statement..."
)
```

## Package Structure

```
habermas_machine/
├── core/           # Voting algorithms and prompt templates
├── llm/            # Ollama integration and response parsing
├── utils/          # File I/O and utilities
├── ui/             # UI components (future)
└── chorus/         # Chorus extension (future)
```

## Documentation

- **[EXAMPLES.md](EXAMPLES.md)** - Practical usage examples
- **[../REFACTORING.md](../REFACTORING.md)** - Complete refactoring guide
- **Module docstrings** - Comprehensive API documentation in each file

## Key Modules

### `core.voting`
Schulze method implementation and election utilities.
```python
from habermas_machine.core import schulze_method, calculate_victories
```

### `core.templates`
Prompt template management and formatting.
```python
from habermas_machine.core import get_default_templates, create_candidate_generation_prompt
```

### `llm.client`
Ollama API client with streaming support.
```python
from habermas_machine.llm import OllamaClient
client = OllamaClient()
```

### `llm.response_parser`
JSON parsing and validation with retry logic.
```python
from habermas_machine.llm import RankingParser
parser = RankingParser(num_candidates=3, max_retries=3)
```

### `utils.file_utils`
File I/O operations for saving and loading data.
```python
from habermas_machine.utils import save_friendly_output, load_participant_statements_from_file
```

## Design Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Comprehensive Documentation**: Every function has docstrings with examples
3. **Type Hints**: All functions use type hints for clarity
4. **Error Handling**: Graceful degradation with detailed logging
5. **Testability**: Modules can be tested independently

## Current Status

✅ **Implemented**:
- Core voting algorithms (Schulze method)
- Prompt template management
- LLM client and response parsing
- File I/O utilities
- Full documentation and examples

⏳ **Future Work**:
- UI component extraction
- Chorus functionality extraction
- Integration into main application
- Unit test suite
- Command-line interface

## License

AGPLv3 - Same as parent project

See [../LICENSE](../LICENSE) for details.
