# Habermas Machine Project

## Project Overview

### Core Purpose
Implementation and extension of Google DeepMind's "Habermas Machine" research—an AI-assisted consensus-building system that uses LLMs to help diverse groups find common ground on contentious questions through simulated deliberation and voting.

**Two Main Components:**
1. **Habermas Machine** (Core): Synthesizes individual opinions into group consensus statements through iterative generation, prediction, and simulated elections
2. **Habermas Chorus** (Original Extension): Simulates stakeholder feedback on proposals based on value statements—addressing organizational "survey fatigue" by maintaining a repository of employee perspectives that can be queried repeatedly without re-surveying

### Problems Being Explored

**Primary Questions:**
- How to make democratic deliberation scale beyond small groups
- How to gather representative feedback without survey fatigue
- What happens when LLMs are deployed at scale (hundreds/thousands of autonomous queries) rather than chatbot interactions
- Which hidden assumptions about governance ("consensus doesn't scale") can be challenged with AI augmentation

**Conceptual Framework:**
Not creating AI copies of people, but providing "robot lobbyists"—transparent agents that represent users based on explicitly written briefings. Users maintain full control and visibility into how their perspectives are represented.

### Development Stage
**Working prototype** with functional GUI interface, ready for demonstration and internal pitch. Created during/after transition from Foundever position, demonstrating self-directed portfolio work and strategic positioning at the intersection of AI, product design, and organizational systems.

---

## Technical Architecture

### Core Technologies
- **Python 3.x** with tkinter/customtkinter for GUI
- **Local LLM Integration**: Connects to Ollama API (localhost:11434)
  - Tested primarily with `deepseek-r1:14b`
  - Handles model-specific quirks (e.g., stripping `<think>...</think>` tags from DeepSeek responses)
- **Voting Theory**: Schulze method for elections (Condorcet-compliant, clone-independent, strategically robust)
- **Vector Embeddings**: Optional Ollama integration for semantic similarity in verbatim quote selection

### Key Components

**habermas_machine.py** (Primary Implementation)
```
HabermasMachine Class
├── UI Management (customtkinter)
│   ├── Left Column: Inputs, Settings, Templates
│   ├── Middle Column: Results (Friendly, Detailed, Chorus)
│   └── Right Column: Debug (Prompts, Responses)
├── Consensus Engine
│   ├── Single-run consensus (≤12 participants)
│   ├── Recursive consensus (>12 participants, hierarchical)
│   ├── Candidate generation (shuffled, multiple samples)
│   └── Schulze election simulation
├── Ranking Prediction
│   ├── JSON-formatted responses
│   ├── Multi-retry with fallback
│   └── Temperature-based sampling
└── State Management
    ├── Session tracking
    ├── Stop event handling
    └── Auto-save functionality
```

**File Structure (Unified Design)**
- `habermas_machine.py`: Main application with all functionality
- `habermas_machine.log`: Runtime logging
- Output files: `habermas_results_[timestamp].md`, `habermas_detailed_[timestamp].md`

### Algorithmic Details

**1. Candidate Generation**
- Generate N candidates (default 4, max 9)
- Each candidate uses randomly shuffled participant statements to avoid bias
- Uses customizable prompt template with placeholders: `{question}`, `{participant_statements}`

**2. Ranking Prediction (JSON-Based)**
- System prompt instructs model to output JSON: `{"ranking": [1,2,3,4]}`
- Up to M retries (default 3) with regex extraction and JSON parsing
- Falls back to random ranking on failure (logged extensively)
- Lower temperature (default 0.2) for more deterministic predictions

**3. Schulze Method**
```
1. Build pairwise preference matrix from individual rankings
2. Calculate strongest paths using Floyd-Warshall algorithm
3. Determine winner: candidate i wins if ∀j≠i, strongest_path[i][j] ≥ strongest_path[j][i]
```

**4. Recursive Consensus**
- Divide large groups into subgroups (max size configurable, default 12)
- Find consensus within each subgroup
- Treat subgroup consensuses as new "participant statements"
- Recurse until single consensus emerges
- Two voting strategies: "own_groups_only" vs "all_elections"

---

## Key Design Decisions

### 1. Transparency Over Optimization
**Decision:** Users see exact prompts, responses, and voting matrices
**Rationale:** "Robot lobbyist" metaphor requires full visibility—users should understand and be able to "game" the system because that's strategic representation, not manipulation
**Implementation:** Dedicated debug panels show current prompts/responses in real-time

### 2. Iterative Reliability Handling
**Decision:** Multi-retry JSON parsing with fallback to random rankings
**Rationale:** LLM JSON output is unreliable; better to log failures and fall back gracefully than crash
**Implementation:** 
- Regex extraction of JSON objects from verbose responses
- `ast.literal_eval` fallback if `json.loads` fails
- Comprehensive logging of all attempts
**Example from code:**
```python
# Try to extract JSON from the response
match = re.search(r'({[\s\S]*?})', clean_response)
if match:
    json_str = match.group(1)
    ranking_data = json.loads(json_str)
```

### 3. Model-Specific Compatibility
**Decision:** Strip DeepSeek-R1 `<think>...</think>` tags explicitly
**Rationale:** Shows awareness that different models have different output formats
**Implementation:**
```python
clean_response = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL).strip()
```

### 4. Schulze Over Simpler Methods
**Decision:** Use Schulze method despite added complexity
**Rationale:** Need Condorcet compliance, clone independence, and strategic voting resistance for mathematical fairness
**Why Not Plurality:** Vulnerable to vote splitting
**Why Not IRV:** Not Condorcet-compliant, clone-dependent
**Why Not Borda:** Vulnerable to strategic voting

### 5. Separation of Concerns: Questions vs Proposals
**Decision:** Habermas Machine handles abstract questions; Chorus handles specific proposals
**Rationale:** Different use cases require different outputs—consensus statements vs simulated feedback
**Note:** System intentionally limited to "Questions and Opinions, not Proposals and Decisions" until certain AI safety problems are solved

---

## Habermas Chorus Extension

### Purpose
Address organizational survey fatigue by maintaining a persistent repository of employee "value statements" that can be queried repeatedly to simulate feedback on new proposals without re-surveying.

### Architecture
```
Chorus Workflow
├── Value Statement Repository
│   ├── Employee statements (persistent, user-controlled)
│   ├── Metadata: department, role, location
│   ├── CRUD operations with filtering
│   └── Bulk import from files
├── Proposal Evaluation
│   ├── Submit proposal text
│   ├── Filter stakeholders by metadata
│   ├── Generate simulated feedback per stakeholder
│   └── JSON responses: sentiment, concerns, suggestions, importance
├── Aggregation & Analysis
│   ├── Approval percentages by category
│   ├── Top themes and concerns
│   ├── Representative verbatim quotes
│   └── Visualizations (charts, graphs)
└── Intelligent Sampling
    ├── Vector embeddings for semantic matching
    ├── Hungarian-inspired diversity balancing
    └── Show 3 distinct verbatims per concern
```

### Key Features

**1. Value Statement Repository**
- Associates control their own statements completely
- Can update, remove, or replace at any time
- Linked to metadata for filtering (department, role, location)
- Statements are persistent—reusable across multiple proposals

**2. Simulated Feedback Generation**
- Each statement processed individually with LLM
- Prompt: "Given this associate's values, how would they respond to this proposal?"
- JSON output structure:
  ```json
  {
    "sentiment": "favorable|neutral|unfavorable",
    "concerns": ["concern1", "concern2"],
    "suggestions": ["suggestion1", "suggestion2"],
    "importance_score": 1-10
  }
  ```

**3. Intelligent Verbatim Sampling**
- **Problem:** Same quotes appearing repeatedly across different concerns
- **Solution:** VerbalSamplingManager class
  - Uses vector embeddings to measure relevance to keywords
  - Balances relevance with diversity (Hungarian algorithm-inspired)
  - Shows 3 distinct quotes per concern
  - Prevents over-representation of any single voice

**4. Aggregated Analytics**
- Approval percentages (favorable/neutral/unfavorable)
- Top themes by frequency
- Department/role/location breakdowns
- Visual charts (sentiment pie chart, department stacked bars)
- Key insights and recommendations

**5. Dynamic Filtering**
- Filter dropdowns auto-populate based on actual metadata in repository
- Can target specific subgroups: "How would Product team respond?"
- Supports "All Departments", "All Roles", "All Locations" options

### Differentiators from Base Habermas Machine
| Aspect | Habermas Machine | Habermas Chorus |
|--------|------------------|-----------------|
| **Input** | Individual opinions on abstract question | Persistent value statements |
| **Process** | Find consensus statement | Simulate individual feedback |
| **Output** | Single group statement | Aggregated feedback analytics |
| **Voting** | Schulze election | No voting (individual responses) |
| **Persistence** | Session-based | Repository-based |
| **Use Case** | Policy formation | Proposal evaluation |

---

## Development Patterns & Problem-Solving

### "Babble and Prune" Philosophy
Explicitly applies this creative pattern:
1. **Expand:** Generate multiple candidates, explore possibilities, gather diverse inputs
2. **Constrain:** Vote, filter, rank, select—ruthlessly prune to actionable decisions
3. **Recurse:** Apply pattern at multiple scales (tasks→phases→projects)

**Example:** Recursive consensus divides large groups, builds consensus in each, then merges—mirroring how real project management works with gradual refinement and periodic pruning.

### The "Excel Moment" Analogy
> "Just as Excel revealed the power of structured data manipulation, the Habermas Machine reveals the power of structured opinion synthesis. You're not just writing text; you're engineering representation."

**Implication:** Moving from chatbot paradigm (one-off generations) to spreadsheet paradigm (systematic, reusable, composable operations on structured inputs)

### Practical Development Approach

**Preference for Concrete Chunks:**
> "Always provide easy-to-paste chunks such as whole functions or whole files with 'fold headers' so that it is easy to identify where it goes and it is at the correct indent level"

**Avoiding Ambiguity:**
- No placeholders like `# your code here` or `# this section remains the same`
- Complete, paste-ready code sections
- Individual scripts stay under 1000 lines for maintainability

**Progressive Disclosure:**
- Main UI uses tabs to separate concerns
- Results split into "Friendly Output" (for users) and "Detailed Records" (for analysis)
- Debug panel separate from main workflow

---

## Technical Challenges & Solutions

### 1. JSON Parsing Unreliability
**Problem:** LLMs frequently produce malformed JSON or wrap JSON in explanatory text
**Solution:**
- Multi-retry loop (configurable, default 3 attempts)
- Regex extraction: `re.search(r'({[\s\S]*?})', response)`
- `ast.literal_eval` fallback
- Comprehensive logging of all parsing attempts
- Graceful degradation to random ranking with explicit logging

### 2. Response Streaming and UI Updates
**Problem:** Long LLM responses need to display progressively without blocking UI
**Solution:**
- Thread-based generation with `Event()` for stop signaling
- Stream responses token-by-token using `response.iter_lines()`
- `root.after(0, lambda: ...)` for thread-safe UI updates
- Visual feedback: textbox "flashing" (color change) on updates

### 3. Verbatim Quote Repetition
**Problem:** Same quotes appearing for multiple concerns/suggestions
**Solution:** VerbalSamplingManager
```python
class VerbalSamplingManager:
    def select_diverse_samples(self, concern, all_responses, embeddings, k=3):
        # 1. Compute relevance scores using semantic similarity
        # 2. Balance relevance with diversity (penalize already-shown quotes)
        # 3. Return top k distinct samples
```
- Vector embeddings for semantic matching (via Ollama)
- Diversity penalty for already-selected quotes
- Result: 3 distinct, relevant quotes per concern

### 4. Handling Model-Specific Behaviors
**DeepSeek-R1 Example:**
- Model adds `<think>...</think>` reasoning tags
- Solution: Strip explicitly before processing
  ```python
  clean_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
  ```
- Shows awareness: different models need different handling

### 5. Dynamic UI State Management
**Problem:** Filter options should reflect actual data in repository
**Solution:**
- `update_filter_dropdowns()` called whenever repository changes
- Extract unique departments, roles, locations from current data
- Update dropdown values dynamically
- Reset to "All" if current selection invalid

---

## Example Workflows

### Single-Run Consensus (Small Group)
```
1. User enters question: "Should voting be compulsory?"
2. User provides 5 participant statements (sample data included)
3. Click "Generate Consensus (Single Run)"
4. System:
   a. Generates 4 candidate consensus statements
   b. Predicts how each participant ranks candidates
   c. Runs Schulze election
   d. Displays winner at top of "Friendly Output"
   e. Provides detailed matrices in "Detailed Records"
5. Auto-saves results to timestamped files
```

### Recursive Consensus (Large Group)
```
1. User enters question + 20+ participant statements
2. Click "Recursive Consensus Builder"
3. System:
   a. Divides into groups of ≤12 (configurable)
   b. Finds consensus within each group
   c. Treats group consensuses as new "participants"
   d. Recurses: groups → meta-groups → final consensus
   e. Logs full tree structure in detailed output
4. Final consensus statement represents all 20+ voices
```

### Chorus Proposal Evaluation
```
1. User manages value statement repository (Chorus tab)
   - Add sample statements or bulk import
   - Associate metadata (dept, role, location)
2. User enters proposal text and applies filters
3. Click "Generate Feedback"
4. System:
   a. Queries filtered subset of repository
   b. Generates JSON feedback per statement
   c. Aggregates results
   d. Selects diverse verbatim quotes
   e. Renders charts and analytics
5. User reviews:
   - Approval percentages
   - Top concerns/suggestions
   - Department breakdowns
   - Representative quotes
```

---

## Project Context & Significance

### Post-Foundever Transition
- **Background:** Recently separated from position as Project Architect for US & Canada region at Foundever
- **Timing:** Project represents self-directed portfolio work during transition
- **Strategic Value:**
  - Demonstrates initiative and technical capability
  - Shows ability to translate organizational experience into novel solutions
  - Positions at intersection of AI, product design, and organizational systems
  - Habermas Chorus specifically targets Foundever-type challenges (survey fatigue, stakeholder management at scale)

### Demonstrable Skills
1. **Full-stack capability:** Algorithms → UI → API integration
2. **Original thinking:** Not just implementing research but extending meaningfully
3. **Systems-level understanding:** Governance theory, voting methods, organizational dynamics
4. **AI/LLM expertise:** Prompt engineering, model integration, reliability handling
5. **Product sensibility:** User needs, workflow design, progressive disclosure
6. **Ethical awareness:** Transparency, user control, clear boundaries
7. **Communication:** Complex ideas made accessible, thoughtful framing
8. **Self-direction:** Substantial independent project completed during transition

### Transferable Insights from Foundever Experience
- Deep understanding of large organization dynamics
- Experience with stakeholder management at scale
- Practical knowledge of survey/feedback challenges
- Context for "urgency and seriousness" driving production-quality standards

---

## Future Directions

### Research Questions
- How do results change with different voting strategies in recursive mode?
- Can embedding-based clustering improve group division in recursive consensus?
- How to detect and mitigate bias in candidate generation?
- What's the minimal viable value statement for useful Chorus predictions?

### Potential Extensions
**Multi-Option Decisions:**
- Beyond binary yes/no to "How should we fund X?" with multiple options
- Find ranges/combinations that satisfy diverse groups

**Policy Parameter Setting:**
- "What should minimum wage be?" → find acceptable ranges
- Reveal "zone of possible agreement"

**Constitutional Conventions:**
- Help groups write founding documents/bylaws
- Synthesize governance philosophies

**Budget Allocation:**
- Community deliberation on spending priorities
- Find acceptable compromises on resource distribution

### Production Considerations
**Security:**
- Cryptographic signing of statements
- Audit trails for robot behavior
- Sandboxing to prevent adversarial statements

**Scalability:**
- Distributed processing for thousands of simultaneous deliberations
- Efficient caching of common interpretations
- Hierarchical consensus for very large groups

**UX Enhancements:**
- Interactive tutorials for writing effective statements
- Visualization of voting patterns and paths
- Natural language explanations of compromises

**Evaluation:**
- A/B testing synthesis approaches
- Feedback mechanisms for outcome quality
- Long-term tracking of consensus stability

---

## Usage Instructions

### Setup
```bash
# Install dependencies
pip install customtkinter requests numpy matplotlib pillow

# Ensure Ollama is running locally
# Default: http://localhost:11434

# Run the application
python habermas_machine.py
```

### Quick Start (Habermas Machine)
1. **Inputs Tab:**
   - Question pre-filled: "Should voting be compulsory?"
   - Sample participant statements already loaded
   - Or use "Bulk Import" for custom data

2. **Settings Tab:**
   - Default model: `deepseek-r1:14b`
   - Adjust generation/ranking temperatures
   - Configure recursive parameters

3. **Templates Tab:**
   - Customize prompt templates if needed
   - Use placeholders: `{question}`, `{participant_statements}`, etc.

4. **Generate:**
   - "Single Run" for ≤12 participants
   - "Recursive" for larger groups
   - Watch progress in "Friendly Output"
   - Inspect details in "Detailed Records"

5. **Debug:**
   - Right column shows real-time prompts/responses
   - Helpful for understanding model behavior

### Quick Start (Habermas Chorus)
1. **Chorus Tab → Repository:**
   - "Add Sample Value Statements" for demo
   - Or add custom statements with metadata

2. **Proposal:**
   - Enter proposal title and text
   - Apply demographic filters if desired

3. **Generate Feedback:**
   - System simulates responses from filtered group
   - View aggregated results in "Chorus Results" tab

4. **Analyze:**
   - Check sentiment distribution
   - Review top concerns/suggestions
   - Examine department breakdowns
   - Read representative verbatim quotes

---

## Key Files & Outputs

### Project Files
- `habermas_machine.py`: Main application (unified implementation)
- `habermas_machine.log`: Runtime log with detailed API interactions
- `Habermas Machine — LessWrong.md`: Reference documentation of original research
- `Problem of Governance`: Conversation about governance theory and hidden assumptions

### Generated Outputs
- `habermas_results_[timestamp].md`: User-friendly consensus results
- `habermas_detailed_[timestamp].md`: Complete process record with matrices
- `habermas_recursive_results_[timestamp].md`: Recursive consensus results
- `habermas_recursive_detailed_[timestamp].md`: Detailed recursive process log

### Sample Data
Pre-loaded example on compulsory voting:
```
Participant 1: Against (personal choice, informed voting)
Participant 2: For (civic duty, representation)
Participant 3: Against (address root causes instead)
Participant 4: Fence-sitting (sees both sides)
Participant 5: For (ensures participation, reduces polarization)
```

---

## Communication Style & Preferences

### "Literary Brain" Mode
For brainstorming/discussion (not final products):
- Use most-correct form of every term
- Efficient, no fluff
- Disambiguate with joining syntax:
  - `{word|word|word}` = inner join (intersection of meanings)
  - `}word|word|word{` = outer join (union of meanings)
- Avoid in formal artifacts or external documents

### Unicode Where Appropriate
- Prefer unicode over ASCII when more appropriate
- Examples: Superscript numbers for footnotes (¹²³), mathematical symbols, etc.
- Keep Markdown readable in plaintext: prefer headers, lists, quotes over inline formatting

### Response Expectations
- Complete, paste-ready code chunks
- Whole functions or files with clear headers
- No placeholders or "sections remain the same"
- Avoid special handling for edge cases if fundamental design is the issue

---

## Philosophical Underpinnings

### Challenging Hidden Assumptions
The project explicitly questions conventional wisdom about governance scaling:

**"Consensus doesn't scale" — Hidden Assumptions:**
- Fixed communication bandwidth
- Opinion rigidity
- Linear time complexity
- No technological augmentation
- Binary outcomes (all-or-nothing agreement)

**Habermas Machine Challenges:**
- AI can synthesize viewpoints efficiently (sub-linear scaling)
- People do change positions when presented with synthesis
- Recursive structure enables hierarchical consensus
- Workable common ground ≠ unanimous agreement

### Meta-Assumptions Across Governance Systems
1. **Human cognitive limits are fixed** → Ignores AI augmentation
2. **Communication is costly** → Pre-internet/AI assumption
3. **Trust requires personal knowledge** → Ignores cryptographic verification
4. **Time uniformly valuable** → Could match urgency to importance
5. **Groups are monolithic** → Could use different modes for different decisions
6. **Path dependency is strong** → Switching costs might be lower than assumed

### Vision: Augmentation, Not Replacement
> "Most importantly, it reframes our relationship with AI. Instead of fearing replacement or manipulation, we're explicitly partnering with AI to solve coordination problems that have plagued humanity forever. We're not training the AI on ourselves—we're training ourselves to better instruct AI."

**Key Principle:** AI as tool for improving human coordination, not as decision-maker
- Humans define values and constraints
- AI handles computational complexity
- Humans validate and refine results
- Full transparency enables trust and iteration

---

## Notes for Claude Code

### Development Approach
- Work in discrete, complete chunks (whole functions/files)
- Prefer modular files <1000 lines each
- Use clear "fold headers" for easy navigation
- Avoid fragmented updates across multiple files

### Testing & Debugging
- Ollama connection required for full functionality
- Can run without Ollama but features limited
- Check logs for API interaction details
- Debug panel in UI shows real-time prompt/response

### Extension Points
- Easily customizable prompt templates
- Pluggable voting methods (currently Schulze)
- Swappable LLM backends (currently Ollama)
- Additional metadata fields for Chorus filtering

### Known Limitations
- Local LLM only (no cloud API support)
- Single-threaded generation (no parallel processing)
- No persistence between app sessions (except exported files)
- Limited to text-based inputs (no images, audio)

---

## Credits & References

### Original Research
- **Paper:** "Finding Consensus with AI" (Google DeepMind, Science, 2024)
- **Link:** https://www.science.org/doi/10.1126/science.adq2852
- **Named After:** Jürgen Habermas (philosopher, communicative rationality theory)

### This Implementation
- **Author:** [User's name not specified in project]
- **Context:** Independent project following Foundever separation
- **Purpose:** Portfolio demonstration, internal pitch preparation
- **Originality:** Chorus extension, recursive implementation details, specific UX patterns

### Intellectual Property Notes
- Core concept: Google DeepMind (published research)
- Implementation: Original work
- Chorus extension: Original concept and implementation
- Code: Available for demonstration and pitch purposes
