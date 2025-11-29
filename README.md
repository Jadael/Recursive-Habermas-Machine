# Habermas Machine

**AI-assisted consensus building and stakeholder feedback simulation**

An implementation and extension of Google DeepMind's [Habermas Machine research](https://www.science.org/doi/10.1126/science.adq2852)—using large language models to help diverse groups find common ground on contentious questions through simulated deliberation and democratic voting.

## What Does It Do?

The Habermas Machine helps groups find consensus by:

1. **Collecting** individual opinions on a question
2. **Synthesizing** multiple candidate consensus statements using AI
3. **Predicting** how each participant would rank the candidates
4. **Electing** the statement with broadest support using the [Schulze voting method](https://en.wikipedia.org/wiki/Schulze_method)
5. **Presenting** the result as a fair compromise representing the group

**Example:**
```
Question: "Should voting be compulsory?"

5 participants with diverse views
       ↓
AI generates 4 candidate consensus statements
       ↓
System predicts how each person ranks the candidates
       ↓
Schulze election identifies the most broadly acceptable statement
       ↓
"While compulsory voting could increase participation,
it should be implemented thoughtfully with exemptions
for conscientious objection..."
```

## Two Components

### 1. **Habermas Machine** (Core)
Finds consensus statements that synthesize diverse opinions on abstract questions.

- **Single-run consensus**: For small groups (≤12 participants)
- **Recursive consensus**: For large groups (automatically divides into subgroups, finds consensus within each, then merges)
- **Transparent process**: See exact prompts, responses, and voting matrices
- **Schulze voting**: Condorcet-compliant, strategically robust election method

### 2. **Habermas Chorus** (Extension)
Simulates stakeholder feedback on proposals without survey fatigue.

**The Problem:** Organizations face "survey fatigue"—employees tire of repeated surveys on every new proposal.

**The Solution:** Maintain a repository of employee "value statements" that can be queried repeatedly to simulate feedback without re-surveying.

**How It Works:**
- Employees write persistent value statements (e.g., "I prioritize work-life balance and transparent communication")
- When evaluating a proposal, the system simulates how each person would respond based on their values
- Aggregates results into approval ratings, top concerns, suggestions, and representative quotes
- Provides targeted feedback by department, role, or location

## Features

- 🎯 **Find consensus** among divergent opinions
- 🔄 **Recursive processing** for large groups (100+ participants)
- 🗳️ **Democratic voting** using Schulze method
- 📊 **Feedback analytics** with sentiment analysis and visualizations
- 🔍 **Full transparency** - see all prompts, responses, and voting matrices
- 🎨 **Modern GUI** built with CustomTkinter
- 🤖 **Local AI** via Ollama (no cloud APIs required)
- 📝 **Customizable prompts** for different use cases

## Quick Start

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.com) installed and running locally

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Recursive-Habermas-Machine.git
cd Recursive-Habermas-Machine

# Install Python dependencies
pip install customtkinter requests numpy matplotlib pillow scikit-learn

# Pull a language model (if not already installed)
ollama pull deepseek-r1:14b

# Run the application
python main.py
```

### First Run

1. The GUI launches with sample data pre-loaded
2. Click **"Generate Consensus (Single Run)"** to see it in action
3. Review the consensus statement in the "Friendly Output" tab
4. Explore "Detailed Records" to see the full process
5. Try the **Chorus** tab to simulate stakeholder feedback

For detailed instructions, see [QUICKSTART.md](QUICKSTART.md).

## Use Cases

### Consensus Building
- **Policy formation**: Help organizations draft policies that reflect diverse employee values
- **Community decisions**: Facilitate deliberation on local issues
- **Research synthesis**: Find common ground in expert opinions
- **Conflict resolution**: Identify acceptable compromises in disputes

### Stakeholder Feedback (Chorus)
- **Proposal evaluation**: Quickly gauge reaction to new initiatives
- **Change management**: Understand concerns before rollout
- **Product decisions**: Simulate user feedback on features
- **Budget allocation**: Test support for spending priorities

## How It Works

### Consensus Algorithm

```
1. Generate N candidates (default: 4)
   - Each uses shuffled participant statements to avoid bias
   - Customizable prompt templates

2. Predict rankings
   - System predicts how each participant ranks candidates
   - JSON-formatted responses with multi-retry fallback
   - Lower temperature (0.2) for deterministic predictions

3. Run Schulze election
   - Build pairwise preference matrix
   - Calculate strongest paths (Floyd-Warshall)
   - Identify Condorcet winner

4. Recursive mode (for large groups)
   - Divide into subgroups (max size: 12)
   - Find consensus within each
   - Treat subgroup consensuses as new "participants"
   - Recurse until single consensus emerges
```

### Chorus Workflow

```
1. Value Statement Repository
   - Employees control their own statements
   - Link to metadata (department, role, location)
   - Persistent and reusable

2. Proposal Evaluation
   - Submit proposal text
   - Filter stakeholders by metadata
   - LLM generates simulated feedback per person
   - JSON output: sentiment, concerns, suggestions, importance

3. Aggregation & Analysis
   - Approval percentages by category
   - Top themes and concerns
   - Department/role breakdowns
   - Intelligent verbatim quote sampling (diverse, relevant)
   - Visual charts and graphs
```

## Design Philosophy

### Transparency Over Optimization
Users see exact prompts, responses, and voting matrices. The "robot lobbyist" metaphor requires full visibility—understanding and being able to "game" the system is strategic representation, not manipulation.

### Iterative Reliability
LLM outputs are unreliable. The system uses multi-retry JSON parsing with comprehensive logging and graceful fallback to ensure robustness.

### Democratic Legitimacy
Uses the Schulze voting method for mathematical fairness:
- **Condorcet-compliant**: Picks the option that would win against all others
- **Clone-independent**: Adding similar options doesn't spoil results
- **Strategically robust**: Resistant to tactical voting

### Ethical Boundaries
Currently limited to **"Questions and Opinions, not Proposals and Decisions."** The system helps groups understand each other and find common ground, but final decisions remain with humans.

## Technical Details

### Architecture
- **Language**: Python 3.8+
- **GUI**: CustomTkinter
- **LLM Integration**: Ollama API (local inference)
- **Voting**: Schulze method implementation
- **Embeddings**: Optional Ollama integration for semantic similarity

### Project Structure
```
Recursive-Habermas-Machine/
├── main.py                      # Entry point
├── habermas_machine_app.py      # Main application (GUI + logic)
├── habermas_machine/            # Package structure
│   ├── core/                    # Consensus algorithms, voting, prompts
│   ├── utils/                   # LLM client, embeddings, utilities
│   └── data/                    # Sample data and questions
├── docs/                        # Research papers and references
├── QUICKSTART.md               # Detailed usage guide
├── CLAUDE.md                   # Developer documentation
└── TECHNICAL_DOCS.md           # Full code walkthrough
```

### Model Compatibility
Tested primarily with `deepseek-r1:14b`, but designed to work with any Ollama model. The system handles model-specific quirks (e.g., stripping DeepSeek's `<think>...</think>` tags).

## Development Context

This project was created as a portfolio demonstration following experience in organizational systems and stakeholder management at scale. It represents:

- Translation of academic research into working software
- Original extensions (Chorus) addressing real organizational challenges
- Full-stack capability: algorithms → UI → API integration
- Thoughtful consideration of governance, ethics, and democratic theory

## Research Background

Based on Google DeepMind's 2024 paper ["Finding Consensus with AI"](https://www.science.org/doi/10.1126/science.adq2852) published in *Science*.

**Key Insight:** AI can help groups find common ground not by replacing human judgment, but by efficiently synthesizing perspectives and identifying statements with broad support.

Named after philosopher Jürgen Habermas and his work on communicative rationality and democratic deliberation.

## Future Directions

### Potential Extensions
- **Multi-option decisions**: Beyond binary to "How should we fund X?" with ranges
- **Policy parameter setting**: Find acceptable ranges (e.g., "What should minimum wage be?")
- **Constitutional conventions**: Help groups write founding documents
- **Budget allocation**: Community deliberation on spending priorities

### Research Questions
- How do results vary with different voting strategies in recursive mode?
- Can embedding-based clustering improve group division?
- How to detect and mitigate bias in candidate generation?
- What's the minimal viable value statement for useful predictions?

### Production Considerations
- Cryptographic signing of statements for auditability
- Distributed processing for scale
- A/B testing of synthesis approaches
- Long-term tracking of consensus stability

## Contributing

This is currently a personal portfolio project. If you're interested in collaborating or have ideas for extensions, feel free to open an issue or reach out.

## License

See [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google DeepMind for the original research
- Jürgen Habermas for foundational work on deliberative democracy
- The Ollama team for excellent local LLM infrastructure
- CustomTkinter for the modern Python GUI framework

---

**Note:** This system is designed for research, demonstration, and internal organizational use. It is not intended for production deployment in high-stakes decision-making without additional safety measures, testing, and human oversight.
