# Quick Start Guide - Habermas Machine 2.0

Get up and running with the Habermas Machine in 5 minutes!

---

## Prerequisites

1. **Python 3.8 or higher**
   ```bash
   python --version  # Should show 3.8+
   ```

2. **Ollama installed and running**
   - Download from: https://ollama.com
   - Verify it's running: `ollama list`

3. **At least one language model**
   ```bash
   ollama pull deepseek-r1:14b  # Recommended (reasoning-capable)
   # OR
   ollama pull llama3.1         # Alternative
   ```

---

## Installation

### Step 1: Install Python Dependencies

```bash
pip install customtkinter requests numpy matplotlib pillow scikit-learn
```

### Step 2: Verify Installation

```bash
cd Recursive-Habermas-Machine
python test_imports.py
```

You should see:
```
✓ All imports and basic tests passed!
```

---

## Running the Application

### Option 1: Simple Launcher (Recommended)

```bash
python main.py
```

### Option 2: Original GUI

```bash
python habermas_machine.py
```

---

## First Consensus (5-minute tutorial)

### Step 1: Load Sample Data

The application comes pre-loaded with a sample question:
- **Question**: "Should voting be compulsory?"
- **5 participant opinions** with diverse perspectives

### Step 2: Generate Consensus

1. Click **"Generate Consensus (Single Run)"** button
2. Watch the process in the middle column:
   - Candidate statements generated
   - Rankings predicted
   - Election simulated
   - Winner announced

### Step 3: Review Results

**Friendly Output** shows:
- The winning consensus statement (in a highlight box at top)
- How it was determined
- Original participant statements

**Detailed Records** shows:
- All candidate statements
- Preference rankings for each participant
- Voting matrices
- Complete election process

---

## Using New Modules (For Developers)

### Import the New API

```python
# Core modules
from habermas_machine.core import (
    generate_opinion_only_cot_prompt,      # DeepMind's CoT prompts
    generate_opinion_only_ranking_prompt,   # Arrow notation ranking
    schulze_method,                         # Voting
)

# Utilities
from habermas_machine.utils import (
    OllamaClient,                # API client
    OllamaEmbeddingHelper,       # Semantic similarity
    HabermasLLMSummarizer,       # LLM summaries
)

# Data
from habermas_machine.data.sample_statements import (
    SAMPLE_VALUE_STATEMENTS,         # 12 stakeholder personas
    COMPULSORY_VOTING_OPINIONS,      # Classic example
    get_filtered_statements,          # Filter by dept/role/location
)
```

### Example 1: Generate a Prompt

```python
from habermas_machine.core import generate_opinion_only_cot_prompt

prompt = generate_opinion_only_cot_prompt(
    question="Should remote work be mandatory?",
    opinions=[
        "I value flexibility and work-life balance...",
        "I believe in-person collaboration is essential...",
        "We should let each team decide..."
    ]
)

print(prompt)
# Uses DeepMind's production-tested template with <answer><sep></answer> format
```

### Example 2: Run a Schulze Election

```python
from habermas_machine.core import schulze_method

# Participant rankings (each person ranks candidates 0-2)
rankings = {
    0: [1, 0, 2],  # Participant 0 prefers candidate 1, then 0, then 2
    1: [0, 1, 2],  # Participant 1 prefers candidate 0, then 1, then 2
    2: [1, 2, 0],  # Participant 2 prefers candidate 1, then 2, then 0
}

winner, pairwise_matrix, strongest_paths = schulze_method(rankings, num_candidates=3)

print(f"Winner: Candidate {winner}")
print(f"Pairwise matrix: {pairwise_matrix}")
```

### Example 3: Use Ollama Client

```python
from habermas_machine.utils import OllamaClient

client = OllamaClient(default_model="deepseek-r1:14b")

# Simple generation
response = client.generate(
    "Explain quantum computing in one sentence",
    temperature=0.2
)
print(response)

# Streaming generation
for token in client.generate_stream("Write a haiku about AI"):
    print(token, end="", flush=True)

# JSON generation with retry
result = client.generate_json(
    'Return JSON: {"sentiment": "positive", "score": 8}',
    max_retries=3
)
print(result)  # {'sentiment': 'positive', 'score': 8}
```

### Example 4: Filter Sample Data

```python
from habermas_machine.data.sample_statements import get_filtered_statements

# Get all remote workers
remote = get_filtered_statements(location="Remote")
print(f"Found {len(remote)} remote workers")

# Get IT managers
it_managers = get_filtered_statements(department="IT", role="Manager")
for stmt in it_managers:
    print(f"{stmt['role']} at {stmt['location']}")
```

---

## Testing Your Setup

### Run the Test Suite

```bash
python test_imports.py
```

This verifies:
- ✓ All modules import correctly
- ✓ Prompt generation works
- ✓ Schulze voting works
- ✓ Data filtering works
- ✓ Ollama client connects

### Quick Consensus Test

```python
# test_quick_consensus.py
from habermas_machine.data.sample_statements import COMPULSORY_VOTING_OPINIONS
from habermas_machine.core import generate_opinion_only_cot_prompt

prompt = generate_opinion_only_cot_prompt(
    question="Should voting be compulsory?",
    opinions=COMPULSORY_VOTING_OPINIONS
)

print("Prompt generated successfully!")
print(f"Length: {len(prompt)} characters")
print("\nFirst 200 chars:")
print(prompt[:200] + "...")
```

---

## Troubleshooting

### Issue: "Ollama not running"

**Solution:**
```bash
# Start Ollama (it should auto-start, but if not):
ollama serve  # In one terminal

# In another terminal, verify:
ollama list
```

### Issue: "Missing dependency: customtkinter"

**Solution:**
```bash
pip install customtkinter requests numpy matplotlib pillow scikit-learn
```

### Issue: "No module named 'habermas_machine'"

**Solution:**
Make sure you're in the project root directory:
```bash
cd Recursive-Habermas-Machine
python main.py
```

### Issue: "Model not found: deepseek-r1:14b"

**Solution:**
```bash
ollama pull deepseek-r1:14b
# OR use a different model:
ollama pull llama3.1
```

Then update the model in the GUI Settings tab.

### Issue: Unicode errors on Windows

**Solution:**
The test script handles this automatically. If you see errors in your own scripts:
```python
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
```

---

## Next Steps

### Learn More

- **[README_v2.md](README_v2.md)**: Complete guide to new structure
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)**: Migrating from old code
- **[CLAUDE.md](CLAUDE.md)**: Full project context and philosophy

### Try Advanced Features

1. **Recursive Consensus**
   - Use for groups larger than 12 participants
   - Automatically subdivides and merges

2. **Custom Prompts**
   - Edit templates in the Templates tab
   - Experiment with different instructions

3. **Chorus Mode** (if available in your version)
   - Simulate stakeholder feedback
   - Avoid survey fatigue

### Extend the Code

The new modular structure makes it easy to:
- Add new voting methods to `core/voting.py`
- Create new prompt templates in `core/prompts.py`
- Build custom utilities in `utils/`
- Add more sample data in `data/`

---

## Configuration Options

### Model Settings (in GUI)

- **Model**: Choose from available Ollama models
- **Temperature**: 0.0 (deterministic) to 2.0 (creative)
  - Consensus generation: 0.6-0.8 recommended
  - Ranking prediction: 0.2-0.4 recommended (more deterministic)
- **Top P**: Nucleus sampling (0.9 default)
- **Top K**: Top-k sampling (40 default)

### Consensus Settings

- **Number of Candidates**: How many consensus statements to generate (4 default)
- **Max Retries**: JSON parsing retry attempts (3 default)
- **Max Group Size**: For recursive consensus (12 default)
- **Voting Strategy**: "Own groups only" or "All participants"

---

## Using with Finetuned Models (Future)

The system is designed to support both:

1. **Prompted Models** (current): Instruct/chat-tuned models like deepseek-r1, llama3.1
2. **Finetuned Models** (future): Base models finetuned on Habermas Machine data

To use a finetuned model:
```python
client = OllamaClient(default_model="your-finetuned-model")

# Use without complex prompts (model is already trained)
response = client.generate("Opinion 1: ...\nOpinion 2: ...")
```

---

## Getting Help

- **Issues**: Create a GitHub issue with details
- **Questions**: Check existing documentation first
- **Ollama Problems**: Visit https://ollama.com/docs

---

## Success Checklist

- [ ] Python 3.8+ installed
- [ ] Ollama running with at least one model
- [ ] Dependencies installed (`pip install ...`)
- [ ] `python test_imports.py` passes
- [ ] GUI launches with `python main.py`
- [ ] Sample consensus generates successfully
- [ ] Can access new modules in Python

**If all checked**: You're ready to use Habermas Machine 2.0! 🎉

---

**Estimated time**: 5-10 minutes for full setup
**Next**: Try generating your first consensus with the sample data!
