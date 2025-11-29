# DeepMind Habermas Machine - Reference Implementation

**⚠️ This directory contains reference code from Google DeepMind's original Habermas Machine research.**

## License

This reference code is included under the **Apache License 2.0** as specified by Google DeepMind.

**Important:** This code is **separate** from the main Habermas Machine application (`habermas_machine_app.py`), which is licensed under AGPLv3.

## Purpose

This directory serves as:

1. **Reference material** for understanding DeepMind's original implementation
2. **Prompt templates** that informed the main application's design
3. **Research context** for developers working on the project

## Relationship to Main Application

The main application (`habermas_machine_app.py`) is an **independent implementation** that:
- Does **not import** from this reference code
- Was inspired by DeepMind's research and prompts
- Extends the concept with original features (Chorus, recursive consensus, GUI)
- Is licensed under AGPLv3 (compatible use of Apache 2.0 reference material)

## Contents

- `core/` - Core algorithms and prompt templates from DeepMind
- `utils/` - Utility functions for LLM integration
- `data/` - Sample data and question sets
- `gui/` - GUI components (empty/placeholder)
- `tests/` - Test utilities

## Citation

If you use concepts from this reference implementation, please cite the original research:

```
Tessler, M. H., et al. (2024).
"AI can help humans find common ground in democratic deliberation."
Science, 385(6714), eadq2852.
https://www.science.org/doi/10.1126/science.adq2852
```

## Legal Note

This reference code is provided for educational and research purposes. The Apache 2.0 license allows:
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use

But requires:
- ⚠️ Preservation of copyright and license notices
- ⚠️ Statement of changes if modified
- ⚠️ Inclusion of Apache 2.0 license text

For details, see the Apache License 2.0: https://www.apache.org/licenses/LICENSE-2.0
