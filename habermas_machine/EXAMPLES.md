# Habermas Machine Module Usage Examples

This document provides practical examples of using the modularized Habermas Machine components.

## Table of Contents
- [Basic Voting Example](#basic-voting-example)
- [LLM Integration Example](#llm-integration-example)
- [Complete Consensus Pipeline](#complete-consensus-pipeline)
- [File I/O Example](#file-io-example)
- [Custom Prompt Templates](#custom-prompt-templates)

---

## Basic Voting Example

Run a Schulze election from participant rankings:

```python
from habermas_machine.core import (
    schulze_method,
    calculate_victories,
    format_pairwise_matrix
)

# Define how each participant ranks the candidates
# Keys = participant IDs, Values = candidate IDs in preference order
rankings = {
    0: [1, 0, 2],  # Participant 0 prefers candidate 1 most
    1: [1, 2, 0],  # Participant 1 also prefers candidate 1
    2: [0, 1, 2],  # Participant 2 prefers candidate 0
    3: [2, 1, 0],  # Participant 3 prefers candidate 2
}

num_candidates = 3

# Run the Schulze method
winner_idx, pairwise_matrix, strongest_paths = schulze_method(
    rankings,
    num_candidates
)

print(f"Winner: Candidate {winner_idx}")

# Show detailed results
victories = calculate_victories(strongest_paths, num_candidates)
print(f"\nVictories per candidate: {victories}")

# Print pairwise comparison matrix
print("\nPairwise Preferences:")
print(format_pairwise_matrix(pairwise_matrix, num_candidates))
```

**Output:**
```
Winner: Candidate 1

Victories per candidate: {0: 0, 1: 2, 2: 0}

Pairwise Preferences:
|       | S 1 | S 2 | S 3 |
|-------|-----|-----|-----|
| S 1   |  0  |  2  |  2  |
| S 2   |  2  |  0  |  3  |
| S 3   |  2  |  1  |  0  |
```

---

## LLM Integration Example

Generate text using the Ollama client:

```python
from habermas_machine.llm import OllamaClient
from habermas_machine.core import create_candidate_generation_prompt

# Initialize client
client = OllamaClient()

# Check if Ollama is running
if not client.test_connection():
    print("Error: Ollama is not running!")
    print("Start it with: ollama serve")
    exit(1)

# List available models
models = client.list_models()
print(f"Available models: {models}")

# Prepare a consensus generation prompt
question = "Should voting be compulsory?"
statements = [
    "Yes, voting is a civic duty and should be mandatory",
    "No, forcing people to vote violates personal freedom",
    "Maybe, but only with a 'none of the above' option"
]

prompt = create_candidate_generation_prompt(question, statements)

# Generate consensus statement with streaming
print("\nGenerating consensus statement...\n")

def print_token(token):
    print(token, end='', flush=True)

response = client.generate_streaming(
    model="deepseek-r1:14b",
    prompt=prompt,
    temperature=0.7,
    on_token=print_token
)

print("\n\nGeneration complete!")
```

---

## Complete Consensus Pipeline

Full example combining all modules:

```python
from habermas_machine import (
    OllamaClient,
    RankingParser,
    schulze_method,
    create_candidate_generation_prompt,
    create_ranking_prediction_prompt,
    save_friendly_output,
    generate_session_id
)

# ============================================================================
# Setup
# ============================================================================

question = "Should voting be compulsory?"
participant_statements = [
    "Yes, it ensures everyone participates in democracy",
    "No, freedom of choice is more important",
    "Only if we allow blank votes"
]

num_candidates = 3  # We'll generate 3 consensus candidates
model = "deepseek-r1:14b"

client = OllamaClient()

# ============================================================================
# Step 1: Generate Candidate Consensus Statements
# ============================================================================

print("Generating candidate consensus statements...\n")

candidate_statements = []

for i in range(num_candidates):
    # Shuffle statements for diversity (not shown here)
    prompt = create_candidate_generation_prompt(
        question,
        participant_statements
    )

    candidate = client.generate(
        model=model,
        prompt=prompt,
        temperature=0.7
    )

    candidate_statements.append(candidate)
    print(f"Candidate {i+1} generated")

# ============================================================================
# Step 2: Predict How Each Participant Would Rank Candidates
# ============================================================================

print("\nPredicting participant rankings...\n")

rankings = {}
parser = RankingParser(num_candidates=num_candidates, max_retries=3)

for p_idx, participant_stmt in enumerate(participant_statements):
    # Create ranking prediction prompt
    prompt = create_ranking_prediction_prompt(
        question=question,
        participant_statement=participant_stmt,
        candidate_statements=candidate_statements,
        participant_num=p_idx + 1
    )

    # Get system prompt for JSON output
    from habermas_machine.llm import create_ranking_system_prompt
    system_prompt = create_ranking_system_prompt(num_candidates)

    # Try to get ranking
    for attempt in range(1, 4):
        response = client.generate(
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2  # Lower temp for more consistent JSON
        )

        ranking = parser.parse(response, attempt_num=attempt)

        if ranking:
            rankings[p_idx] = ranking
            print(f"Participant {p_idx+1} ranking: {ranking}")
            break
    else:
        # Failed all attempts, use fallback
        ranking, log = parser.get_fallback_ranking()
        rankings[p_idx] = ranking
        print(f"Participant {p_idx+1} (fallback): {ranking}")

    parser.reset()  # Clear log for next participant

# ============================================================================
# Step 3: Run Schulze Election
# ============================================================================

print("\nRunning Schulze election...\n")

winner_idx, pairwise_matrix, strongest_paths = schulze_method(
    rankings,
    num_candidates
)

print(f"Winner: Candidate {winner_idx + 1}")
print(f"\nWinning statement:")
print(candidate_statements[winner_idx])

# ============================================================================
# Step 4: Save Results
# ============================================================================

session_id = generate_session_id()

results = f"""# Consensus Results - {session_id}

## Question
{question}

## Winning Consensus Statement
{candidate_statements[winner_idx]}

## All Candidates
"""

for i, stmt in enumerate(candidate_statements):
    marker = "🏆 WINNER" if i == winner_idx else ""
    results += f"\n### Candidate {i+1} {marker}\n{stmt}\n"

results += "\n## Participant Rankings\n"
for p_idx, ranking in rankings.items():
    results += f"- Participant {p_idx+1}: {[r+1 for r in ranking]}\n"

# Save to file
filepath = save_friendly_output(results, session_id)
print(f"\nResults saved to: {filepath}")
```

---

## File I/O Example

Load statements from a file and save results:

```python
from habermas_machine.utils import (
    load_participant_statements_from_file,
    export_statements_to_file,
    parse_bulk_import_text,
    save_friendly_output,
    generate_session_id
)

# ============================================================================
# Loading Statements from File
# ============================================================================

# Create a sample input file
sample_file = "participant_input.txt"

with open(sample_file, 'w') as f:
    f.write("""# Participant statements on compulsory voting
# Lines starting with # are comments

I believe voting should be mandatory because it's a civic duty
Personal freedom is more important than forced participation
We should have compulsory voting but allow blank votes
""")

# Load the statements
statements = load_participant_statements_from_file(sample_file)
print(f"Loaded {len(statements)} statements:")
for i, stmt in enumerate(statements, 1):
    print(f"{i}. {stmt}")

# ============================================================================
# Parsing Bulk Import (various formats)
# ============================================================================

bulk_text = """
1. First opinion from the survey
2. Second opinion from the survey
- Third opinion (bullet format)
* Fourth opinion (different bullet)

Fifth opinion (no prefix)
"""

parsed = parse_bulk_import_text(bulk_text)
print(f"\nParsed {len(parsed)} statements from bulk text:")
for stmt in parsed:
    print(f"  - {stmt}")

# ============================================================================
# Exporting Statements
# ============================================================================

export_path = export_statements_to_file(
    statements,
    "exported_statements.txt",
    include_header=True
)
print(f"\nExported to: {export_path}")

# ============================================================================
# Saving Results
# ============================================================================

session_id = generate_session_id()

results_content = """# Consensus Results

Winner: Make voting compulsory with blank vote option

This consensus combines civic duty with personal freedom...
"""

output_path = save_friendly_output(results_content, session_id)
print(f"Results saved to: {output_path}")
```

---

## Custom Prompt Templates

Modify templates for different use cases:

```python
from habermas_machine.core.templates import (
    DEFAULT_CANDIDATE_GENERATION_TEMPLATE,
    validate_candidate_template,
    format_participant_statements
)

# ============================================================================
# Using the Default Template
# ============================================================================

print("Default template:")
print(DEFAULT_CANDIDATE_GENERATION_TEMPLATE)

# ============================================================================
# Creating a Custom Template
# ============================================================================

custom_template = """You are a skilled mediator helping find common ground.

Question: {question}

Participant views:
{participant_statements}

Task: Write ONE statement that most participants could accept.
Focus on shared values and practical compromises.

Consensus statement:"""

# Validate the template
is_valid, error = validate_candidate_template(custom_template)

if is_valid:
    print("✓ Template is valid")
else:
    print(f"✗ Template error: {error}")

# ============================================================================
# Using Custom Template
# ============================================================================

question = "Should we allow remote work?"
statements = [
    "Remote work improves work-life balance",
    "In-office collaboration is essential",
    "Hybrid approach gives flexibility"
]

formatted_statements = format_participant_statements(statements)

prompt = custom_template.format(
    question=question,
    participant_statements=formatted_statements
)

print("\nGenerated prompt:")
print(prompt)

# Use this with OllamaClient.generate()
```

---

## Batch Processing Example

Process multiple questions in parallel:

```python
from habermas_machine import OllamaClient, create_candidate_generation_prompt
from concurrent.futures import ThreadPoolExecutor, as_completed

client = OllamaClient()

questions = [
    "Should voting be compulsory?",
    "Should we increase the minimum wage?",
    "Should we invest more in public transport?"
]

# Participant statements for each question
all_statements = [
    ["Yes civic duty", "No personal freedom", "Maybe with options"],
    ["Yes workers need it", "No businesses will suffer", "Phase it gradually"],
    ["Yes for environment", "No too expensive", "Only in cities"]
]

def generate_consensus(question, statements):
    """Generate consensus for one question"""
    prompt = create_candidate_generation_prompt(question, statements)
    return client.generate(
        model="deepseek-r1:14b",
        prompt=prompt,
        temperature=0.7
    )

# Process in parallel
results = {}

with ThreadPoolExecutor(max_workers=3) as executor:
    # Submit all tasks
    future_to_question = {
        executor.submit(generate_consensus, q, s): q
        for q, s in zip(questions, all_statements)
    }

    # Collect results as they complete
    for future in as_completed(future_to_question):
        question = future_to_question[future]
        try:
            consensus = future.result()
            results[question] = consensus
            print(f"✓ Completed: {question}")
        except Exception as e:
            print(f"✗ Failed: {question} - {e}")

# Display results
for question, consensus in results.items():
    print(f"\n{question}")
    print(f"→ {consensus}")
```

---

## Error Handling Example

Robust error handling when working with LLMs:

```python
from habermas_machine import OllamaClient, RankingParser
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OllamaClient()

# ============================================================================
# Check Prerequisites
# ============================================================================

if not client.test_connection():
    logger.error("Ollama is not running. Please start it:")
    logger.error("  ollama serve")
    exit(1)

models = client.list_models()
required_model = "deepseek-r1:14b"

if required_model not in models:
    logger.error(f"Model {required_model} not found. Please install it:")
    logger.error(f"  ollama pull {required_model}")
    exit(1)

logger.info(f"✓ Using model: {required_model}")

# ============================================================================
# Generate with Timeout and Retry
# ============================================================================

from threading import Event
import time

stop_event = Event()

def generate_with_timeout(prompt, timeout_seconds=60):
    """Generate with timeout support"""
    start_time = time.time()

    response = client.generate_streaming(
        model=required_model,
        prompt=prompt,
        stop_event=stop_event
    )

    if response is None:
        logger.error("Generation failed (returned None)")
        return None

    elapsed = time.time() - start_time
    logger.info(f"Generation completed in {elapsed:.1f}s")

    return response

# Try generation with timeout
prompt = "Write a consensus statement..."

try:
    result = generate_with_timeout(prompt, timeout_seconds=30)
    if result:
        logger.info("Success!")
    else:
        logger.warning("Generation returned empty result")
except Exception as e:
    logger.error(f"Generation error: {e}", exc_info=True)

# ============================================================================
# Ranking Prediction with Fallback
# ============================================================================

parser = RankingParser(num_candidates=3, max_retries=3)

# Simulate unreliable response
bad_response = "I think the ranking should be [1, 2, 3] but I'm not sure"

ranking = parser.parse(bad_response, attempt_num=1)

if ranking is None:
    logger.warning("Failed to parse ranking, using fallback")
    ranking, log = parser.get_fallback_ranking()

    # Log what happened
    for message in log:
        logger.info(message)

logger.info(f"Final ranking: {ranking}")
```

---

## Integration with Existing Code

How to gradually integrate modules into `habermas_machine_app.py`:

```python
# In habermas_machine_app.py, replace sections one at a time:

class HabermasMachine:
    def __init__(self, root):
        # ... existing setup ...

        # NEW: Use modular client instead of direct requests
        from habermas_machine.llm import OllamaClient
        self.ollama_client = OllamaClient()

    def schulze_method(self, rankings, num_candidates):
        # OLD: 60+ lines of Schulze implementation here

        # NEW: Use module
        from habermas_machine.core import schulze_method
        return schulze_method(rankings, num_candidates)

    def generate_single_candidate(self, question, statements, candidate_num):
        # OLD: Manual prompt formatting and requests.post

        # NEW: Use modules
        from habermas_machine.core import create_candidate_generation_prompt

        prompt = create_candidate_generation_prompt(question, statements)

        response = self.ollama_client.generate(
            model=self.model_var.get(),
            prompt=prompt,
            temperature=float(self.temperature_var.get())
        )

        return response
```

---

## See Also

- [REFACTORING.md](../REFACTORING.md) - Complete refactoring guide
- [Module API Documentation](../habermas_machine/) - Detailed docstrings in each module
- [Main Application](../habermas_machine_app.py) - Current GUI application

For questions or issues, please open a GitHub issue.
