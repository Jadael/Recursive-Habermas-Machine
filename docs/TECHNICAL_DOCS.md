# Habermas Machine: AI-Assisted Consensus Builder Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Conceptual Overview](#conceptual-overview)
3. [System Architecture](#system-architecture)
4. [Installation and Setup](#installation-and-setup)
5. [User Interface](#user-interface)
6. [Core Components](#core-components)
7. [Consensus Building Algorithms](#consensus-building-algorithms)
8. [Advanced Features](#advanced-features)
9. [Full Code Walkthrough](#full-code-walkthrough)
10. [Troubleshooting](#troubleshooting)

<a id="introduction"></a>
## 1. Introduction

The Habermas Machine is an AI-assisted tool designed to find consensus among people with differing opinions. Named after philosopher Jürgen Habermas, it uses large language models to synthesize diverse perspectives into coherent group statements that represent fair compromises most participants can accept.

This implementation is based on research from Google DeepMind that demonstrated how AI can help mediate group discussions and build consensus. The system takes individual opinion statements from different participants, generates candidate consensus positions, and uses simulated elections to identify statements with broad support.

<a id="conceptual-overview"></a>
## 2. Conceptual Overview

### 2.1 Purpose

The primary purpose of the Habermas Machine is to:

- Find common ground among divergent opinions
- Generate synthesized statements that fairly represent multiple perspectives
- Help groups converge toward consensus through an iterative process
- Provide a structured approach to deliberation in potentially contentious topics

### 2.2 Core Process Flow

The Habermas Machine follows a structured process:

1. **Question Definition**: A binary or open-ended question is posed
2. **Opinion Collection**: Participants provide their individual opinions
3. **Candidate Generation**: The AI generates multiple potential consensus statements
4. **Preference Prediction**: The system predicts how each participant would rank the candidate statements
5. **Election Simulation**: Using the Schulze voting method, the system identifies the most broadly acceptable statement
6. **Consensus Presentation**: The winning statement is presented as the group consensus

### 2.3 Key Features

- **Single-Run Consensus**: Process a set of opinions once to find a common position
- **Recursive Consensus**: Break large groups into smaller circles that find consensus, then merge these positions
- **Schulze Voting Method**: Uses a sophisticated voting algorithm that finds broadly acceptable options
- **Detailed Documentation**: Provides transparency into how consensus was reached
- **Customizable Parameters**: Allows fine-tuning of the AI's behavior

<a id="system-architecture"></a>
## 3. System Architecture

### 3.1 High-Level Design

The Habermas Machine consists of the following main components:

- **User Interface**: Built with CustomTkinter for a modern, responsive design
- **AI Integration**: Connects to Ollama API for language model inference
- **Consensus Engine**: Core algorithms for statement generation and ranking
- **Election Simulator**: Implements the Schulze voting method
- **Output Generator**: Creates human-readable reports of the consensus process

### 3.2 Dependencies

```python
# Core dependencies
import customtkinter as ctk
import tkinter as tk
import json
import requests
from threading import Thread, Event
import time
import random
import re
from collections import defaultdict
import math
import datetime
```

### 3.3 Integration with Ollama

The system uses the Ollama API for language model inference. Ollama is a local inference server that runs language models on your device. The Habermas Machine connects to Ollama to:

1. Generate candidate consensus statements
2. Predict participant preferences for ranking

The application requires Ollama to be running locally with access to models like DeepSeek-R1 or similar models capable of complex reasoning and synthesis tasks.

<a id="installation-and-setup"></a>
## 4. Installation and Setup

### 4.1 Prerequisites

- Python 3.8 or higher
- Ollama installed and running locally
- Required Python packages:
  - customtkinter
  - requests
  - tkinter (usually included with Python)

### 4.2 Installation Steps

1. Install required packages:
   ```bash
   pip install customtkinter requests
   ```

2. Install and set up Ollama following the instructions at https://ollama.com/download

3. Pull a suitable language model:
   ```bash
   ollama pull deepseek-r1:14b
   ```

4. Clone or download the Habermas Machine code

5. Run the application:
   ```bash
   python habermas_machine.py
   ```

<a id="user-interface"></a>
## 5. User Interface

The Habermas Machine features a three-column interface designed for clarity and usability:

### 5.1 Left Column: Inputs and Settings

The left column contains tabs for:

1. **Inputs**: Where you define the question and participant statements
2. **Settings**: Configure model parameters, consensus options, and output preferences
3. **Templates**: Edit prompt templates used for generation and ranking

### 5.2 Middle Column: Results

The middle column displays:

1. **Friendly Output**: A human-readable summary of the consensus process
2. **Detailed Records**: A comprehensive log of all steps in the process

### 5.3 Right Column: Debug Information

The right column shows:

1. **Current Prompt**: The prompt being sent to the language model
2. **Current Response**: The raw output from the language model

### 5.4 UI Components

```python
def create_layout(self):
    # Configure grid layout with 3 columns
    self.root.grid_columnconfigure(0, weight=1)  # Left: Settings & Inputs
    self.root.grid_columnconfigure(1, weight=3)  # Middle: Results - giving more space
    self.root.grid_columnconfigure(2, weight=2)  # Right: Debug
    self.root.grid_rowconfigure(0, weight=1)
    
    # Create main frames
    self.left_column = ctk.CTkFrame(self.root)
    self.middle_column = ctk.CTkFrame(self.root)
    self.right_column = ctk.CTkFrame(self.root)
    
    self.left_column.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    self.middle_column.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    self.right_column.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
    
    # Set up the individual columns
    self.setup_left_column()
    self.setup_middle_column()
    self.setup_right_column()
```

<a id="core-components"></a>
## 6. Core Components

### 6.1 Participant Statement Management

The system allows input of multiple participant statements, each representing an individual opinion on the question:

```python
def get_participant_statements(self):
    """Extract participant statements from the textbox"""
    text = self.participants_text.get("1.0", "end-1c")
    statements = [line.strip() for line in text.split('\n') if line.strip()]
    return statements

def update_participant_count(self, event=None):
    """Update the participant count label based on the number of non-empty lines"""
    text = self.participants_text.get("1.0", "end-1c")
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    self.participant_count_label.configure(text=f"Count: {len(lines)}")
```

### 6.2 Candidate Statement Generation

The system generates candidate consensus statements by prompting the language model with the question and shuffled participant statements:

```python
def generate_single_candidate(self, question, statements, candidate_num):
    """Generate a single candidate consensus statement"""
    # Prepare participant statements text
    participant_statements_text = ""
    for i, statement in enumerate(statements):
        participant_statements_text += f"Participant {i+1}: {statement}\n\n"
    
    # Get the template and format it
    template = self.prompt_templates["candidate_generation"]
    prompt = template.format(
        question=question,
        participant_statements=participant_statements_text
    )
    
    # Log the prompt to detailed output
    self.log_to_detailed(f"**Prompt for Candidate {candidate_num}:**\n\n```\n{prompt}\n```\n\n")
    
    # Update the debug prompt display
    self.root.after(0, lambda: self.update_debug_prompt(prompt))
    
    # Make the API call to Ollama
    try:
        self.current_response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": self.model_var.get(),
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": float(self.temperature_var.get()),
                    "top_p": float(self.top_p_var.get()),
                    "top_k": int(self.top_k_var.get())
                }
            },
            stream=True
        )
        
        # Process the streamed response
        full_response = ""
        for line in self.current_response.iter_lines():
            if self.stop_event.is_set():
                break
                
            if line:
                try:
                    data = json.loads(line)
                    if 'response' in data:
                        response_text = data['response']
                        full_response += response_text
                        self.root.after(0, lambda r=full_response: self.update_debug_response(r))
                except json.JSONDecodeError:
                    self.log_to_detailed("**Error:** Failed to decode response from Ollama API\n\n")
        
        # Clean up the response
        clean_response = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL).strip()
        return clean_response
        
    except Exception as e:
        self.log_to_detailed(f"**Error generating candidate {candidate_num}:** {str(e)}\n\n")
        return None
```

### 6.3 Preference Prediction

The system predicts how each participant would rank the candidate statements:

```python
def predict_participant_ranking_json(self, question, participant_statement, candidate_statements, participant_num):
    """Predict a participant's ranking with JSON format output and retries"""
    # Get max retries from settings
    try:
        max_retries = int(self.max_retries_var.get())
    except ValueError:
        max_retries = 3
    
    # Create a system prompt for JSON output
    system_prompt = self.create_ranking_system_prompt(len(candidate_statements))
    
    # Prepare candidate statements text
    candidate_statements_text = ""
    for i, statement in enumerate(candidate_statements):
        candidate_statements_text += f"Statement {i+1}:\n{statement}\n\n"
    
    # Get the template and format it
    template = self.prompt_templates["ranking_prediction"] 
    prompt = template.format(
        question=question,
        participant_num=participant_num,
        participant_statement=participant_statement,
        num_candidates=len(candidate_statements),
        candidate_statements=candidate_statements_text
    )
    
    # Make API calls with retries
    attempts = 0
    attempts_log = []
    
    while attempts < max_retries:
        attempts += 1
        
        # Try to get ranking prediction from the model
        try:
            response = self.call_ranking_api(prompt, system_prompt)
            
            # Try to extract ranking from JSON response
            try:
                match = re.search(r'({[\s\S]*?})', response)
                if match:
                    json_str = match.group(1)
                    ranking_data = json.loads(json_str)
                    
                    if "ranking" in ranking_data and isinstance(ranking_data["ranking"], list):
                        # Convert 1-indexed to 0-indexed
                        ranking = [num - 1 for num in ranking_data["ranking"]]
                        
                        # Validate ranking has correct indices
                        if self.validate_ranking(ranking, len(candidate_statements)):
                            return ranking, attempts_log
            except Exception as e:
                attempts_log.append(f"Attempt {attempts}: Error: {str(e)}")
                
        except Exception as e:
            attempts_log.append(f"Attempt {attempts}: API error: {str(e)}")
    
    # Fallback to random ranking if all attempts fail
    random_ranking = list(range(len(candidate_statements)))
    random.shuffle(random_ranking)
    return random_ranking, attempts_log
```

### 6.4 Schulze Voting Method

The system uses the Schulze voting method to determine the winning statement:

```python
def schulze_method(self, rankings, num_candidates):
    """
    Implementation of the Schulze voting method
    
    Args:
        rankings: Dictionary where keys are participant indexes and values are lists of candidate indexes
                 in order of preference (most preferred first)
        num_candidates: Number of candidates

    Returns:
        winner_idx: Index of the winning candidate
        pairwise_matrix: Matrix of pairwise preferences
        strongest_paths: Matrix of strongest path strengths
    """
    # Step 1: Initialize the pairwise preference matrix
    pairwise_matrix = [[0 for _ in range(num_candidates)] for _ in range(num_candidates)]
    
    # Step 2: For each voter, count pairwise preferences
    for p_idx, ranking in rankings.items():
        # For each pair of candidates in the voter's ranking
        for i in range(len(ranking)):
            for j in range(i + 1, len(ranking)):
                # The candidate at ranking[i] is preferred over the candidate at ranking[j]
                preferred = ranking[i]
                not_preferred = ranking[j]
                pairwise_matrix[preferred][not_preferred] += 1
    
    # Step 3: Find the strongest paths (Floyd-Warshall algorithm)
    strongest_paths = [[0 for _ in range(num_candidates)] for _ in range(num_candidates)]
    
    # Initialize with direct pairwise preferences
    for i in range(num_candidates):
        for j in range(num_candidates):
            if i != j:
                strongest_paths[i][j] = pairwise_matrix[i][j]
    
    # Calculate strongest paths
    for i in range(num_candidates):
        for j in range(num_candidates):
            if i != j:
                for k in range(num_candidates):
                    if i != k and j != k:
                        strongest_paths[j][k] = max(
                            strongest_paths[j][k],
                            min(strongest_paths[j][i], strongest_paths[i][k])
                        )
    
    # Step 4: Determine the winner
    potential_winners = set(range(num_candidates))
    
    for i in range(num_candidates):
        for j in range(num_candidates):
            if i != j and strongest_paths[j][i] > strongest_paths[i][j]:
                if i in potential_winners:
                    potential_winners.remove(i)
    
    # Return the winner with the lowest index (if there are multiple winners)
    winner_idx = min(potential_winners) if potential_winners else 0
    
    return winner_idx, pairwise_matrix, strongest_paths
```

<a id="consensus-building-algorithms"></a>
## 7. Consensus Building Algorithms

### 7.1 Single-Run Consensus

The single-run consensus process follows these steps:

1. Collect participant statements
2. Generate multiple candidate consensus statements
3. Predict how each participant would rank the candidates
4. Run a Schulze election to determine the winning statement
5. Present the winning statement as the group consensus

```python
def run_single_consensus(self):
    """Run a single consensus generation process"""
    try:
        question = self.question_text.get("1.0", "end-1c").strip()
        
        # Initial log entries
        self.log_to_friendly(f"# Consensus Builder Results\n\n")
        self.log_to_friendly(f"**Question:** {question}\n\n")
        self.log_to_friendly("## Original Participant Statements\n\n")
        
        # Log participant statements
        for i, statement in enumerate(self.participant_statements):
            self.log_to_friendly(f"**Participant {i+1}:**  \n{statement}\n\n")
        
        # Generate candidate statements
        self.log_to_friendly("## Generating Candidate Statements...\n\n")
        self.candidate_statements = self.generate_candidate_statements(question)
        
        if not self.candidate_statements:
            self.log_to_friendly("**Error:** Failed to generate candidate statements.\n\n")
            return
        
        # Display the candidates
        self.log_to_friendly("### Candidate Statements\n\n")
        for i, candidate in enumerate(self.candidate_statements):
            self.log_to_friendly(f"**Candidate {i+1}:**  \n{candidate}\n\n")
        
        # Run election simulation
        self.log_to_friendly("## Simulating Election...\n\n")
        winner_idx, rankings, pairwise_matrix, strongest_paths = self.run_election_simulation(question)
        
        if winner_idx is None:
            return
        
        # Get winning statement
        winning_statement = self.candidate_statements[winner_idx]
        
        # Display the winning statement at the top for visibility
        self.root.after(0, lambda: self.update_friendly_output_with_winner(winning_statement))
        
        # Log the election results
        self.log_election_results(winner_idx, rankings, pairwise_matrix, strongest_paths)
        
    except Exception as e:
        self.log_to_friendly(f"\n\n**Error:** {str(e)}\n")
    
    finally:
        self.cleanup_after_process()
```

### 7.2 Recursive Consensus Building

The recursive consensus approach is designed for larger groups:

1. Divide participants into smaller groups
2. Find consensus within each small group
3. Take the consensus statements from each group
4. Recursively apply the process until a single consensus emerges

```python
def recursive_habermas_process(self, question, process_data, max_group_size, voting_strategy):
    """
    Run the recursive consensus process
    
    Args:
        question: The question being debated
        process_data: Dict containing statements, level, and participant_mapping
        max_group_size: Maximum number of statements per group
        voting_strategy: Strategy for voting in elections
    
    Returns:
        The winning consensus statement
    """
    statements = process_data["statements"]
    level = process_data["level"]
    participant_mapping = process_data["participant_mapping"]
    
    # Log the current level
    self.log_to_friendly(f"### Level {level+1} - Processing {len(statements)} statements\n\n")
    
    # If we have few enough statements to process in one group, do it directly
    if len(statements) <= max_group_size:
        self.log_to_friendly(f"All statements fit in a single group. Processing directly...\n\n")
        
        # Get list of original participant indices for this group
        if level == 0:
            # At level 0, statements are from original participants
            original_participant_indices = list(range(len(statements)))
        else:
            # At higher levels, use the mapping
            original_participant_indices = []
            for idx in range(len(statements)):
                if idx in participant_mapping:
                    original_participant_indices.extend(participant_mapping[idx])
        
        # Process this single group
        winning_statement = self.process_single_group(
            question, 
            statements, 
            original_participant_indices,
            voting_strategy,
            level, 
            0
        )
        
        return winning_statement
        
    # Otherwise, divide into groups and process recursively
    groups = self.divide_statements_into_groups(statements, max_group_size)
    
    self.log_to_friendly(f"Dividing into {len(groups)} groups...\n\n")
    
    # Process each group to get winning statements
    winning_statements = []
    new_participant_mapping = {}  # Maps winning statement index to original participant indices
    
    for group_idx, group in enumerate(groups):
        self.log_to_friendly(f"#### Processing Group {group_idx+1} ({len(group)} statements)\n\n")
        
        # Get list of original participant indices for this group
        group_participant_indices = self.get_group_participant_indices(
            group, groups, group_idx, level, participant_mapping
        )
        
        # Process this group
        winning_statement = self.process_single_group(
            question, 
            group, 
            group_participant_indices,
            voting_strategy,
            level, 
            group_idx
        )
        
        if winning_statement:
            winning_statements.append(winning_statement)
            # Update the participant mapping
            new_idx = len(winning_statements) - 1
            new_participant_mapping[new_idx] = group_participant_indices
            
            self.log_to_friendly(f"Group {group_idx+1} consensus:\n\n{winning_statement}\n\n")
    
    # If we only got one winning statement, return it
    if len(winning_statements) == 1:
        return winning_statements[0]
        
    # Otherwise, recurse to process the winning statements
    if winning_statements:
        self.log_to_friendly(f"Moving to next level with {len(winning_statements)} group consensuses...\n\n")
        
        # Set up the next level's process data
        next_process_data = {
            "statements": winning_statements,
            "level": level + 1,
            "participant_mapping": new_participant_mapping
        }
        
        return self.recursive_habermas_process(
            question, 
            next_process_data,
            max_group_size, 
            voting_strategy
        )
    
    return None
```

<a id="advanced-features"></a>
## 8. Advanced Features

### 8.1 Prompt Templates

The system uses customizable prompt templates to guide the language model:

```python
# Default prompt templates
self.default_templates = {
    "candidate_generation": "Given the following question and participant statements, generate a single group statement that synthesizes their perspectives. This should represent a fair consensus or compromise position that most participants could accept.\n\n"
                          "---\n\nQuestion: {question}\n\n"
                          "---\n\n{participant_statements}\n\n---\n\n"
                          "Generate a thoughtful and nuanced group statement that represents a fair synthesis of these perspectives. Focus on finding common ground, acknowledge areas of disagreement or lack of information, and present a position that most participants could accept.",
    
    "ranking_prediction": "Given a participant's statement on a question, predict how they would rank different group statements from most preferred (1) to least preferred ({num_candidates}).\n\n\n\n"
                        "Question: {question}\n\n"
                        "Participant {participant_num}'s original statement: {participant_statement}\n\n"
                        "Group Statements to Rank:\n\n"
                        "{candidate_statements}\n\n\n\n"
                        """Based on the participant's original statement, predict their ranking of these group statements from most preferred to least preferred as a JSON object:\n\n{{\n  "ranking": []\n}}\n\nThe ranking should reflect which statements best align with the participant's expressed viewpoint, values, and concerns."""
}
```

### 8.2 Voting Strategies

The system supports different strategies for voting in the recursive consensus process:

```python
# Add voting strategy options in the settings tab
ctk.CTkLabel(recursive_grid, text="Voting Strategy:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=5, sticky="w")
self.voting_strategy_var = ctk.StringVar(value="own_groups_only")

strategy_frame = ctk.CTkFrame(recursive_grid)
strategy_frame.grid(row=1, column=1, columnspan=3, padx=10, pady=5, sticky="w")

own_groups_radio = ctk.CTkRadioButton(
    strategy_frame, 
    text="Own groups only", 
    variable=self.voting_strategy_var, 
    value="own_groups_only",
    font=("Arial", 12)
)
own_groups_radio.pack(anchor="w", pady=2)

all_elections_radio = ctk.CTkRadioButton(
    strategy_frame, 
    text="All participants vote in all elections", 
    variable=self.voting_strategy_var, 
    value="all_elections",
    font=("Arial", 12)
)
all_elections_radio.pack(anchor="w", pady=2)
```

These strategies determine who votes in each election:

- **Own Groups Only**: Participants only vote in their own group's elections
- **All Elections**: All participants vote in all elections across the process

### 8.3 Group Division Algorithm

When dividing statements into groups for recursive consensus, the system uses a balanced approach:

```python
def divide_statements_into_groups(self, statements, max_group_size):
    """Divide statements into groups of maximum size"""
    # Shuffle statements first to avoid manipulation
    shuffled_statements = statements.copy()
    random.shuffle(shuffled_statements)
    
    # Calculate number of groups needed
    num_statements = len(shuffled_statements)
    num_groups = math.ceil(num_statements / max_group_size)
    
    # Try to balance group sizes
    base_size = num_statements // num_groups
    remainder = num_statements % num_groups
    
    groups = []
    start_idx = 0
    
    for i in range(num_groups):
        # Groups at the beginning get an extra item if there's a remainder
        group_size = base_size + (1 if i < remainder else 0)
        end_idx = start_idx + group_size
        
        groups.append(shuffled_statements[start_idx:end_idx])
        start_idx = end_idx
        
    return groups
```

<a id="full-code-walkthrough"></a>
## 9. Full Code Walkthrough

Here's a comprehensive walkthrough of the main components of the Habermas Machine implementation:

### 9.1 Class Initialization

```python
class HabermasMachine:
    def __init__(self, root):
        self.root = root
        self.root.title("Habermas Machine - AI-Assisted Consensus Builder")
        self.root.geometry("1800x900")
        
        # Configure dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # State management
        self.stop_event = Event()
        self.current_response = None
        self.participant_statements = []
        self.candidate_statements = []
        self.election_results = {}
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Default prompt templates
        self.default_templates = {
            # Templates defined here...
        }
        
        # Create templates that will be edited
        self.prompt_templates = self.default_templates.copy()
        
        # Create main layout
        self.create_layout()
        
        # Configure default values
        self.model_var.set("deepseek-r1:14b")
        self.temperature_var.set("0.6")
        self.top_p_var.set("0.9")
        self.top_k_var.set("40")
        self.ranking_temperature_var.set("0.2")
        self.max_retries_var.set("3")
        self.max_group_size_var.set("9")
        self.num_candidates_var.set("4")
        self.question_text.insert("1.0", "Should voting be compulsory?")
        
        # Set prompt templates in the UI
        # Initialize with sample data
        self.load_sample_data()
```

### 9.2 Running an Election Simulation

The election simulation process is central to the Habermas Machine:

```python
def run_election_simulation(self, question):
    """Simulate an election between candidate statements"""
    num_participants = len(self.participant_statements)
    
    # Initialize simulated rankings
    rankings = {i: [] for i in range(num_participants)}
    ranking_attempts_log = []
    
    # For each participant, predict their rankings
    for p_idx in range(num_participants):
        if self.stop_event.is_set():
            return None, None, None, None
            
        participant_statement = self.participant_statements[p_idx]
        
        # Predict ranking for this participant with JSON format
        predicted_ranking, attempts_log = self.predict_participant_ranking_json(
            question, 
            participant_statement, 
            self.candidate_statements,
            p_idx + 1
        )
        
        ranking_attempts_log.append(attempts_log)
        
        if predicted_ranking:
            rankings[p_idx] = predicted_ranking
    
    if self.stop_event.is_set():
        return None, None, None, None
    
    # Calculate winner using the Schulze method
    winner_idx, pairwise_matrix, strongest_paths = self.schulze_method(
        rankings, 
        len(self.candidate_statements)
    )
    
    return winner_idx, rankings, pairwise_matrix, strongest_paths
```

### 9.3 Processing a Single Group

```python
def process_single_group(self, question, statements, original_participant_indices, voting_strategy, level, group_idx):
    """Process a single group of statements to find a winning statement"""
    if self.stop_event.is_set():
        return None
        
    group_label = f"Level {level+1}, Group {group_idx+1} ({len(statements)} statements)"
    
    # Generate candidate statements for this group
    candidates = []
    
    try:
        num_candidates = min(len(statements), max(2, int(self.num_candidates_var.get())))
    except ValueError:
        num_candidates = min(len(statements), 4)
        
    for i in range(num_candidates):
        if self.stop_event.is_set():
            return None
            
        # Copy and shuffle statements to avoid bias
        shuffled_statements = statements.copy()
        random.shuffle(shuffled_statements)
        
        # Generate a candidate
        candidate = self.generate_single_candidate(question, shuffled_statements, i+1)
        if candidate:
            candidates.append(candidate)
    
    if not candidates:
        return None
        
    # Determine which participants vote in this election
    voting_participants = []
    
    if voting_strategy == "own_groups_only":
        # Only original participants in this group vote
        voting_participants = [
            (i, self.participant_statements[i]) 
            for i in original_participant_indices 
            if i < len(self.participant_statements)
        ]
    else:  # "all_elections"
        # All original participants vote in all elections
        voting_participants = [
            (i, self.participant_statements[i]) 
            for i in range(len(self.participant_statements))
        ]
        
    # Run an election with these candidates and participants
    rankings = {i: [] for i in range(len(voting_participants))}
    
    # For each participant, predict their rankings
    for p_idx, (orig_idx, statement) in enumerate(voting_participants):
        if self.stop_event.is_set():
            return None
            
        # Predict ranking for this participant
        predicted_ranking, attempts_log = self.predict_participant_ranking_json(
            question, 
            statement, 
            candidates,
            orig_idx + 1  # Use original participant number for prompt
        )
        
        if predicted_ranking:
            rankings[p_idx] = predicted_ranking
    
    if self.stop_event.is_set():
        return None
        
    # Calculate winner using Schulze method
    winner_idx, pairwise_matrix, strongest_paths = self.schulze_method(rankings, len(candidates))
    
    # Return the winning statement
    return candidates[winner_idx]
```

### 9.4 Log Output and UI Updates

```python
def log_to_friendly(self, text):
    """Append text to the friendly output"""
    self.root.after(0, lambda: self._append_to_textbox(self.friendly_output, text))

def log_to_detailed(self, text):
    """Append text to the detailed output"""
    self.root.after(0, lambda: self._append_to_textbox(self.detailed_output, text))

def _append_to_textbox(self, textbox, text):
    """Helper to append text to a textbox with smooth scrolling"""
    # Flash the textbox to indicate activity
    self.flash_textbox(textbox)
    
    # Determine if the textbox is scrolled to the bottom
    current_position = textbox.yview()
    at_bottom = (current_position[1] >= 0.99)
    
    # Scroll to end before appending if we were at the bottom
    if at_bottom:
        textbox.see("end")
    
    # Append the text
    textbox.insert("end", text)
    
    # Maintain scroll position based on previous state
    if at_bottom:
        textbox.see("end")
        textbox.yview_moveto(1.0)
```

<a id="troubleshooting"></a>
## 10. Troubleshooting

### 10.1 Common Issues

1. **Missing Dependencies**
   - The application handles missing dependencies with informative error messages:
   ```python
   try:
       import customtkinter as ctk
   except ImportError:
       # Show a message box with installation instructions if customtkinter is missing
       root = tk.Tk()
       root.withdraw()
       messagebox.showerror(
           "Missing Dependency", 
           "The customtkinter package is required but not installed.\n\n"
           "Please install it using pip:\n"
           "pip install customtkinter"
       )
       sys.exit(1)
   ```

2. **Ollama Connection Issues**
   - Ensure Ollama is running locally
   - Check that the selected model is installed (`ollama list` to verify)
   - Verify Ollama is running on the default port (11434)

3. **JSON Parsing Errors**
   - The system has built-in retry mechanisms for handling JSON parsing failures:
   ```python
   # Retry mechanism for JSON parsing
   attempts = 0
   while attempts < max_retries:
       attempts += 1
       # API call and parsing logic...
       # If successful, return the ranking
   
   # Fallback to random ranking if all attempts fail
   ```

### 10.2 Logging

The application includes comprehensive logging:

```python
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='habermas_machine.log',
    filemode='w'
)
logger = logging.getLogger('habermas_machine')
```

Error handling captures and logs exceptions:

```python
except Exception as e:
    error_msg = f"Error in consensus process: {str(e)}"
    self.log_to_friendly(f"\n\n**Error:** {error_msg}\n")
    self.log_to_detailed(f"\n\n**Error:** {error_msg}\n\nStacktrace:\n```\n{traceback.format_exc()}\n```\n")
    logger.error(error_msg, exc_info=True)
```

## Conclusion

The Habermas Machine represents an innovative approach to AI-assisted consensus building. By leveraging language models to synthesize diverse opinions and simulate preference-based elections, it offers a structured methodology for finding common ground in group discussions.

This implementation provides a user-friendly interface, detailed process documentation, and advanced features like recursive consensus building. It demonstrates how AI can help mediate complex human deliberations and build bridges between differing viewpoints.

Future improvements could include:
- Integration with additional language models
- More sophisticated preference prediction algorithms
- Real-time collaborative features for remote participants
- Analysis of convergence patterns over multiple rounds

Human-AI collaboration in consensus building remains an exciting and promising area of research, with potential applications in democratic processes, organizational decision-making, and conflict resolution.