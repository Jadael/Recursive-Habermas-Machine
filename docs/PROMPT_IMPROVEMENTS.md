# Prompt Template Improvements

## Overview

Updated prompt templates to incorporate best practices from Google DeepMind's Habermas Machine research while maintaining our simpler, more flexible output format.

## Key Changes

### 1. Democratic Deliberation Framing

**Before:**
- Generic "combine these statements" language
- No context about purpose or methodology

**After:**
- "citizens' jury" framing
- Explicit role: "assisting with democratic deliberation"
- Clear purpose statements

### 2. Explicit Non-Conflict Constraint

**New requirement:**
> "The draft statement must NOT conflict with any of the individual opinions."

This ensures consensus statements don't contradict any participant's position, maintaining the integrity of the deliberative process.

### 3. Step-by-Step Guidance

Both templates now include numbered reasoning steps:

**Consensus Generation:**
1. Analyze opinions (themes, agreement, disagreement)
2. Synthesize consensus statement
3. Ensure non-conflict and completeness

**Ranking Prediction:**
1. Analyze participant's opinion
2. Compare statements to opinion
3. Consider nuances and implications
4. Rank accordingly

### 4. Embedded Examples

Each template includes concrete examples:

**Consensus:** Public transportation example showing how to synthesize opinions
**Ranking:** Climate action example demonstrating reasoning process

### 5. Structured Response Format

Added lightweight structure with "release valve" for model reasoning:

```
---REASONING---
[Optional: Analysis and reasoning]

---STATEMENT--- / ---RANKING---
[The actual output]
```

**Benefits:**
- Models can include chitchat/reasoning if needed
- Easy extraction of official content
- Backward compatible (falls back to entire response if structure absent)

## Implementation

### Files Updated

1. **`habermas_machine/core/templates.py`**
   - Updated `DEFAULT_CANDIDATE_GENERATION_TEMPLATE`
   - Updated `DEFAULT_RANKING_PREDICTION_TEMPLATE`
   - Added `extract_statement_from_response()`
   - Added `extract_ranking_from_response()`

2. **`habermas_machine_app.py`**
   - Updated default templates to match
   - Added extraction methods to HabermasMachine class
   - Integrated extraction into candidate generation flow

3. **`habermas_machine/core/__init__.py`**
   - Exported new extraction functions

### New Extraction Utilities

```python
from habermas_machine.core.templates import (
    extract_statement_from_response,
    extract_ranking_from_response
)

# Extract consensus statement
statement = extract_statement_from_response(llm_response)

# Extract ranking with reasoning
ranking_dict, reasoning = extract_ranking_from_response(llm_response)
```

**Features:**
- Looks for `---STATEMENT---` or `---RANKING---` markers
- Falls back to full response if markers not found
- Handles chatty models gracefully
- Backward compatible with unstructured responses

## Philosophy

### What We Adopted from DeepMind

✅ **Democratic language** - Citizens' jury, deliberation, consensus
✅ **Non-conflict constraint** - Explicit requirement
✅ **Step-by-step guidance** - Numbered reasoning framework
✅ **Embedded examples** - Concrete illustrations
✅ **Purpose clarity** - Why we're doing this task

### What We Kept Ours

✅ **Simple output format** - No XML-like `<answer><sep></answer>`
✅ **JSON for rankings** - Easier than arrow notation
✅ **Flexible parsing** - Graceful degradation
✅ **Optional structure** - Models can follow format or not

### Design Rationale

DeepMind's rigid XML structure (`<answer><sep></answer>`) was likely needed for early models like Chinchilla. Modern models (2024-2025) are much better at following instructions without needing such scaffolding.

Our approach:
- **Teach methodology** (step-by-step, examples, constraints)
- **Suggest structure** (---REASONING---, ---STATEMENT---)
- **Allow flexibility** (works with or without structure)
- **Parse permissively** (multiple fallback strategies)

## Testing

Tested with various response formats:

```bash
python test_extraction.py
```

Results:
- ✅ Structured responses (with ---REASONING--- and ---STATEMENT---)
- ✅ Plain responses (backward compatible)
- ✅ Chatty responses (extracts correctly)
- ✅ JSON with explanation text
- ✅ Plain JSON

## Benefits

### For Model Quality

1. **Better instruction following** - Clear step-by-step guidance
2. **Consistent framing** - Democratic deliberation context
3. **Quality constraints** - Non-conflict requirement
4. **Learning from examples** - Embedded demonstrations

### For Robustness

1. **Handles chatty models** - Gemma, Llama, etc. can ramble safely
2. **Backward compatible** - Works with old and new response formats
3. **Graceful degradation** - Falls back to entire response if structure missing
4. **Easy debugging** - Can see reasoning when models provide it

### For Development

1. **Cleaner extraction** - Simple regex patterns
2. **Reusable utilities** - Exported functions for any consumer
3. **Well-documented** - Docstrings with examples
4. **Tested** - Verification script included

## Migration Notes

### For Existing Code

The extraction happens automatically in `habermas_machine_app.py`:

```python
# In generate_single_candidate():
extracted_statement = self.extract_statement_from_response(clean_response)
```

No changes needed to calling code.

### For Custom Implementations

If you're using the library directly:

```python
from habermas_machine.core import (
    create_candidate_generation_prompt,
    extract_statement_from_response
)

# Generate prompt
prompt = create_candidate_generation_prompt(question, statements)

# Get LLM response
response = your_llm_call(prompt)

# Extract statement
statement = extract_statement_from_response(response)
```

## Future Enhancements

Potential additions:

1. **Critique iteration** - DeepMind's second-round prompts with critiques
2. **Opinion citation** - Require models to reference opinion numbers
3. **Configurable structure** - Toggle between strict/loose formatting
4. **Reasoning analysis** - Use extracted reasoning for quality metrics
5. **Arrow notation option** - Alternative to JSON for rankings

## References

- **DeepMind Research:** `docs/deepmind_reference/core/prompts.py`
- **Original Paper:** "AI can help humans find common ground in democratic deliberation" (Science, 2024)
- **Our Analysis:** See comparison document for detailed diff

---

**Summary:** We've enhanced our prompts with DeepMind's proven deliberative democracy methodology while maintaining the simplicity and flexibility that makes our implementation robust across diverse model families.
