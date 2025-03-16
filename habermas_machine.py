import tkinter as tk
import tkinter.messagebox as messagebox
import traceback
import sys
import os

# Try importing customtkinter with error handling
try:
    import customtkinter as ctk
except ImportError:
    # Show a message box with installation instructions if customtkinter is missing
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    messagebox.showerror(
        "Missing Dependency", 
        "The customtkinter package is required but not installed.\n\n"
        "Please install it using pip:\n"
        "pip install customtkinter"
    )
    sys.exit(1)

# Try importing other dependencies with error handling
try:
    import json
    import requests
    from threading import Thread, Event
    import time
    import random
    import re
    from collections import defaultdict
    import math
except ImportError as e:
    # Show message box for other missing dependencies
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Missing Dependency", 
        f"The following package is required but not installed:\n{str(e)}\n\n"
        "Please install it using pip."
    )
    sys.exit(1)

class HabermasMachine:
    def __init__(self, root):
        self.root = root
        self.root.title("Habermas Machine - Ollama Group Statement Synthesizer")
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
        self.recursive_group_frames = {}
        
        # Default prompt templates
        self.default_templates = {
            "candidate_generation": "Given the following question and participant statements, generate a single group statement that synthesizes their perspectives. This should represent a fair consensus or compromise position that most participants could accept.\n\n"
                                  "---\n\nQuestion: {question}\n\n"
                                  "---\n\n{participant_statements}\n\n---\n\n"
                                  "Generate a thoughtful and nuanced group statement that represents a fair synthesis of these perspectives. Focus on finding common ground, acknowledge areas of disagreement or lack of information, and present a position that most participants could accept.",
            
            "ranking_prediction": "Given a participant's statement on a question, predict how they would rank different group statements from most preferred (1) to least preferred ({num_candidates}).\n\n"
                                "Question: {question}\n\n"
                                "---\n\nParticipant {participant_num}'s original statement: {participant_statement}\n\n---\n\n"
                                "Group Statements to Rank:\n\n"
                                "---\n\n{candidate_statements}\n---\n\n"
                                "Based on the participant's original statement, predict their ranking of these group statements from most preferred to least preferred as a JSON object containing `\"ranking\": []`.\n\nThe ranking should reflect which statements best align with the participant's expressed viewpoint, values, and concerns."
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
        self.max_retries_var.set("3")  # Default for retries
        self.max_group_size_var.set("9")  # Default max group size
        self.question_text.insert("1.0", "Should voting be compulsory?")
        
        # Set prompt templates in the UI
        for key, template in self.prompt_templates.items():
            if key == "candidate_generation":
                self.candidate_template_text.delete("1.0", "end")
                self.candidate_template_text.insert("1.0", template)
            elif key == "ranking_prediction":
                self.ranking_template_text.delete("1.0", "end")
                self.ranking_template_text.insert("1.0", template)
        
        # Now that the UI is set up, add sample data
        self.load_sample_data()
    
    def load_sample_data(self):
        """Load sample participant statements for testing"""
        sample_participants = [
            "I believe voting should not be compulsory. It's a fundamental right, but also a personal choice. Forcing people to vote might lead to uninformed voting which could harm democracy. I think we should focus on making voting easier and educating people on its importance instead.",
            "I firmly believe that voting should be compulsory. Democracy only works when people participate, and too many people don't vote out of apathy rather than principled objection. In Australia, compulsory voting has led to higher turnout and a more representative government. The civic duty to vote outweighs individual inconvenience.",
            "While I understand the democratic importance of voting, making it compulsory seems problematic. People shouldn't be forced to participate in a system they might fundamentally disagree with. Instead, we should address the root causes of low voter turnout like inaccessibility, lack of faith in the system, and voter suppression.",
            "I'm on the fence about compulsory voting. On one hand, it ensures broader representation and forces politicians to appeal to all segments of society. On the other hand, it's coercive and might lead to random voting. Perhaps a middle ground is a small incentive for voting rather than a punishment for not voting.",
            "Voting should absolutely be compulsory with reasonable exemptions for those who cannot vote. Democracy requires participation, and treating voting as optional has led to lower turnout among disadvantaged groups. Compulsory voting ensures everyone has a stake in the outcome and reduces political polarization by requiring appeal to the majority."
        ]

        # Set them in the single textbox
        self.participants_text.delete("1.0", "end")
        self.participants_text.insert("1.0", "\n".join(sample_participants))
        self.update_participant_count()
    
    def create_layout(self):
        # Configure grid layout with 3 columns
        self.root.grid_columnconfigure(0, weight=1)  # Left: Settings & Inputs
        self.root.grid_columnconfigure(1, weight=1)  # Middle: Results
        self.root.grid_columnconfigure(2, weight=1)  # Right: Debug
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create main frames
        self.left_column = ctk.CTkFrame(self.root)
        self.middle_column = ctk.CTkFrame(self.root)
        self.right_column = ctk.CTkFrame(self.root)
        
        self.left_column.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.middle_column.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.right_column.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        
        # Set up the left column (settings & inputs)
        self.setup_left_column()
        
        # Set up the middle column (results)
        self.setup_middle_column()
        
        # Set up the right column (debug)
        self.setup_right_column()
    
    def setup_left_column(self):
        # Create a tabview for the left column (Settings, Inputs)
        self.left_tabview = ctk.CTkTabview(self.left_column)
        self.left_tabview.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add tabs for the left column
        self.left_tabview.add("Inputs")
        self.left_tabview.add("Settings")
        self.left_tabview.add("Templates")
        
        # Setup the Inputs tab (question, participants)
        self.setup_inputs_tab()
        
        # Setup the Settings tab (model, parameters)
        self.setup_settings_tab()
        
        # Setup the Templates tab (prompt templates)
        self.setup_templates_tab()
    
    def setup_inputs_tab(self):
        # Create a scrollable frame for inputs
        inputs_frame = ctk.CTkScrollableFrame(self.left_tabview.tab("Inputs"))
        inputs_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # The debate question
        ctk.CTkLabel(inputs_frame, text="Question:", anchor="w").pack(fill="x", padx=10, pady=(10, 5))
        self.question_text = ctk.CTkTextbox(inputs_frame, height=40)
        self.question_text.pack(fill="x", padx=10, pady=(0, 5))
        
        # Participant statements
        participants_header = ctk.CTkFrame(inputs_frame)
        participants_header.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(participants_header, text="Participant Statements (one per line):", anchor="w").pack(side="left", fill="x", padx=5)
        self.participant_count_label = ctk.CTkLabel(participants_header, text="Count: 0", width=100)
        self.participant_count_label.pack(side="right", padx=5)
        
        # Create a single textbox for all participant statements
        self.participants_text = ctk.CTkTextbox(inputs_frame, height=300, wrap="word")
        self.participants_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Add text changed callback to update participant count
        self.participants_text.bind("<KeyRelease>", self.update_participant_count)
        
        # Control buttons
        self.buttons_frame = ctk.CTkFrame(inputs_frame)
        self.buttons_frame.pack(fill="x", padx=10, pady=10)
        
        self.generate_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Generate Candidate Statements",
            command=self.start_generation
        )
        self.generate_btn.pack(side="left", padx=10, pady=10)
        
        self.simulate_election_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Simulate Election",
            command=self.simulate_election,
            state="disabled"
        )
        self.simulate_election_btn.pack(side="left", padx=10, pady=10)
        
        # Button for recursive generation
        self.recursive_generate_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Recursive Habermas",
            command=self.start_recursive_generation,
            fg_color="#1f5d3c"  # Dark green to distinguish it
        )
        self.recursive_generate_btn.pack(side="left", padx=10, pady=10)
        
        # Add bulk import button
        bulk_import_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Bulk Import",
            command=self.bulk_import,
            fg_color="#3d7e9a"  # Blue color to distinguish it
        )
        bulk_import_btn.pack(side="left", padx=10, pady=10)
        
        self.stop_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Stop",
            command=self.stop_generation,
            fg_color="darkred"
        )
        self.stop_btn.pack(side="right", padx=10, pady=10)
    
    def setup_settings_tab(self):
        # Create a scrollable frame for settings
        settings_frame = ctk.CTkScrollableFrame(self.left_tabview.tab("Settings"))
        settings_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Model selection
        model_frame = ctk.CTkFrame(settings_frame)
        model_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(model_frame, text="Model:", anchor="w").pack(side="left", padx=10)
        self.model_var = ctk.StringVar()
        self.model_entry = ctk.CTkEntry(model_frame, textvariable=self.model_var, width=200)
        self.model_entry.pack(side="left", padx=10, fill="x", expand=True)
        
        # Generation parameters section
        gen_params_frame = ctk.CTkFrame(settings_frame)
        gen_params_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(gen_params_frame, text="Generation Parameters", font=("Arial", 12, "bold")).pack(pady=5)
        
        params_grid = ctk.CTkFrame(gen_params_frame)
        params_grid.pack(fill="x", padx=10, pady=5, expand=True)
        
        # Temperature
        ctk.CTkLabel(params_grid, text="Temperature:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.temperature_var = ctk.StringVar()
        self.temperature_entry = ctk.CTkEntry(params_grid, textvariable=self.temperature_var, width=60)
        self.temperature_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Top P
        ctk.CTkLabel(params_grid, text="Top P:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.top_p_var = ctk.StringVar()
        self.top_p_entry = ctk.CTkEntry(params_grid, textvariable=self.top_p_var, width=60)
        self.top_p_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # Top K
        ctk.CTkLabel(params_grid, text="Top K:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.top_k_var = ctk.StringVar()
        self.top_k_entry = ctk.CTkEntry(params_grid, textvariable=self.top_k_var, width=60)
        self.top_k_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # Number of candidate statements
        ctk.CTkLabel(params_grid, text="Candidate Statements:").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.num_candidates_var = ctk.StringVar()
        self.num_candidates_spinbox = ctk.CTkEntry(params_grid, textvariable=self.num_candidates_var, width=50)
        self.num_candidates_spinbox.grid(row=0, column=3, padx=10, pady=5, sticky="w")
        
        # Ranking prediction parameters section
        rank_params_frame = ctk.CTkFrame(settings_frame)
        rank_params_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(rank_params_frame, text="Ranking Prediction Parameters", font=("Arial", 12, "bold")).pack(pady=5)
        
        rank_grid = ctk.CTkFrame(rank_params_frame)
        rank_grid.pack(fill="x", padx=10, pady=5, expand=True)
        
        # Ranking temperature
        ctk.CTkLabel(rank_grid, text="Temperature:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.ranking_temperature_var = ctk.StringVar()
        self.ranking_temperature_entry = ctk.CTkEntry(rank_grid, textvariable=self.ranking_temperature_var, width=60)
        self.ranking_temperature_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Maximum retries for JSON parsing
        ctk.CTkLabel(rank_grid, text="Max JSON Retries:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.max_retries_var = ctk.StringVar()
        self.max_retries_entry = ctk.CTkEntry(rank_grid, textvariable=self.max_retries_var, width=60)
        self.max_retries_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # NEW: Recursive Habermas settings
        recursive_frame = ctk.CTkFrame(settings_frame)
        recursive_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(recursive_frame, text="Recursive Habermas Settings", font=("Arial", 12, "bold")).pack(pady=5)
        
        recursive_grid = ctk.CTkFrame(recursive_frame)
        recursive_grid.pack(fill="x", padx=10, pady=5, expand=True)
        
        # Max group size
        ctk.CTkLabel(recursive_grid, text="Max Group Size:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.max_group_size_var = ctk.StringVar()
        self.max_group_size_entry = ctk.CTkEntry(recursive_grid, textvariable=self.max_group_size_var, width=60)
        self.max_group_size_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Voting strategy
        ctk.CTkLabel(recursive_grid, text="Voting Strategy:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.voting_strategy_var = ctk.StringVar(value="own_groups_only")
        
        strategy_frame = ctk.CTkFrame(recursive_grid)
        strategy_frame.grid(row=1, column=1, columnspan=3, padx=10, pady=5, sticky="w")
        
        own_groups_radio = ctk.CTkRadioButton(
            strategy_frame, 
            text="Own groups only", 
            variable=self.voting_strategy_var, 
            value="own_groups_only"
        )
        own_groups_radio.pack(anchor="w", pady=2)
        
        all_elections_radio = ctk.CTkRadioButton(
            strategy_frame, 
            text="All participants vote in all elections", 
            variable=self.voting_strategy_var, 
            value="all_elections"
        )
        all_elections_radio.pack(anchor="w", pady=2)
        
        # Template reset buttons section
        reset_frame = ctk.CTkFrame(settings_frame)
        reset_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(reset_frame, text="Reset Templates", font=("Arial", 12, "bold")).pack(pady=5)
        
        reset_buttons = ctk.CTkFrame(reset_frame)
        reset_buttons.pack(fill="x", padx=10, pady=5)
        
        reset_candidate_btn = ctk.CTkButton(
            reset_buttons,
            text="Reset Candidate Template",
            command=lambda: self.reset_template("candidate_generation")
        )
        reset_candidate_btn.pack(side="left", padx=10, pady=5)
        
        reset_ranking_btn = ctk.CTkButton(
            reset_buttons,
            text="Reset Ranking Template",
            command=lambda: self.reset_template("ranking_prediction")
        )
        reset_ranking_btn.pack(side="left", padx=10, pady=5)
        
        reset_all_btn = ctk.CTkButton(
            reset_buttons,
            text="Reset All Templates",
            command=self.reset_all_templates
        )
        reset_all_btn.pack(side="left", padx=10, pady=5)
    
    def setup_templates_tab(self):
        # Create a scrollable frame for templates
        templates_frame = ctk.CTkScrollableFrame(self.left_tabview.tab("Templates"))
        templates_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Candidate generation template
        ctk.CTkLabel(templates_frame, text="Candidate Generation Template:", anchor="w", font=("Arial", 12, "bold")).pack(fill="x", padx=10, pady=(10, 5))
        self.candidate_template_text = ctk.CTkTextbox(templates_frame, height=200, wrap="word")
        self.candidate_template_text.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(templates_frame, text="Available placeholders: {question}, {participant_statements}", anchor="w").pack(fill="x", padx=10, pady=(0, 10))
        
        # Ranking prediction template
        ctk.CTkLabel(templates_frame, text="Ranking Prediction Template:", anchor="w", font=("Arial", 12, "bold")).pack(fill="x", padx=10, pady=(10, 5))
        self.ranking_template_text = ctk.CTkTextbox(templates_frame, height=200, wrap="word")
        self.ranking_template_text.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(templates_frame, text="Available placeholders: {question}, {participant_num}, {participant_statement}, {num_candidates}, {candidate_statements}", anchor="w").pack(fill="x", padx=10, pady=(0, 10))
        
        # Save template changes button
        save_btn = ctk.CTkButton(
            templates_frame,
            text="Save Template Changes",
            command=self.save_templates
        )
        save_btn.pack(padx=10, pady=10)
    
    def setup_middle_column(self):
        # Create a notebook for different result tabs
        self.results_tabview = ctk.CTkTabview(self.middle_column)
        self.results_tabview.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add tabs
        self.results_tabview.add("Candidate Statements")
        self.results_tabview.add("Election Results")
        self.results_tabview.add("Recursive Results")  # NEW: Tab for recursive results
        
        # Candidate statements tab
        self.candidates_frame = ctk.CTkScrollableFrame(self.results_tabview.tab("Candidate Statements"))
        self.candidates_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Set up candidate statement displays
        self.candidate_displays = []
        max_candidates = 10  # Maximum number of candidates we'll support
        
        for i in range(max_candidates):
            candidate_frame = ctk.CTkFrame(self.candidates_frame)
            
            header_frame = ctk.CTkFrame(candidate_frame)
            header_frame.pack(fill="x", padx=5, pady=5)
            
            label = ctk.CTkLabel(header_frame, text=f"Candidate Statement {i+1}", anchor="w", font=("Arial", 14, "bold"))
            label.pack(side="left", padx=5, pady=5)
            
            vote_label = ctk.CTkLabel(header_frame, text="", anchor="e")
            vote_label.pack(side="right", padx=5, pady=5)
            
            candidate_text = ctk.CTkTextbox(candidate_frame, height=150, wrap="word")
            candidate_text.pack(fill="both", expand=True, padx=5, pady=5)
            
            self.candidate_displays.append((candidate_frame, label, vote_label, candidate_text))
            # We'll pack the frames only when we have content
        
        # Election results tab - make sure it's fully expandable
        self.results_frame = ctk.CTkScrollableFrame(self.results_tabview.tab("Election Results"))
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configure the results frame to give more space to the winner frame
        self.results_frame.columnconfigure(0, weight=1)
        
        self.winner_frame = ctk.CTkFrame(self.results_frame)
        self.winner_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(self.winner_frame, text="Winning Statement", font=("Arial", 16, "bold")).pack(pady=5)
        
        self.winner_text = ctk.CTkTextbox(self.winner_frame, height=300, wrap="word")
        self.winner_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.ranking_frame = ctk.CTkFrame(self.results_frame)
        self.ranking_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(self.ranking_frame, text="Simulated Election Results", font=("Arial", 14, "bold")).pack(pady=5)
        
        self.ranking_text = ctk.CTkTextbox(self.ranking_frame, height=300, wrap="word")
        self.ranking_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # NEW: Recursive results tab
        self.recursive_results_frame = ctk.CTkScrollableFrame(self.results_tabview.tab("Recursive Results"))
        self.recursive_results_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    def setup_right_column(self):
        # Create debug frames with more space
        self.right_column.grid_rowconfigure(0, weight=1)
        self.right_column.grid_rowconfigure(1, weight=1)
        self.right_column.grid_columnconfigure(0, weight=1)
        
        # Debug prompt panel - ensure it expands to fill available space
        prompt_frame = ctk.CTkFrame(self.right_column)
        prompt_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        prompt_frame.pack_propagate(False)  # Prevent the frame from shrinking to fit its contents
        
        prompt_frame.grid_rowconfigure(1, weight=1)
        prompt_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(prompt_frame, text="Current Prompt", font=("Arial", 14, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.prompt_text = ctk.CTkTextbox(prompt_frame, wrap="word")
        self.prompt_text.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Debug response panel - ensure it expands to fill available space
        response_frame = ctk.CTkFrame(self.right_column)
        response_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        response_frame.pack_propagate(False)  # Prevent the frame from shrinking to fit its contents
        
        response_frame.grid_rowconfigure(1, weight=1)
        response_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(response_frame, text="Current Response", font=("Arial", 14, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.response_text = ctk.CTkTextbox(response_frame, wrap="word")
        self.response_text.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
    
    def update_participant_count(self, event=None):
        """Update the participant count label based on the number of non-empty lines"""
        text = self.participants_text.get("1.0", "end-1c")
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        self.participant_count_label.configure(text=f"Count: {len(lines)}")
    
    # REMOVED - Replaced with a method where all particpant statements share a single textboxt, for easier copy-paste and better performance.
    # def update_participant_panels(self):
        # try:
            # new_num_participants = max(2, min(50, int(self.num_participants_var.get())))
            # self.num_participants_var.set(str(new_num_participants))
        # except ValueError:
            # new_num_participants = 5
            # self.num_participants_var.set("5")
        
        # # Store existing participant statements
        # old_entries = []
        # for entry in self.participant_entry_fields:
            # if entry.winfo_exists():
                # old_entries.append(entry.get("1.0", "end-1c"))
            # else:
                # old_entries.append("")
        
        # # Make sure our persistent storage has enough slots
        # # Extend the stored statements list if needed
        # while len(self.stored_participant_statements) < len(old_entries):
            # self.stored_participant_statements.append("")
        
        # # Update our persistent storage with any UI changes
        # for i, entry_text in enumerate(old_entries):
            # if i < len(self.stored_participant_statements):
                # self.stored_participant_statements[i] = entry_text
        
        # # Clear existing participant frames
        # for widget in self.participants_container.winfo_children():
            # widget.destroy()
        
        # # Reset the list of entry fields
        # self.participant_entry_fields = []
        
        # # Create new participant frames based on the new count
        # for i in range(new_num_participants):
            # participant_frame = ctk.CTkFrame(self.participants_container)
            # participant_frame.pack(fill="x", pady=5)
            
            # # Create label with participant number
            # ctk.CTkLabel(participant_frame, text=f"Participant {i+1}:", anchor="w", width=100).pack(side="top", anchor="w", padx=5, pady=2)
            
            # # Create text entry for participant opinion
            # participant_entry = ctk.CTkTextbox(participant_frame, height=80, wrap="word")
            # participant_entry.pack(fill="x", padx=5, pady=2)
            
            # # Add to list of entry fields
            # self.participant_entry_fields.append(participant_entry)
            
            # # Restore previous text if available
            # if i < len(self.stored_participant_statements) and self.stored_participant_statements[i]:
                # participant_entry.insert("1.0", self.stored_participant_statements[i])
    
    def save_templates(self):
        # Get the current template text
        candidate_template = self.candidate_template_text.get("1.0", "end-1c")
        ranking_template = self.ranking_template_text.get("1.0", "end-1c")
        
        # Update the templates
        self.prompt_templates["candidate_generation"] = candidate_template
        self.prompt_templates["ranking_prediction"] = ranking_template
        
        messagebox.showinfo("Templates Saved", "Prompt templates have been updated.")
    
    def reset_template(self, template_key):
        if template_key in self.default_templates:
            self.prompt_templates[template_key] = self.default_templates[template_key]
            
            if template_key == "candidate_generation":
                self.candidate_template_text.delete("1.0", "end")
                self.candidate_template_text.insert("1.0", self.default_templates[template_key])
            elif template_key == "ranking_prediction":
                self.ranking_template_text.delete("1.0", "end")
                self.ranking_template_text.insert("1.0", self.default_templates[template_key])
            
            messagebox.showinfo("Template Reset", f"The {template_key} template has been reset to default.")
    
    def bulk_import(self):
        """Import question and participant statements from a text file"""
        file_path = ctk.filedialog.askopenfilename(
            title="Select text file",
            filetypes=(
                ("Text files", "*.txt"),
                ("Markdown files", "*.md"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            )
        )
        
        if not file_path:
            return  # User canceled
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            # Filter out empty lines
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            
            if not non_empty_lines:
                messagebox.showerror("Error", "File contains no content.")
                return
            
            # First line is the question
            question = non_empty_lines[0]
            
            # Remaining lines are participant statements
            statements = non_empty_lines[1:]
            
            # Update the UI
            self.question_text.delete("1.0", "end")
            self.question_text.insert("1.0", question)
            
            # Update participants textbox
            self.participants_text.delete("1.0", "end")
            self.participants_text.insert("1.0", "\n".join(statements))
            
            # Update the count
            self.update_participant_count()
            
            messagebox.showinfo("Import Successful", f"Imported question and {len(statements)} participant statements.")
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Error importing file: {str(e)}")
    
    def reset_all_templates(self):
        self.prompt_templates = self.default_templates.copy()
        
        self.candidate_template_text.delete("1.0", "end")
        self.candidate_template_text.insert("1.0", self.default_templates["candidate_generation"])
        
        self.ranking_template_text.delete("1.0", "end")
        self.ranking_template_text.insert("1.0", self.default_templates["ranking_prediction"])
        
        messagebox.showinfo("Templates Reset", "All prompt templates have been reset to default.")
    
    def get_participant_statements(self):
        """Extract participant statements from the textbox"""
        text = self.participants_text.get("1.0", "end-1c")
        statements = [line.strip() for line in text.split('\n') if line.strip()]
        return statements
    
    def start_generation(self):
        self.stop_event.clear()
        
        # Collect participant statements
        self.participant_statements = self.get_participant_statements()
        
        if len(self.participant_statements) < 2:
            messagebox.showerror("Error", "Please provide at least 2 participant statements.")
            return
        
        # Clear previous candidate statements
        self.candidate_statements = []
        for frame, _, _, text in self.candidate_displays:
            if frame.winfo_ismapped():
                frame.pack_forget()
            text.delete("1.0", "end")
        
        # Disable buttons during generation
        self.generate_btn.configure(state="disabled")
        self.recursive_generate_btn.configure(state="disabled")
        self.simulate_election_btn.configure(state="disabled")
        
        # Start generation thread
        Thread(target=self.generate_candidate_statements, daemon=True).start()
    
    def stop_generation(self):
        self.stop_event.set()
        if self.current_response:
            try:
                self.current_response.close()
            except:
                pass
        
        self.generate_btn.configure(state="normal")
        self.recursive_generate_btn.configure(state="normal")
        if len(self.candidate_statements) > 1:
            self.simulate_election_btn.configure(state="normal")
    
    def generate_candidate_statements(self):
        try:
            num_candidates = min(10, max(2, int(self.num_candidates_var.get())))
        except ValueError:
            num_candidates = 4
            self.root.after(0, lambda: self.num_candidates_var.set("4"))
        
        question = self.question_text.get("1.0", "end-1c").strip()
        
        for i in range(num_candidates):
            if self.stop_event.is_set():
                break
                
            # Randomize the order of participant statements for each candidate
            shuffled_statements = self.participant_statements.copy()
            random.shuffle(shuffled_statements)
            
            # Generate the candidate statement
            candidate = self.generate_single_candidate(question, shuffled_statements, i+1)
            
            if candidate and not self.stop_event.is_set():
                self.candidate_statements.append(candidate)
                
                # Display the candidate
                frame, label, vote_label, text_widget = self.candidate_displays[i]
                frame.pack(fill="x", pady=10, padx=5, expand=True)
                text_widget.delete("1.0", "end")
                text_widget.insert("1.0", candidate)
                
                # Switch to the candidates tab
                self.results_tabview.set("Candidate Statements")
        
        # Re-enable buttons after generation
        if not self.stop_event.is_set():
            self.root.after(0, lambda: self.generate_btn.configure(state="normal"))
            self.root.after(0, lambda: self.recursive_generate_btn.configure(state="normal"))
            if len(self.candidate_statements) > 1:
                self.root.after(0, lambda: self.simulate_election_btn.configure(state="normal"))
    
    def generate_single_candidate(self, question, statements, candidate_num):
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
        
        # Update the debug prompt display
        self.root.after(0, lambda: self.update_debug_prompt(prompt))
        
        # Prepare API call parameters
        model = self.model_var.get()
        try:
            temperature = float(self.temperature_var.get())
            top_p = float(self.top_p_var.get())
            top_k = int(self.top_k_var.get())
        except ValueError:
            temperature = 0.7
            top_p = 0.9
            top_k = 40
            
        # Make the API call
        try:
            self.current_response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k
                    }
                },
                stream=True
            )
            
            if self.current_response.status_code != 200:
                self.root.after(0, lambda: messagebox.showerror("API Error", f"Error: Status code {self.current_response.status_code}"))
                return None
            
            full_response = ""
            for line in self.current_response.iter_lines():
                if self.stop_event.is_set():
                    break
                    
                if line:
                    try:
                        data = json.loads(line)
                        if 'response' in data:
                            # Handle streamed text
                            response_text = data['response']
                            full_response += response_text
                            
                            # Update the debug response display
                            self.root.after(0, lambda r=full_response: self.update_debug_response(r))
                    except json.JSONDecodeError:
                        self.root.after(0, lambda: messagebox.showerror("Error", "Failed to decode response from Ollama API"))
                
            # Remove the <think>...</think> tag that DeepSeek-R1 may add
            clean_response = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL).strip()
            
            return clean_response
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Exception: {str(e)}"))
            return None
        finally:
            self.current_response = None
    
    def simulate_election(self):
        if len(self.candidate_statements) < 2:
            messagebox.showerror("Error", "Need at least 2 candidate statements to simulate an election.")
            return
        
        self.stop_event.clear()
        self.simulate_election_btn.configure(state="disabled")
        self.generate_btn.configure(state="disabled")
        self.recursive_generate_btn.configure(state="disabled")
        
        # Start simulation thread
        Thread(target=self.run_election_simulation, daemon=True).start()
    
    def run_election_simulation(self):
        question = self.question_text.get("1.0", "end-1c").strip()
        num_participants = len(self.participant_statements)
        
        # Initialize simulated rankings
        rankings = {i: [] for i in range(num_participants)}
        
        # Log for JSON ranking attempts
        ranking_attempts_log = []
        
        # For each participant, predict their rankings
        for p_idx in range(num_participants):
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
            self.generate_btn.configure(state="normal")
            self.recursive_generate_btn.configure(state="normal")
            self.simulate_election_btn.configure(state="normal")
            return
        
        # Calculate winner using the Schulze method
        winner_idx, pairwise_matrix, strongest_paths = self.schulze_method(rankings, len(self.candidate_statements))
        winner_statement = self.candidate_statements[winner_idx]
        
        # Generate information about pairwise votes for display
        pairwise_counts = {}
        for i in range(len(self.candidate_statements)):
            for j in range(len(self.candidate_statements)):
                if i != j:
                    pairwise_counts[(i, j)] = pairwise_matrix[i][j]
        
        # Update the UI with results
        self.root.after(0, lambda: self.show_election_results(rankings, winner_idx, pairwise_counts, pairwise_matrix, strongest_paths, ranking_attempts_log))
        
        # Re-enable buttons
        self.root.after(0, lambda: self.generate_btn.configure(state="normal"))
        self.root.after(0, lambda: self.recursive_generate_btn.configure(state="normal"))
        self.root.after(0, lambda: self.simulate_election_btn.configure(state="normal"))
    
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
        # A candidate is a winner if their strongest path to every other candidate is stronger than
        # or equal to the strongest path from each other candidate to them
        potential_winners = set(range(num_candidates))
        
        for i in range(num_candidates):
            for j in range(num_candidates):
                if i != j and strongest_paths[j][i] > strongest_paths[i][j]:
                    if i in potential_winners:
                        potential_winners.remove(i)
        
        # Return the winner with the lowest index (if there are multiple winners)
        winner_idx = min(potential_winners) if potential_winners else 0
        
        return winner_idx, pairwise_matrix, strongest_paths
    
    def create_ranking_system_prompt(self, num_candidates):
        """Create a system prompt that instructs the model to output JSON ranking"""
        # Generate a simple non-biasing example with a different number of candidates
        example_size = max(3, num_candidates - 1)  # Use a different number to avoid bias
        example_ranking = list(range(1, example_size + 1))
        random.shuffle(example_ranking)  # Randomize to avoid bias
        
        system_prompt = (
            "You are a ranking prediction assistant that outputs results in JSON format. "
            "Your task is to predict how a participant would rank statements based on their perspective.\n\n"
            f"Your response MUST be a valid JSON object with a 'ranking' field containing an array of integers representing "
            f"statement numbers (1 to {num_candidates}), ordered from most preferred to least preferred.\n\n"
            "Example JSON format (do not copy these example values):\n"
            "{\n"
            f"  \"ranking\": {example_ranking}\n"
            "}\n\n"
            "Your entire response should ONLY contain the JSON object, with no additional text before or after."
        )
        return system_prompt
    
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
        
        # Update the debug prompt display
        self.root.after(0, lambda: self.update_debug_prompt(f"System prompt:\n{system_prompt}\n\n---\n\nUser prompt:\n{prompt}"))
        
        # Prepare API call parameters
        model = self.model_var.get()
        try:
            temperature = float(self.ranking_temperature_var.get())
        except ValueError:
            temperature = 0.2  # Lower temperature for more deterministic ranking prediction
        
        # Keep track of retry attempts
        attempts = 0
        attempts_log = []
        
        while attempts < max_retries:
            attempts += 1
            
            # Make the API call with system prompt
            try:
                self.current_response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "system": system_prompt,  # Add system prompt here
                        "stream": True,
                        "options": {
                            "temperature": temperature
                        }
                    },
                    stream=True
                )
                
                if self.current_response.status_code != 200:
                    attempt_error = f"Attempt {attempts}: API Error: Status code {self.current_response.status_code}"
                    attempts_log.append(attempt_error)
                    continue
                
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
                                
                                # Update the debug response display
                                self.root.after(0, lambda r=full_response: self.update_debug_response(r))
                        except json.JSONDecodeError:
                            pass
                
                # Log this attempt
                attempts_log.append(f"Attempt {attempts}: Response received, parsing...")
                
                # Try to extract JSON from the response
                try:
                    # Remove the <think>...</think> tag that DeepSeek-R1 may add
                    clean_response = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL).strip()
                    
                    # Try to find a JSON object within the text
                    match = re.search(r'({[\s\S]*?})', clean_response)
                    if match:
                        json_str = match.group(1)
                        ranking_data = json.loads(json_str)
                        
                        if "ranking" in ranking_data and isinstance(ranking_data["ranking"], list):
                            # Convert 1-indexed to 0-indexed
                            ranking = [num - 1 for num in ranking_data["ranking"]]
                            
                            # Validate ranking has correct indices
                            valid_indices = set(range(len(candidate_statements)))
                            if set(ranking) == valid_indices and len(ranking) == len(candidate_statements):
                                attempts_log.append(f"Attempt {attempts}: Success! Valid JSON ranking found.")
                                return ranking, attempts_log
                            else:
                                attempts_log.append(f"Attempt {attempts}: Invalid ranking indices: {ranking}")
                        else:
                            attempts_log.append(f"Attempt {attempts}: JSON missing 'ranking' field or not a list")
                    else:
                        attempts_log.append(f"Attempt {attempts}: No JSON object found in response")
                
                except json.JSONDecodeError as e:
                    attempts_log.append(f"Attempt {attempts}: JSON parsing error: {str(e)}")
                except Exception as e:
                    attempts_log.append(f"Attempt {attempts}: Error processing response: {str(e)}")
                
            except Exception as e:
                attempts_log.append(f"Attempt {attempts}: Exception: {str(e)}")
            finally:
                self.current_response = None
        
        # If we get here, all attempts failed
        attempts_log.append("All attempts failed. Falling back to random ranking.")
        
        # Fallback to a random ranking
        random_ranking = list(range(len(candidate_statements)))
        random.shuffle(random_ranking)
        return random_ranking, attempts_log
    
    def show_election_results(self, rankings, winner_idx, pairwise_counts, pairwise_matrix, strongest_paths, ranking_attempts_log):
        # Display the winner
        self.winner_text.delete("1.0", "end")
        self.winner_text.insert("1.0", self.candidate_statements[winner_idx])
        
        # Display vote counts on candidate statements
        for i, (frame, _, vote_label, _) in enumerate(self.candidate_displays):
            if i < len(self.candidate_statements):
                # Calculate "strength" which is how many other candidates this one defeats in a pairwise comparison
                victories = sum(1 for j in range(len(self.candidate_statements)) if i != j and strongest_paths[i][j] > strongest_paths[j][i])
                vote_label.configure(text=f"Schulze Score: {victories}")
                
                # Highlight the winner
                if i == winner_idx:
                    frame.configure(fg_color="#1f5d3c")  # dark green for winner
                else:
                    frame.configure(fg_color="transparent")  # Use 'transparent' instead of None
        
        # Display detailed election results
        self.ranking_text.delete("1.0", "end")
        election_report = "=== SIMULATED ELECTION RESULTS (SCHULZE METHOD) ===\n\n"
        
        # Add election summary
        total_participants = len(rankings)
        election_report += f"Total participants: {total_participants}\n"
        election_report += f"Winning statement: Statement {winner_idx + 1}\n\n"
        
        # Add Schulze method explanation
        election_report += "=== SCHULZE METHOD RESULTS ===\n"
        election_report += "The Schulze method compares each pair of statements to see which one is preferred by more participants.\n"
        election_report += "For each pair of statements, a 'path strength' is calculated, representing how strongly one\n"
        election_report += "statement is preferred over another considering all possible transitive preferences.\n\n"
        
        # Add information about strongest paths
        election_report += "Statement rankings based on Schulze method:\n"
        
        # Count how many other statements each statement defeats
        victories = defaultdict(int)
        for i in range(len(self.candidate_statements)):
            for j in range(len(self.candidate_statements)):
                if i != j and strongest_paths[i][j] > strongest_paths[j][i]:
                    victories[i] += 1
        
        # Display statements sorted by Schulze ranking
        sorted_statements = sorted(range(len(self.candidate_statements)), 
                                  key=lambda x: victories[x], 
                                  reverse=True)
        
        for rank, stmt_idx in enumerate(sorted_statements, 1):
            marker = "[WINNER]" if stmt_idx == winner_idx else ""
            election_report += f"Rank {rank}: Statement {stmt_idx + 1} (defeats {victories[stmt_idx]} other statements) {marker}\n"
        
        election_report += "\n=== PAIRWISE PREFERENCE MATRIX ===\n"
        election_report += "This matrix shows how many participants preferred statement in row over statement in column:\n\n"
        
        # Header row
        election_report += "       |"
        for i in range(len(self.candidate_statements)):
            election_report += f" S{i+1:2d} |"
        election_report += "\n"
        
        # Separator
        election_report += "-------+" + "-----+" * len(self.candidate_statements) + "\n"
        
        # Data rows
        for i in range(len(self.candidate_statements)):
            election_report += f" S{i+1:2d}  |"
            for j in range(len(self.candidate_statements)):
                if i == j:
                    election_report += "  -  |"
                else:
                    election_report += f" {pairwise_matrix[i][j]:2d}  |"
            election_report += "\n"
        
        election_report += "\n=== STRONGEST PATHS MATRIX ===\n"
        election_report += "This matrix shows the strength of the strongest 'path' from row statement to column statement:\n\n"
        
        # Header row
        election_report += "       |"
        for i in range(len(self.candidate_statements)):
            election_report += f" S{i+1:2d} |"
        election_report += "\n"
        
        # Separator
        election_report += "-------+" + "-----+" * len(self.candidate_statements) + "\n"
        
        # Data rows
        for i in range(len(self.candidate_statements)):
            election_report += f" S{i+1:2d}  |"
            for j in range(len(self.candidate_statements)):
                if i == j:
                    election_report += "  -  |"
                else:
                    election_report += f" {strongest_paths[i][j]:2d}  |"
            election_report += "\n"
        
        election_report += "\n=== INDIVIDUAL PARTICIPANT RANKINGS ===\n" 
        election_report += "(Lower number = higher preference)\n\n"
        
        # Create a table-like format for participant rankings
        header = "Participant |"
        for i in range(len(self.candidate_statements)):
            header += f" Stmt {i+1} |"
        election_report += header + "\n"
        
        separator = "-" * len(header) + "\n"
        election_report += separator
        
        # Add each participant's ranking
        for p_idx in sorted(rankings.keys()):
            p_ranking = rankings[p_idx]
            row = f"    P{p_idx + 1}     |"
            
            # Create ranking display
            for stmt_idx in range(len(self.candidate_statements)):
                if p_ranking and stmt_idx in p_ranking:
                    rank = p_ranking.index(stmt_idx) + 1
                    row += f"   {rank}   |"
                else:
                    row += "   -   |"
            
            election_report += row + "\n"
        
        election_report += separator + "\n"
        
        # Add JSON ranking attempts log
        election_report += "=== JSON RANKING ATTEMPTS LOG ===\n\n"
        for p_idx, attempts in enumerate(ranking_attempts_log):
            election_report += f"Participant {p_idx + 1}:\n"
            for attempt in attempts:
                election_report += f"  • {attempt}\n"
            election_report += "\n"
        
        # Add methodology explanation
        election_report += "=== ELECTION METHODOLOGY ===\n"
        election_report += "The election was simulated using the Schulze method, which is a Condorcet voting system.\n"
        election_report += "This method compares each pair of candidates and finds paths of preference between them.\n"
        election_report += "The Schulze method has the following properties:\n"
        election_report += " • Independence of clones (similar candidates don't split votes)\n"
        election_report += " • Condorcet winner criterion (if a candidate beats all others in pairwise comparisons, they win)\n"
        election_report += " • Robustness to strategic voting\n\n"
        
        election_report += "Each participant's ranking was predicted by the\n"
        election_report += f"'{self.model_var.get()}' model based on their initial statements.\n"
        election_report += "Rankings were extracted from JSON-formatted responses.\n"
        
        self.ranking_text.insert("1.0", election_report)
        
        # Switch to the results tab
        self.results_tabview.set("Election Results")
        
        # Return the winning statement for use in recursive functions
        return self.candidate_statements[winner_idx]

    def update_debug_response(self, response):
        # Keep track of whether we should auto-scroll
        # Get the current position of the scroll
        current_position = self.response_text.yview()
        # Check if we were already at the bottom before the update
        at_bottom = (current_position[1] >= 0.99)
        
        # Update the text
        self.response_text.delete("1.0", "end")
        self.response_text.insert("1.0", response)
        
        # If we were at the bottom, scroll back to the bottom after the update
        if at_bottom:
            self.response_text.see("end")
            # Make sure we're really at the bottom
            self.response_text.yview_moveto(1.0)

    # Apply the same fix to the prompt text display
    def update_debug_prompt(self, prompt):
        # Keep track of whether we should auto-scroll
        current_position = self.prompt_text.yview()
        at_bottom = (current_position[1] >= 0.99)
        
        # Update the text
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", prompt)
        
        # If we were at the bottom, scroll back to the bottom after the update
        if at_bottom:
            self.prompt_text.see("end")
            self.prompt_text.yview_moveto(1.0)
            
    # RECURSIVE HABERMAS MACHINE METHODS
    
    def start_recursive_generation(self):
        """Start the recursive Habermas Machine process"""
        self.stop_event.clear()
        
        # Collect participant statements
        self.participant_statements = self.get_participant_statements()
        
        if len(self.participant_statements) < 2:
            messagebox.showerror("Error", "Please provide at least 2 participant statements.")
            return
        
        # Clear the recursive results display
        for widget in self.recursive_results_frame.winfo_children():
            widget.destroy()
            
        # Disable buttons during generation
        self.generate_btn.configure(state="disabled")
        self.recursive_generate_btn.configure(state="disabled")
        self.simulate_election_btn.configure(state="disabled")
        
        # Start recursive generation thread
        Thread(target=self.run_recursive_habermas, daemon=True).start()
    
    def run_recursive_habermas(self):
        """Run the recursive Habermas process"""
        question = self.question_text.get("1.0", "end-1c").strip()
        
        # Get and validate max group size
        try:
            max_group_size = min(9, max(2, int(self.max_group_size_var.get())))
        except ValueError:
            max_group_size = 9
            self.root.after(0, lambda: self.max_group_size_var.set("9"))
        
        # Get voting strategy
        voting_strategy = self.voting_strategy_var.get()
        
        # Create header in recursive results FIRST (this creates recursive_progress_label)
        self.root.after(0, lambda: self.create_recursive_header(question, len(self.participant_statements), max_group_size))
        
        # Give time for the UI to update and create the progress label
        time.sleep(0.1)
        
        # THEN update progress with information (only after recursive_progress_label exists)
        self.root.after(0, lambda: self.update_recursive_progress(
            f"Starting recursive process with {len(self.participant_statements)} participant statements..."
        ))
        
        # Run the recursive process
        final_statement = self.recursive_habermas_process(
            question, 
            self.participant_statements.copy(), 
            max_group_size,
            voting_strategy,
            0,  # Initial level
            {}  # Empty participant mapping (first level uses original participants)
        )
        
        if not self.stop_event.is_set():
            # Display final result
            self.root.after(0, lambda: self.display_final_recursive_result(final_statement))
            
        # Re-enable buttons
        self.root.after(0, lambda: self.generate_btn.configure(state="normal"))
        self.root.after(0, lambda: self.recursive_generate_btn.configure(state="normal"))

    def update_recursive_progress(self, message):
        """Update the recursive progress label if it exists"""
        if hasattr(self, 'recursive_progress_label'):
            self.recursive_progress_label.configure(text=message)

    def recursive_habermas_process(self, question, statements, max_group_size, voting_strategy, level, participant_mapping):
        """
        Run the recursive Habermas process for a list of statements
        
        Args:
            question: The question being debated
            statements: List of statements to process
            max_group_size: Maximum number of statements per group
            voting_strategy: Strategy for voting in elections ('own_groups_only' or 'all_elections')
            level: Current recursion level (0 = initial statements)
            participant_mapping: Dictionary mapping meta-statement indices to original participant indices
        
        Returns:
            The winning consensus statement
        """
        if self.stop_event.is_set():
            return None
            
        # If we have few enough statements to process in one group, do it directly
        if len(statements) <= max_group_size:
            # Create a frame to show this group's process
            group_frame = self.root.after(0, lambda: self.create_recursive_group_frame(
                level, 0, statements, len(statements)
            ))
            
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
        
        # Process each group to get winning statements
        winning_statements = []
        new_participant_mapping = {}  # Maps winning statement index to original participant indices
        
        for group_idx, group in enumerate(groups):
            if self.stop_event.is_set():
                return None
                
            # Create a frame to show this group's process
            group_frame = self.root.after(0, lambda gi=group_idx, g=group: self.create_recursive_group_frame(
                level, gi, g, len(statements)
            ))
            
            # Get list of original participant indices for this group
            if level == 0:
                # At level 0, map the group's statement indices to original participant indices
                group_participant_indices = [i for i, _ in enumerate(group)]
            else:
                # At higher levels, use the existing mapping to find original participants
                group_participant_indices = []
                start_idx = sum(len(g) for g in groups[:group_idx])
                for i, _ in enumerate(group):
                    orig_idx = start_idx + i
                    if orig_idx in participant_mapping:
                        group_participant_indices.extend(participant_mapping[orig_idx])
            
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
            
        # If we only got one winning statement, return it
        if len(winning_statements) == 1:
            return winning_statements[0]
            
        # Otherwise, recurse to process the winning statements
        if winning_statements:
            return self.recursive_habermas_process(
                question, 
                winning_statements, 
                max_group_size, 
                voting_strategy,
                level + 1,
                new_participant_mapping
            )
        
        return None
    
    def process_single_group(self, question, statements, original_participant_indices, voting_strategy, level, group_idx):
        """Process a single group of statements to find a winning statement"""
        if self.stop_event.is_set():
            return None
            
        group_size = len(statements)
        group_label = f"Level {level}, Group {group_idx+1} ({group_size} statements)"
        
        # Update debug with info about processing this group
        self.root.after(0, lambda: self.update_debug_prompt(
            f"Processing {group_label}\n\n"
            f"Question: {question}\n\n"
            f"Statements:\n" + "\n\n".join([f"{i+1}. {s}" for i, s in enumerate(statements)])
        ))
        
        # Update UI to show we're working on this group
        self.root.after(0, lambda: self.update_recursive_group_progress(
            level, group_idx, "Generating candidates...", 
            "Starting candidate generation for this group..."
        ))
        
        # Generate candidate statements for this group
        candidates = []
        
        try:
            num_candidates = min(group_size, max(2, int(self.num_candidates_var.get())))
        except ValueError:
            num_candidates = min(group_size, 3)
            
        for i in range(num_candidates):
            if self.stop_event.is_set():
                return None
                
            # Copy and shuffle statements to avoid bias
            shuffled_statements = statements.copy()
            random.shuffle(shuffled_statements)
            
            # Generate a candidate
            self.root.after(0, lambda: self.update_debug_response(
                f"Generating candidate {i+1}/{num_candidates} for {group_label}..."
            ))
            
            candidate = self.generate_single_candidate(question, shuffled_statements, i+1)
            if candidate:
                candidates.append(candidate)
                
                # Update UI to show progress
                self.root.after(0, lambda c=candidate, i=i: self.update_recursive_group_progress(
                    level, group_idx, f"Generated candidate {i+1}/{num_candidates}", 
                    f"Candidate {i+1}:\n{c[:150]}..."
                ))
        
        if not candidates:
            self.root.after(0, lambda: self.update_recursive_group_progress(
                level, group_idx, "Failed to generate candidates", 
                "No candidates were successfully generated for this group."
            ))
            return None
            
        # For voting, determine which participants vote in this election
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
        self.root.after(0, lambda: self.update_recursive_group_progress(
            level, group_idx, f"Running election with {len(voting_participants)} voters", 
            f"Candidates: {len(candidates)}\nVoters: {len(voting_participants)}"
        ))
            
        winner_idx = self.run_mini_election(question, candidates, voting_participants)
        
        if winner_idx is not None:
            winning_statement = candidates[winner_idx]
            
            # Update UI to show result
            self.root.after(0, lambda w=winning_statement: self.update_recursive_group_result(
                level, group_idx, w
            ))
            
            return winning_statement
        
        self.root.after(0, lambda: self.update_recursive_group_progress(
            level, group_idx, "Failed to determine a winner", 
            "The election process did not produce a clear winner."
        ))
        return None
    
    def run_mini_election(self, question, candidates, voting_participants):
        """Run a smaller election for a group of statements
        
        Args:
            question: The debate question
            candidates: List of candidate statements
            voting_participants: List of (participant_idx, statement) tuples
            
        Returns:
            Index of winning candidate or None
        """
        if not candidates or not voting_participants:
            return None
            
        # Initialize rankings
        rankings = {i: [] for i in range(len(voting_participants))}
        
        # For each participant, predict their rankings
        for p_idx, (orig_idx, statement) in enumerate(voting_participants):
            if self.stop_event.is_set():
                return None
                
            # Predict ranking for this participant
            predicted_ranking, _ = self.predict_participant_ranking_json(
                question, 
                statement, 
                candidates,
                orig_idx + 1  # Use original participant number for prompt
            )
            
            if predicted_ranking:
                rankings[p_idx] = predicted_ranking
        
        if not rankings:
            return None
            
        # Calculate winner using Schulze method
        winner_idx, _, _ = self.schulze_method(rankings, len(candidates))
        return winner_idx
    
    def divide_statements_into_groups(self, statements, max_group_size):
        # Shuffle statements first to avoid manipulation
        shuffled_statements = statements.copy()
        random.shuffle(shuffled_statements)
        
        """Divide statements into groups of maximum size"""
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
    
    def create_recursive_header(self, question, num_participants, max_group_size):
        """Create a header for the recursive results display"""
        header_frame = ctk.CTkFrame(self.recursive_results_frame)
        header_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(
            header_frame, 
            text="Recursive Habermas Machine Results", 
            font=("Arial", 16, "bold")
        ).pack(pady=5)
        
        info_text = (
            f"Question: {question}\n"
            f"Total participants: {num_participants}\n"
            f"Maximum group size: {max_group_size}\n"
            f"Voting strategy: {self.voting_strategy_var.get()}\n"
        )
        
        info_label = ctk.CTkLabel(header_frame, text=info_text, justify="left")
        info_label.pack(pady=5, padx=10, anchor="w")
        
        # Add a progress frame
        self.recursive_progress_frame = ctk.CTkFrame(self.recursive_results_frame)
        self.recursive_progress_frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(
            self.recursive_progress_frame, 
            text="Current progress:", 
            font=("Arial", 12, "bold")
        ).pack(pady=5, anchor="w", padx=10)
        
        self.recursive_progress_label = ctk.CTkLabel(
            self.recursive_progress_frame, 
            text="Starting recursive process...", 
            justify="left"
        )
        self.recursive_progress_label.pack(pady=5, padx=10, anchor="w")
        
        # Switch to the recursive results tab
        self.results_tabview.set("Recursive Results")
    
    def create_recursive_group_frame(self, level, group_idx, statements, total_statements):
        """Create a frame for displaying a group's process in the recursive UI"""
        group_label = f"Level {level}, Group {group_idx+1}"
        
        # Create a collapsible frame for this group
        group_frame = ctk.CTkFrame(self.recursive_results_frame)
        group_frame.pack(fill="x", pady=5, padx=5)
        
        # Header with toggle button
        header_frame = ctk.CTkFrame(group_frame)
        header_frame.pack(fill="x", pady=2)
        
        # Update progress label
        self.recursive_progress_label.configure(
            text=f"Processing {group_label} ({len(statements)} of {total_statements} statements)"
        )
        
        # Group label
        ctk.CTkLabel(
            header_frame, 
            text=f"{group_label} ({len(statements)} statements)", 
            font=("Arial", 12, "bold"),
            anchor="w"
        ).pack(side="left", padx=10, pady=5)
        
        # Progress label for this group
        progress_label = ctk.CTkLabel(header_frame, text="Initializing...", anchor="e")
        progress_label.pack(side="right", padx=10, pady=5)
        
        # Content frame
        content_frame = ctk.CTkFrame(group_frame)
        content_frame.pack(fill="x", pady=5, padx=10, expand=True)
        
        # Text display for details
        details_text = ctk.CTkTextbox(content_frame, height=80, wrap="word")
        details_text.pack(fill="x", pady=5, expand=True)
        details_text.insert("1.0", "Processing group...")
        details_text.configure(state="disabled")
        
        # Result frame for the winning statement
        result_frame = ctk.CTkFrame(group_frame)
        
        # Store these widgets for later updates
        group_frame.progress_label = progress_label
        group_frame.details_text = details_text
        group_frame.result_frame = result_frame
        
        # Save the frame for later reference by level and group index
        key = f"level{level}_group{group_idx}"
        if not hasattr(self, 'recursive_group_frames'):
            self.recursive_group_frames = {}
        self.recursive_group_frames[key] = group_frame
        
        return group_frame
    
    def update_recursive_group_progress(self, level, group_idx, progress_text, details_text):
        """Update the progress display for a group"""
        key = f"level{level}_group{group_idx}"
        if hasattr(self, 'recursive_group_frames') and key in self.recursive_group_frames:
            group_frame = self.recursive_group_frames[key]
            
            # Update progress label
            group_frame.progress_label.configure(text=progress_text)
            
            # Update details text
            group_frame.details_text.configure(state="normal")
            group_frame.details_text.delete("1.0", "end")
            group_frame.details_text.insert("1.0", details_text)
            group_frame.details_text.configure(state="disabled")
    
    def update_recursive_group_result(self, level, group_idx, winning_statement):
        """Update a group with its winning statement"""
        key = f"level{level}_group{group_idx}"
        if hasattr(self, 'recursive_group_frames') and key in self.recursive_group_frames:
            group_frame = self.recursive_group_frames[key]
            
            # Update progress label
            group_frame.progress_label.configure(text="Complete", text_color="green")
            
            # Display the winning statement
            if not group_frame.result_frame.winfo_ismapped():
                group_frame.result_frame.pack(fill="x", pady=5, padx=10)
            
            for widget in group_frame.result_frame.winfo_children():
                widget.destroy()
                
            ctk.CTkLabel(
                group_frame.result_frame, 
                text="Winning Statement:", 
                font=("Arial", 11, "bold"),
                anchor="w"
            ).pack(anchor="w", pady=(5,2))
            
            result_text = ctk.CTkTextbox(group_frame.result_frame, height=60, wrap="word")
            result_text.pack(fill="x", pady=2)
            result_text.insert("1.0", winning_statement)
            result_text.configure(state="disabled")
    
    def display_final_recursive_result(self, final_statement):
        """Display the final result of the recursive process"""
        if not final_statement:
            self.recursive_progress_label.configure(
                text="Process complete, but no final statement was generated.",
                text_color="red"
            )
            return
            
        # Create a frame for the final result
        final_frame = ctk.CTkFrame(self.recursive_results_frame)
        final_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(
            final_frame, 
            text="FINAL CONSENSUS STATEMENT", 
            font=("Arial", 16, "bold")
        ).pack(pady=5)
        
        # Update progress label
        self.recursive_progress_label.configure(
            text="Recursive Habermas Machine completed successfully!",
            text_color="green"
        )
        
        # Display the final statement
        final_text = ctk.CTkTextbox(final_frame, height=200, wrap="word")
        final_text.pack(fill="both", expand=True, pady=10, padx=10)
        final_text.insert("1.0", final_statement)
        
        # Stay on the recursive results tab
        self.results_tabview.set("Recursive Results")

def main():
    try:
        root = ctk.CTk()
        root.protocol("WM_DELETE_WINDOW", lambda: (root.quit(), root.destroy()))
        app = HabermasMachine(root)
        root.mainloop()
    except Exception as e:
        # Create basic error window if initialization fails
        error_root = tk.Tk()
        error_root.title("Error")
        error_root.geometry("600x400")
        error_root.configure(bg="#2b2b2b")
        
        tk.Label(
            error_root, 
            text="Error Starting Habermas Machine", 
            font=("Arial", 16, "bold"),
            bg="#2b2b2b",
            fg="#ffffff"
        ).pack(pady=20)
        
        error_text = tk.Text(error_root, height=15, width=70, bg="#1e1e1e", fg="#ffffff")
        error_text.pack(pady=10, padx=20)
        
        error_traceback = traceback.format_exc()
        error_text.insert("1.0", f"Error: {str(e)}\n\nTraceback:\n{error_traceback}")
        
        tk.Label(
            error_root,
            text="Check that Ollama is running and all dependencies are installed.",
            bg="#2b2b2b",
            fg="#ffffff"
        ).pack(pady=10)
        
        tk.Button(
            error_root,
            text="Close",
            command=error_root.destroy,
            bg="#454545",
            fg="#ffffff"
        ).pack(pady=10)
        
        error_root.mainloop()

if __name__ == "__main__":
    main()
