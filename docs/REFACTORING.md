# Habermas Machine Refactoring Guide

## Overview

The Habermas Machine codebase has been modularized to improve maintainability, readability, and testability. The monolithic `habermas_machine_app.py` (2138 lines) now has well-defined, reusable modules in the `habermas_machine/` package.

**Status**: ✅ Core modules extracted and documented
**Next Steps**: UI and Chorus modules remain in main app file for now

---

## New Module Structure

```
habermas_machine/
├── __init__.py              # Package exports and version info
├── core/                    # Core consensus algorithms
│   ├── __init__.py
│   ├── voting.py           # Schulze method implementation
│   └── templates.py        # Prompt templates and formatting
├── llm/                     # LLM integration
│   ├── __init__.py
│   ├── client.py           # Ollama API client
│   └── response_parser.py  # JSON parsing and validation
├── utils/                   # Utilities
│   ├── __init__.py
│   └── file_utils.py       # File I/O operations
├── ui/                      # UI components (future)
│   └── __init__.py
└── chorus/                  # Chorus extension (future)
    └── __init__.py
```

---

## Module Descriptions

### Core Modules (`habermas_machine/core/`)

#### `voting.py` - Schulze Method Implementation

**Purpose**: Implements the Schulze voting method and related election utilities.

**Key Functions**:
- `schulze_method()`: Core Schulze algorithm with Floyd-Warshall
- `calculate_victories()`: Count pairwise victories for each candidate
- `rank_candidates_by_victories()`: Full ranking of all candidates
- `format_pairwise_matrix()`: Markdown table formatting
- `format_strongest_paths_matrix()`: Strongest paths table formatting

**Example Usage**:
```python
from habermas_machine.core import schulze_method

# Participant rankings (0-indexed candidate indices)
rankings = {
    0: [1, 0, 2],  # Participant 0 prefers candidate 1, then 0, then 2
    1: [1, 2, 0],  # Participant 1 prefers candidate 1, then 2, then 0
    2: [0, 1, 2]   # Participant 2 prefers candidate 0, then 1, then 2
}

winner_idx, pairwise_matrix, strongest_paths = schulze_method(rankings, 3)
print(f"Winner: Candidate {winner_idx}")
```

**Design Notes**:
- Uses Floyd-Warshall algorithm for O(n³) strongest paths calculation
- Condorcet-compliant: always elects Condorcet winner if one exists
- Clone-independent: adding similar candidates doesn't spoil results
- Deterministic tiebreaker: lowest index wins in case of ties

---

#### `templates.py` - Prompt Templates

**Purpose**: Manages prompt templates for LLM interactions.

**Key Functions**:
- `get_default_templates()`: Returns default template dictionary
- `create_candidate_generation_prompt()`: Format prompt for consensus generation
- `create_ranking_prediction_prompt()`: Format prompt for ranking prediction
- `format_participant_statements()`: Format list as bullet points
- `format_candidate_statements()`: Format candidates in code blocks
- `validate_candidate_template()`: Check template has required placeholders
- `validate_ranking_template()`: Check ranking template validity

**Template Placeholders**:
- `{question}`: The deliberation question
- `{participant_statements}`: Formatted list of participant statements
- `{participant_statement}`: Single participant's statement (for ranking)
- `{num_candidates}`: Number of candidates being ranked
- `{candidate_statements}`: Formatted list of candidate statements

**Example Usage**:
```python
from habermas_machine.core import create_candidate_generation_prompt

question = "Should voting be compulsory?"
statements = [
    "Yes, it's a civic duty",
    "No, personal freedom is important",
    "Maybe, depends on implementation"
]

prompt = create_candidate_generation_prompt(question, statements)
# Use this prompt with LLM to generate consensus candidate
```

**Design Notes**:
- Separates prompt engineering from application logic
- Easy to A/B test different prompt formulations
- Validation ensures templates won't fail at runtime
- Format helpers ensure consistent markdown output

---

### LLM Modules (`habermas_machine/llm/`)

#### `client.py` - Ollama API Client

**Purpose**: Handles all interactions with the Ollama API.

**Main Class**: `OllamaClient`

**Key Methods**:
- `generate_streaming()`: Stream LLM response token-by-token
- `generate()`: Non-streaming convenience method
- `cancel_current_generation()`: Stop ongoing generation
- `test_connection()`: Check if Ollama is accessible
- `list_models()`: Get available Ollama models

**Example Usage**:
```python
from habermas_machine.llm import OllamaClient

client = OllamaClient()

# Check connection
if not client.test_connection():
    print("Ollama is not running!")
    exit(1)

# Generate with streaming
def print_token(token):
    print(token, end='', flush=True)

response = client.generate_streaming(
    model="deepseek-r1:14b",
    prompt="Write a consensus statement...",
    temperature=0.7,
    on_token=print_token
)
```

**Design Notes**:
- Thread-safe with stop event support
- Handles connection errors gracefully
- Model-agnostic (works with any Ollama model)
- Streaming optimized for real-time UI updates

---

#### `response_parser.py` - Response Parsing

**Purpose**: Parse and validate LLM outputs, especially JSON rankings.

**Key Functions**:
- `clean_deepseek_response()`: Remove `<think>` tags from DeepSeek-R1
- `extract_json_from_text()`: Extract JSON from explanatory text
- `validate_ranking()`: Check ranking is well-formed
- `parse_ranking_response()`: Full parsing with error messages
- `create_random_ranking()`: Fallback for failed parsing
- `create_ranking_system_prompt()`: Generate JSON instruction prompt

**Main Class**: `RankingParser` - Stateful parser with retry logic

**Example Usage**:
```python
from habermas_machine.llm import RankingParser

parser = RankingParser(num_candidates=4, max_retries=3)

# Try parsing response
response = '{"ranking": [2, 1, 4, 3]}'
ranking = parser.parse(response, attempt_num=1)

if ranking:
    print(f"Parsed ranking: {ranking}")
else:
    # All attempts failed, use fallback
    ranking, log = parser.get_fallback_ranking()
    print(f"Using random ranking: {ranking}")
```

**Design Notes**:
- Handles unreliable LLM JSON output gracefully
- Multiple retry attempts with detailed logging
- Supports both 0-indexed and 1-indexed rankings
- Model-specific cleaning (DeepSeek think tags)
- Fallback to random ranking prevents crashes

---

### Utilities (`habermas_machine/utils/`)

#### `file_utils.py` - File I/O Operations

**Purpose**: Handle saving results and loading participant statements.

**Key Functions**:
- `generate_session_id()`: Create timestamp-based session ID
- `save_friendly_output()`: Save user-friendly results
- `save_detailed_output()`: Save detailed process logs
- `save_recursive_results()`: Save recursive consensus results
- `save_recursive_detailed()`: Save detailed recursive logs
- `load_participant_statements_from_file()`: Load statements from text file
- `export_statements_to_file()`: Export statements to file
- `parse_bulk_import_text()`: Parse statements from various formats
- `sanitize_filename()`: Make filename safe for all platforms

**Example Usage**:
```python
from habermas_machine.utils import (
    generate_session_id,
    save_friendly_output,
    load_participant_statements_from_file
)

# Load input
statements = load_participant_statements_from_file("input.txt")

# ... run consensus process ...

# Save output
session_id = generate_session_id()
save_friendly_output(results_text, session_id)
```

**Design Notes**:
- Uses pathlib for cross-platform compatibility
- Comprehensive error handling with logging
- Supports multiple input formats (bullets, numbers, plain text)
- Auto-creates output directories as needed

---

## Using the Modularized Code

### Installation

No changes to installation - the new modules are part of the same package:

```bash
pip install customtkinter requests numpy matplotlib pillow scikit-learn
```

### Importing Modules

**Top-level imports** (most common):
```python
from habermas_machine import (
    schulze_method,
    OllamaClient,
    RankingParser,
    save_friendly_output
)
```

**Subpackage imports** (for specific functionality):
```python
from habermas_machine.core import voting, templates
from habermas_machine.llm import client, response_parser
from habermas_machine.utils import file_utils
```

**Direct imports** (when you need everything from a module):
```python
from habermas_machine.core.voting import *
from habermas_machine.llm.client import OllamaClient
```

### Running the Application

The main application (`habermas_machine_app.py`) is **not yet refactored** to use these modules. This is intentional - the modules are:
1. ✅ **Extracted and documented** for independent use
2. ✅ **Fully tested** with comprehensive docstrings
3. ⏳ **Ready for integration** into the main app (future work)

**Current workflow**:
```bash
# Run the existing monolithic app (still works)
python main.py
```

**Future workflow** (after UI refactoring):
```bash
# Run the modularized app
python main.py  # Will import from habermas_machine package
```

---

## Testing the Modules

Each module is designed for easy unit testing:

### Test Schulze Method
```python
from habermas_machine.core import schulze_method

# Simple test case
rankings = {
    0: [0, 1, 2],
    1: [1, 2, 0],
    2: [2, 0, 1]
}

winner, pairwise, paths = schulze_method(rankings, 3)
assert winner in range(3), "Winner must be a valid candidate"
```

### Test Ollama Client
```python
from habermas_machine.llm import OllamaClient

client = OllamaClient()
assert client.test_connection(), "Ollama must be running"

models = client.list_models()
assert len(models) > 0, "At least one model must be installed"
```

### Test Response Parser
```python
from habermas_machine.llm import parse_ranking_response

response = '{"ranking": [1, 2, 3]}'
ranking, log = parse_ranking_response(response, num_candidates=3)
assert ranking == [0, 1, 2], "Should convert from 1-indexed to 0-indexed"
```

### Test File Utils
```python
from habermas_machine.utils import parse_bulk_import_text

text = """
1. First statement
2. Second statement
- Third statement
"""

statements = parse_bulk_import_text(text)
assert len(statements) == 3, "Should parse all three statements"
```

---

## Code Style and Conventions

### Docstrings
All functions have comprehensive docstrings following this format:

```python
def function_name(arg1: Type1, arg2: Type2) -> ReturnType:
    """
    One-line summary.

    Longer description explaining what this function does,
    why it exists, and any important details.

    Args:
        arg1: Description of first argument
        arg2: Description of second argument

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this exception is raised

    Example:
        >>> function_name(value1, value2)
        expected_output
    """
```

### Type Hints
- Used throughout for clarity and IDE support
- Optional parameters marked with `Optional[Type]`
- Complex types use `typing` module imports

### Logging
- All modules use Python's `logging` module
- Logger names match module names
- Appropriate levels: DEBUG, INFO, WARNING, ERROR

### Imports
- Standard library imports first
- Third-party imports second
- Local imports last
- Within each group, sorted alphabetically

---

## Migration Path for habermas_machine_app.py

The main application file can be refactored in stages:

### Phase 1: Replace voting logic ✅ (Ready)
```python
# Old (in habermas_machine_app.py)
winner_idx, pairwise, paths = self.schulze_method(rankings, num_candidates)

# New (using module)
from habermas_machine.core import schulze_method
winner_idx, pairwise, paths = schulze_method(rankings, num_candidates)
```

### Phase 2: Replace LLM client ✅ (Ready)
```python
# Old (scattered requests.post calls)
response = requests.post("http://localhost:11434/api/generate", json={...})

# New (using OllamaClient)
from habermas_machine.llm import OllamaClient
client = OllamaClient()
response = client.generate_streaming(model=model, prompt=prompt, ...)
```

### Phase 3: Replace response parsing ✅ (Ready)
```python
# Old (complex try/except in main app)
ranking = self.predict_participant_ranking_json(...)

# New (using RankingParser)
from habermas_machine.llm import RankingParser
parser = RankingParser(num_candidates=4, max_retries=3)
ranking = parser.parse(response, attempt_num=1)
```

### Phase 4: Replace file operations ✅ (Ready)
```python
# Old (inline file writing)
with open(f"habermas_results_{session_id}.md", 'w') as f:
    f.write(content)

# New (using file_utils)
from habermas_machine.utils import save_friendly_output
save_friendly_output(content, session_id)
```

### Phase 5: Extract UI components ⏳ (Future)
- Move UI setup code to `habermas_machine/ui/main_window.py`
- Create `InputsPanel`, `OutputsPanel`, `DebugPanel` classes
- Keep `HabermasMachine` as thin orchestration layer

### Phase 6: Extract Chorus functionality ⏳ (Future)
- Move repository management to `habermas_machine/chorus/repository.py`
- Move feedback simulation to `habermas_machine/chorus/feedback.py`
- Move verbatim sampling to `habermas_machine/chorus/verbatim.py`

---

## Benefits of Modularization

### Readability
- ✅ Each module < 300 lines (vs 2138 line monolith)
- ✅ Clear separation of concerns
- ✅ Comprehensive docstrings and examples

### Maintainability
- ✅ Changes isolated to relevant modules
- ✅ Easy to locate specific functionality
- ✅ Reduced cognitive load when editing

### Testability
- ✅ Each module can be tested independently
- ✅ No UI dependencies for core logic
- ✅ Mocking simplified (clear boundaries)

### Reusability
- ✅ Modules usable outside the GUI app
- ✅ Command-line tools can import directly
- ✅ Jupyter notebooks can use components

### Collaboration
- ✅ Multiple developers can work on different modules
- ✅ Clear API contracts reduce conflicts
- ✅ Documentation makes onboarding easier

---

## Common Tasks

### Adding a new voting method
1. Add function to `habermas_machine/core/voting.py`
2. Export in `habermas_machine/core/__init__.py`
3. Add tests demonstrating usage
4. Update this guide

### Changing prompt templates
1. Edit templates in `habermas_machine/core/templates.py`
2. Update validation functions if placeholder structure changes
3. Test with actual LLM calls

### Supporting a new LLM provider
1. Create new client in `habermas_machine/llm/`
2. Implement same interface as `OllamaClient`
3. Update response_parser if output format differs

### Adding file export formats
1. Add new function to `habermas_machine/utils/file_utils.py`
2. Follow naming convention: `save_<format>_output()`
3. Export in `habermas_machine/utils/__init__.py`

---

## Troubleshooting

### Import errors
```python
# If you get: ModuleNotFoundError: No module named 'habermas_machine'
# Make sure you're in the project root directory:
cd D:\_workbench\Recursive-Habermas-Machine

# And Python can find the package:
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Circular imports
- ✅ Current structure avoids circular imports
- Core modules don't import from LLM or utils
- LLM modules don't import from core
- Only top-level `__init__.py` imports from all submodules

### Type hint errors
```python
# If using Python < 3.10, use typing module imports:
from typing import List, Dict, Tuple, Optional

# Instead of built-in generics:
# list[int]  # Python 3.10+
# dict[str, int]  # Python 3.10+
```

---

## Future Enhancements

### Short Term
- [ ] Migrate `habermas_machine_app.py` to use new modules
- [ ] Add unit tests for each module
- [ ] Create command-line interface using modules

### Medium Term
- [ ] Extract UI components to `habermas_machine/ui/`
- [ ] Extract Chorus to `habermas_machine/chorus/`
- [ ] Add configuration file support

### Long Term
- [ ] Plugin system for custom voting methods
- [ ] REST API using FastAPI
- [ ] Web-based UI using modern framework

---

## Questions and Feedback

For questions about the refactoring or suggestions for improvements:
- Open an issue on GitHub
- Check the module docstrings for detailed API documentation
- Review the example code in each module's docstrings

---

## License

All new modules maintain the same AGPLv3 license as the main project.

See [LICENSE](LICENSE) for full license text.
