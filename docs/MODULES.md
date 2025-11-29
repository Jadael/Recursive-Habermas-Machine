# Habermas Machine - Module Reference

Quick reference for all modularized components.

## 📦 Package Overview

```
habermas_machine/           # Main package
├── __init__.py            # Exports: schulze_method, OllamaClient, etc.
├── README.md              # Package introduction
├── EXAMPLES.md            # Usage examples
│
├── core/                  # Consensus & voting algorithms
│   ├── __init__.py
│   ├── voting.py         # Schulze method (260 lines)
│   └── templates.py      # Prompt templates (270 lines)
│
├── llm/                   # LLM integration
│   ├── __init__.py
│   ├── client.py         # Ollama API client (230 lines)
│   └── response_parser.py # JSON parsing (300 lines)
│
└── utils/                 # Utilities
    ├── __init__.py
    └── file_utils.py     # File I/O (240 lines)
```

**Total**: ~1,300 lines across 6 focused modules (vs 2,138 line monolith)

---

## 🔧 Module APIs

### `core.voting` - Schulze Method

**Main Functions**:
```python
schulze_method(rankings, num_candidates) -> (winner, pairwise, paths)
calculate_victories(strongest_paths, num_candidates) -> dict
rank_candidates_by_victories(strongest_paths, num_candidates) -> list
format_pairwise_matrix(matrix, num_candidates) -> str
format_strongest_paths_matrix(paths, num_candidates) -> str
```

**Example**:
```python
from habermas_machine.core import schulze_method

rankings = {0: [1, 0, 2], 1: [1, 2, 0], 2: [0, 1, 2]}
winner, pairwise, paths = schulze_method(rankings, 3)
```

**Lines**: 260 | **Dependencies**: None | **Complexity**: O(n³)

---

### `core.templates` - Prompt Templates

**Main Functions**:
```python
get_default_templates() -> dict
create_candidate_generation_prompt(question, statements, template=None) -> str
create_ranking_prediction_prompt(question, participant, candidates, num, template=None) -> str
format_participant_statements(statements) -> str
format_candidate_statements(statements) -> str
validate_candidate_template(template) -> (bool, str)
validate_ranking_template(template) -> (bool, str)
```

**Placeholders**:
- `{question}`: Deliberation question
- `{participant_statements}`: Formatted participant statements
- `{participant_statement}`: Single participant statement
- `{num_candidates}`: Number of candidates
- `{candidate_statements}`: Formatted candidate statements

**Example**:
```python
from habermas_machine.core import create_candidate_generation_prompt

prompt = create_candidate_generation_prompt(
    "Should voting be compulsory?",
    ["Yes civic duty", "No personal freedom"]
)
```

**Lines**: 270 | **Dependencies**: None

---

### `llm.client` - Ollama API Client

**Main Class**: `OllamaClient`

**Methods**:
```python
__init__(base_url="http://localhost:11434")
generate_streaming(model, prompt, system_prompt=None, temperature=0.7,
                   top_p=0.9, top_k=40, stop_event=None,
                   on_token=None, on_complete=None) -> str
generate(model, prompt, ...) -> str
cancel_current_generation()
test_connection() -> bool
list_models() -> list
```

**Example**:
```python
from habermas_machine.llm import OllamaClient

client = OllamaClient()
response = client.generate(
    model="deepseek-r1:14b",
    prompt="Write a consensus..."
)
```

**Lines**: 230 | **Dependencies**: `requests`

---

### `llm.response_parser` - Response Parsing

**Main Functions**:
```python
clean_deepseek_response(response) -> str
extract_json_from_text(text) -> dict | None
validate_ranking(ranking, num_candidates, zero_indexed=True) -> bool
parse_ranking_response(response, num_candidates, max_retries=1, attempt=1) -> (list|None, str)
create_random_ranking(num_candidates) -> list
create_ranking_system_prompt(num_candidates) -> str
```

**Main Class**: `RankingParser`

**Methods**:
```python
__init__(num_candidates, max_retries=3)
parse(response, attempt_num) -> list | None
get_fallback_ranking() -> (list, list)
get_successful_ranking(ranking) -> (list, list)
reset()
```

**Example**:
```python
from habermas_machine.llm import RankingParser

parser = RankingParser(num_candidates=3, max_retries=3)
ranking = parser.parse(llm_response, attempt_num=1)

if not ranking:
    ranking, log = parser.get_fallback_ranking()
```

**Lines**: 300 | **Dependencies**: `json`, `re`, `ast`

---

### `utils.file_utils` - File I/O

**Main Functions**:
```python
generate_session_id() -> str
save_friendly_output(content, session_id, output_dir=".") -> Path | None
save_detailed_output(content, session_id, output_dir=".") -> Path | None
save_recursive_results(content, session_id, output_dir=".") -> Path | None
save_recursive_detailed(content, session_id, output_dir=".") -> Path | None
load_participant_statements_from_file(filepath) -> list
export_statements_to_file(statements, filepath, include_header=True) -> Path | None
parse_bulk_import_text(text) -> list
sanitize_filename(filename) -> str
```

**File Formats**:
- Results: `habermas_results_YYYYMMDD_HHMMSS.md`
- Detailed: `habermas_detailed_YYYYMMDD_HHMMSS.md`
- Recursive: `habermas_recursive_results_YYYYMMDD_HHMMSS.md`
- Recursive Detailed: `habermas_recursive_detailed_YYYYMMDD_HHMMSS.md`

**Example**:
```python
from habermas_machine.utils import save_friendly_output, generate_session_id

session_id = generate_session_id()
save_friendly_output("# Results\n...", session_id)
```

**Lines**: 240 | **Dependencies**: `pathlib`, `datetime`

---

## 📚 Documentation

| File | Purpose | Lines |
|------|---------|-------|
| `REFACTORING.md` | Complete refactoring guide | 600+ |
| `habermas_machine/EXAMPLES.md` | Usage examples | 400+ |
| `habermas_machine/README.md` | Package introduction | 100 |
| `MODULES.md` (this file) | Quick reference | 150 |

---

## 🎯 Common Import Patterns

### Minimal Import (just what you need)
```python
from habermas_machine.core import schulze_method
from habermas_machine.llm import OllamaClient
```

### Convenience Import (top-level exports)
```python
from habermas_machine import (
    schulze_method,
    OllamaClient,
    RankingParser,
    save_friendly_output
)
```

### Full Module Import (all functions)
```python
from habermas_machine.core import voting, templates
from habermas_machine.llm import client, response_parser
```

---

## 🔄 Migration Guide

Replace these patterns in `habermas_machine_app.py`:

### Voting
```python
# Before:
winner, pairwise, paths = self.schulze_method(rankings, num_candidates)

# After:
from habermas_machine.core import schulze_method
winner, pairwise, paths = schulze_method(rankings, num_candidates)
```

### LLM Client
```python
# Before:
response = requests.post("http://localhost:11434/api/generate", json={...})

# After:
from habermas_machine.llm import OllamaClient
client = OllamaClient()
response = client.generate(model=model, prompt=prompt)
```

### Response Parsing
```python
# Before:
# 100+ lines of JSON parsing with try/except

# After:
from habermas_machine.llm import RankingParser
parser = RankingParser(num_candidates, max_retries=3)
ranking = parser.parse(response, attempt_num=1)
```

### File Operations
```python
# Before:
with open(f"habermas_results_{session_id}.md", 'w') as f:
    f.write(content)

# After:
from habermas_machine.utils import save_friendly_output
save_friendly_output(content, session_id)
```

---

## ⚙️ Configuration

All modules use standard Python logging:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('habermas_machine')
```

**Log levels**:
- `DEBUG`: Detailed diagnostic information
- `INFO`: Confirmation of normal operation
- `WARNING`: Non-critical issues (e.g., fallback to random ranking)
- `ERROR`: Serious problems (e.g., API connection failure)

---

## 🧪 Testing

Each module can be tested independently:

```bash
# Test voting
python -c "from habermas_machine.core import schulze_method; \
  rankings = {0: [0, 1, 2], 1: [1, 0, 2], 2: [2, 1, 0]}; \
  winner, _, _ = schulze_method(rankings, 3); \
  print(f'Winner: {winner}')"

# Test LLM client
python -c "from habermas_machine.llm import OllamaClient; \
  client = OllamaClient(); \
  print('Ollama running:', client.test_connection())"

# Test file utils
python -c "from habermas_machine.utils import generate_session_id; \
  print('Session ID:', generate_session_id())"
```

---

## 📊 Module Statistics

| Module | Lines | Functions | Classes | Imports |
|--------|-------|-----------|---------|---------|
| `core.voting` | 260 | 6 | 0 | 2 |
| `core.templates` | 270 | 9 | 0 | 1 |
| `llm.client` | 230 | 6 | 1 | 5 |
| `llm.response_parser` | 300 | 9 | 1 | 6 |
| `utils.file_utils` | 240 | 10 | 0 | 3 |
| **Total** | **1,300** | **40** | **2** | **17** |

**Comparison to monolith**:
- Original: 2,138 lines in one file
- Refactored: 1,300 lines across 6 modules (39% reduction through better organization)
- Average module size: 216 lines (vs 2,138 line monolith)

---

## 🚀 Future Modules

Planned for extraction:

### `ui.main_window`
Main application window and layout orchestration

### `ui.inputs_panel`
Left column: question input, settings, templates

### `ui.outputs_panel`
Middle column: friendly results, detailed records

### `ui.debug_panel`
Right column: prompt/response debugging

### `chorus.repository`
Value statement repository management

### `chorus.feedback`
Proposal feedback simulation

### `chorus.verbatim`
Quote sampling and diversity algorithms

---

## 📖 Further Reading

- [REFACTORING.md](REFACTORING.md) - Detailed refactoring guide
- [habermas_machine/EXAMPLES.md](habermas_machine/EXAMPLES.md) - Practical examples
- [CLAUDE.md](CLAUDE.md) - Project overview and context
- Module docstrings - API documentation with examples

---

## ⚖️ License

AGPLv3 - All modules maintain the same license as the main project.

See [LICENSE](LICENSE) for details.
