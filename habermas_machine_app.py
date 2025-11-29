"""
Habermas Machine - AI-Assisted Consensus Builder

Copyright (C) 2025  Habermas Machine Project

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import tkinter as tk
import tkinter.messagebox as messagebox
import traceback
import sys
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='habermas_machine.log',
    filemode='w'
)
logger = logging.getLogger('habermas_machine')

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
    import datetime
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

# Try importing the new model management system
try:
    from habermas_machine.core import (
        create_manager_from_preset,
        generate_opinion_only_cot_prompt,
        ModelManager,
        PROMPTED_DEEPSEEK,
        PROMPTED_LLAMA,
        PROMPTED_QWEN,
    )
    from habermas_machine.data.sample_statements import COMPULSORY_VOTING_OPINIONS
    MODEL_MANAGEMENT_AVAILABLE = True
    logger.info("Model management system loaded successfully")
except ImportError as e:
    MODEL_MANAGEMENT_AVAILABLE = False
    logger.warning(f"Model management system not available: {e}")
    logger.warning("Continuing with legacy mode")

class HabermasMachine:
    def __init__(self, root):
        self.root = root
        title = "Habermas Machine - AI-Assisted Consensus Builder"
        if MODEL_MANAGEMENT_AVAILABLE:
            title += " v2.0 (Enhanced)"
        self.root.title(title)
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

        # Model management (new)
        self.model_manager = None
        self.use_model_management = MODEL_MANAGEMENT_AVAILABLE
        self.current_preset = "prompted_deepseek" if MODEL_MANAGEMENT_AVAILABLE else None
        
        # Default prompt templates
        self.default_templates = {
            "candidate_generation": "Given these participant statements, please combine these statements into a single group statement that synthesizes their viewpoints and includes all their individual points and concerns. This should represent a fair consensus or position that most participants could accept, and be representative of all details, concerns, suggestions, or questions from all participants, even if that make the combined statement longer. Your response will be used verbatim as the statement, so do not include any preamble or postscript.\n\n"
                                  "---\n\n# {question}\n\n"
                                  "---\n\n{participant_statements}\n\n---\n\n",
            
            "ranking_prediction": "Given this participant's statement, predict how this participant would rank these group statements from most preferred (1) to least preferred ({num_candidates}).\n\n\n\n"
                                "# {question}\n\n"
                                "## Participant's original statement: {participant_statement}\n\n"
                                "## Group Statements to Rank:\n\n"
                                "{candidate_statements}\n\n\n\n"
                                """Based on the participant's original statement, predict their ranking of these group statements from most preferred to least preferred as a JSON object:\n\n{{\n  "ranking": [1, 2, etc.]\n}}\n\nImportant: Your response MUST contain ONLY a valid JSON object with a list of positive integer rankings under the key "ranking", NOT a list of statements, and must align with how this participant would rank them; e.g. how aligned they are with this participant's stance and priorities. Index starts at 1, not 0."""
        }
        
        # Create templates that will be edited
        self.prompt_templates = self.default_templates.copy()
        
        # Create main layout
        self.create_layout()
        
        # Configure default values
        if MODEL_MANAGEMENT_AVAILABLE:
            # Use preset defaults (silent during init)
            self.apply_preset("prompted_deepseek", silent=True)
        else:
            # Legacy defaults - now using new separate variables
            self.gen_model_var.set("deepseek-r1:14b")
            self.rank_model_var.set("deepseek-r1:14b")
            self.gen_temperature_var.set("0.7")
            self.rank_temperature_var.set("0.6")

        self.gen_top_p_var.set("0.9")
        self.gen_top_k_var.set("40")
        self.max_retries_var.set("3")  # Default for retries
        self.max_group_size_var.set("12")  # Default max group size
        self.num_candidates_var.set("4")  # Default number of candidates
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
        
        # Set up the left column (settings & inputs)
        self.setup_left_column()
        
        # Set up the middle column (results)
        self.setup_middle_column()
        
        # Set up the right column (debug)
        self.setup_right_column()
    
    def setup_left_column(self):
        # Configure the left column to expand
        self.left_column.grid_columnconfigure(0, weight=1)
        self.left_column.grid_rowconfigure(0, weight=1)
        
        # Create a tabview for the left column (Settings, Inputs)
        self.left_tabview = ctk.CTkTabview(self.left_column)
        self.left_tabview.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Add tabs for the left column
        self.left_tabview.add("Inputs")
        self.left_tabview.add("Settings")
        self.left_tabview.add("Templates")
        
        # Make sure each tab can expand
        for tab_name in ["Inputs", "Settings", "Templates"]:
            self.left_tabview.tab(tab_name).grid_columnconfigure(0, weight=1)
            self.left_tabview.tab(tab_name).grid_rowconfigure(0, weight=1)
        
        # Setup the Inputs tab (question, participants)
        self.setup_inputs_tab()
        
        # Setup the Settings tab (model, parameters)
        self.setup_settings_tab()
        
        # Setup the Templates tab (prompt templates)
        self.setup_templates_tab()
    
    def setup_inputs_tab(self):
        # Configure grid for the Inputs tab
        inputs_tab = self.left_tabview.tab("Inputs")
        inputs_tab.grid_columnconfigure(0, weight=1)
        inputs_tab.grid_rowconfigure(0, weight=0)  # Question - fixed height
        inputs_tab.grid_rowconfigure(1, weight=1)  # Participants - expandable
        inputs_tab.grid_rowconfigure(2, weight=0)  # Buttons - fixed height
        
        # Question section - fixed height
        question_frame = ctk.CTkFrame(inputs_tab)
        question_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        question_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(question_frame, text="Question:", anchor="w", font=("Arial", 12, "bold")).pack(fill="x", padx=10, pady=(5, 2))
        self.question_text = ctk.CTkTextbox(question_frame, height=60, font=("Arial", 12))
        self.question_text.pack(fill="x", padx=10, pady=(0, 5))
        
        # Participants section - this should expand to fill space
        participants_frame = ctk.CTkFrame(inputs_tab)
        participants_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        participants_frame.grid_columnconfigure(0, weight=1)
        participants_frame.grid_rowconfigure(1, weight=1)  # Make the textbox row expandable
        
        # Participants header
        participants_header = ctk.CTkFrame(participants_frame)
        participants_header.grid(row=0, column=0, sticky="ew", padx=0, pady=(5, 2))
        participants_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(participants_header, text="Participant Statements (one per line):", anchor="w", font=("Arial", 12, "bold")).pack(side="left", fill="x", padx=5)
        self.participant_count_label = ctk.CTkLabel(participants_header, text="Count: 0", width=100)
        self.participant_count_label.pack(side="right", padx=5)
        
        # Create the participants textbox - in a separate row that can expand
        self.participants_text = ctk.CTkTextbox(participants_frame, wrap="word", font=("Arial", 12))
        self.participants_text.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0, 5))
        
        # Add text changed callback to update participant count
        self.participants_text.bind("<KeyRelease>", self.update_participant_count)
        
        # Buttons section - fixed height
        self.buttons_frame = ctk.CTkFrame(inputs_tab)
        self.buttons_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        self.generate_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Generate Consensus (Single Run)",
            command=self.start_generation,
            font=("Arial", 12)
        )
        self.generate_btn.pack(side="left", padx=10, pady=10)
        
        # Button for recursive generation
        self.recursive_generate_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Recursive Consensus Builder",
            command=self.start_recursive_generation,
            fg_color="#1f5d3c",  # Dark green
            font=("Arial", 12)
        )
        self.recursive_generate_btn.pack(side="left", padx=10, pady=10)
        
        # Add bulk import button
        bulk_import_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Bulk Import",
            command=self.bulk_import,
            fg_color="#3d7e9a",  # Blue color
            font=("Arial", 12)
        )
        bulk_import_btn.pack(side="left", padx=10, pady=10)
        
        self.stop_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Stop",
            command=self.stop_generation,
            fg_color="darkred",
            font=("Arial", 12)
        )
        self.stop_btn.pack(side="right", padx=10, pady=10)
    
    def setup_settings_tab(self):
        # Create a scrollable frame for settings
        settings_frame = ctk.CTkScrollableFrame(self.left_tabview.tab("Settings"))
        settings_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Model Management Section (NEW!)
        if MODEL_MANAGEMENT_AVAILABLE:
            model_mgmt_frame = ctk.CTkFrame(settings_frame)
            model_mgmt_frame.pack(fill="x", pady=10, padx=5)

            ctk.CTkLabel(
                model_mgmt_frame,
                text="🎯 Model Configuration (v2.0)",
                font=("Arial", 14, "bold")
            ).pack(pady=5)

            # Preset selector
            preset_frame = ctk.CTkFrame(model_mgmt_frame)
            preset_frame.pack(fill="x", padx=10, pady=5)

            ctk.CTkLabel(preset_frame, text="Preset:", font=("Arial", 12, "bold")).pack(side="left", padx=10)

            self.preset_var = ctk.StringVar(value="prompted_deepseek")
            preset_menu = ctk.CTkOptionMenu(
                preset_frame,
                variable=self.preset_var,
                values=["prompted_deepseek", "prompted_llama", "prompted_qwen", "custom"],
                command=self.on_preset_changed,
                width=200,
                font=("Arial", 12)
            )
            preset_menu.pack(side="left", padx=10, fill="x", expand=True)

            # Preset description
            self.preset_description = ctk.CTkLabel(
                model_mgmt_frame,
                text="DeepSeek-R1 14B (Recommended) - Optimal batching, minimal model loading",
                font=("Arial", 10),
                wraplength=400,
                text_color="gray70"
            )
            self.preset_description.pack(pady=5, padx=10)

            # Use DeepMind Prompts option
            self.use_deepmind_prompts_var = ctk.BooleanVar(value=False)
            deepmind_check = ctk.CTkCheckBox(
                model_mgmt_frame,
                text="📚 Use DeepMind Chain-of-Thought Prompts (Experimental)",
                variable=self.use_deepmind_prompts_var,
                command=self.on_deepmind_prompts_changed,
                font=("Arial", 11)
            )
            deepmind_check.pack(pady=5, padx=10, anchor="w")

            # Show statistics option
            self.show_stats_var = ctk.BooleanVar(value=True)
            stats_check = ctk.CTkCheckBox(
                model_mgmt_frame,
                text="📊 Show Performance Statistics",
                variable=self.show_stats_var,
                font=("Arial", 11)
            )
            stats_check.pack(pady=2, padx=10, anchor="w")

            # Separator
            separator = ctk.CTkFrame(settings_frame, height=2, fg_color="gray30")
            separator.pack(fill="x", pady=10, padx=5)

        # === API Configuration Info ===
        api_info_frame = ctk.CTkFrame(settings_frame)
        api_info_frame.pack(fill="x", pady=5, padx=5)

        info_text = "💡 Configure separate API endpoints and models for statement generation vs. ranking prediction.\nSupports OpenAI-compatible APIs (Ollama, LM Studio, vLLM, etc.)"
        ctk.CTkLabel(
            api_info_frame,
            text=info_text,
            font=("Arial", 10),
            text_color="gray70",
            wraplength=500,
            justify="left"
        ).pack(pady=5, padx=10)

        # === GENERATION API SETTINGS ===
        gen_api_frame = ctk.CTkFrame(settings_frame)
        gen_api_frame.pack(fill="x", pady=10, padx=5)

        ctk.CTkLabel(gen_api_frame, text="🔧 Statement Generation API", font=("Arial", 14, "bold")).pack(pady=5)

        # Generation API endpoint
        gen_endpoint_frame = ctk.CTkFrame(gen_api_frame)
        gen_endpoint_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(gen_endpoint_frame, text="API Endpoint:", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        self.gen_api_endpoint_var = ctk.StringVar(value="http://localhost:11434/api/generate")
        self.gen_api_endpoint_entry = ctk.CTkEntry(gen_endpoint_frame, textvariable=self.gen_api_endpoint_var, width=350, font=("Arial", 11))
        self.gen_api_endpoint_entry.pack(side="left", padx=10, fill="x", expand=True)

        # Generation model
        gen_model_frame = ctk.CTkFrame(gen_api_frame)
        gen_model_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(gen_model_frame, text="Model:", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        self.gen_model_var = ctk.StringVar()
        self.gen_model_entry = ctk.CTkEntry(gen_model_frame, textvariable=self.gen_model_var, width=200, font=("Arial", 12))
        self.gen_model_entry.pack(side="left", padx=10, fill="x", expand=True)

        # Generation parameters
        gen_params_grid = ctk.CTkFrame(gen_api_frame)
        gen_params_grid.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(gen_params_grid, text="Temperature:", font=("Arial", 11)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.gen_temperature_var = ctk.StringVar()
        self.gen_temperature_entry = ctk.CTkEntry(gen_params_grid, textvariable=self.gen_temperature_var, width=60, font=("Arial", 11))
        self.gen_temperature_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(gen_params_grid, text="Top P:", font=("Arial", 11)).grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.gen_top_p_var = ctk.StringVar()
        self.gen_top_p_entry = ctk.CTkEntry(gen_params_grid, textvariable=self.gen_top_p_var, width=60, font=("Arial", 11))
        self.gen_top_p_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(gen_params_grid, text="Top K:", font=("Arial", 11)).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.gen_top_k_var = ctk.StringVar()
        self.gen_top_k_entry = ctk.CTkEntry(gen_params_grid, textvariable=self.gen_top_k_var, width=60, font=("Arial", 11))
        self.gen_top_k_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(gen_params_grid, text="Candidate Statements:", font=("Arial", 11)).grid(row=1, column=2, padx=10, pady=5, sticky="w")
        self.num_candidates_var = ctk.StringVar()
        self.num_candidates_spinbox = ctk.CTkEntry(gen_params_grid, textvariable=self.num_candidates_var, width=60, font=("Arial", 11))
        self.num_candidates_spinbox.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        # Separator
        separator1 = ctk.CTkFrame(settings_frame, height=2, fg_color="gray30")
        separator1.pack(fill="x", pady=10, padx=5)

        # === RANKING API SETTINGS ===
        rank_api_frame = ctk.CTkFrame(settings_frame)
        rank_api_frame.pack(fill="x", pady=10, padx=5)

        ctk.CTkLabel(rank_api_frame, text="🎯 Ranking Prediction API", font=("Arial", 14, "bold")).pack(pady=5)

        # Ranking API endpoint
        rank_endpoint_frame = ctk.CTkFrame(rank_api_frame)
        rank_endpoint_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(rank_endpoint_frame, text="API Endpoint:", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        self.rank_api_endpoint_var = ctk.StringVar(value="http://localhost:11434/api/generate")
        self.rank_api_endpoint_entry = ctk.CTkEntry(rank_endpoint_frame, textvariable=self.rank_api_endpoint_var, width=350, font=("Arial", 11))
        self.rank_api_endpoint_entry.pack(side="left", padx=10, fill="x", expand=True)

        # Ranking model
        rank_model_frame = ctk.CTkFrame(rank_api_frame)
        rank_model_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(rank_model_frame, text="Model:", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        self.rank_model_var = ctk.StringVar()
        self.rank_model_entry = ctk.CTkEntry(rank_model_frame, textvariable=self.rank_model_var, width=200, font=("Arial", 12))
        self.rank_model_entry.pack(side="left", padx=10, fill="x", expand=True)

        # Ranking parameters
        rank_params_grid = ctk.CTkFrame(rank_api_frame)
        rank_params_grid.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(rank_params_grid, text="Temperature:", font=("Arial", 11)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.rank_temperature_var = ctk.StringVar()
        self.rank_temperature_entry = ctk.CTkEntry(rank_params_grid, textvariable=self.rank_temperature_var, width=60, font=("Arial", 11))
        self.rank_temperature_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(rank_params_grid, text="Max JSON Retries:", font=("Arial", 11)).grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.max_retries_var = ctk.StringVar()
        self.max_retries_entry = ctk.CTkEntry(rank_params_grid, textvariable=self.max_retries_var, width=60, font=("Arial", 11))
        self.max_retries_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Keep legacy variables for backward compatibility (point to new vars)
        self.model_var = self.gen_model_var  # Legacy compatibility
        self.temperature_var = self.gen_temperature_var  # Legacy compatibility
        self.ranking_temperature_var = self.rank_temperature_var  # Legacy compatibility
        self.top_p_var = self.gen_top_p_var  # Legacy compatibility
        self.top_k_var = self.gen_top_k_var  # Legacy compatibility

        # Separator
        separator2 = ctk.CTkFrame(settings_frame, height=2, fg_color="gray30")
        separator2.pack(fill="x", pady=10, padx=5)
        
        # Recursive Habermas settings
        recursive_frame = ctk.CTkFrame(settings_frame)
        recursive_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(recursive_frame, text="Recursive Consensus Settings", font=("Arial", 14, "bold")).pack(pady=5)
        
        recursive_grid = ctk.CTkFrame(recursive_frame)
        recursive_grid.pack(fill="x", padx=10, pady=5, expand=True)
        
        # Max group size
        ctk.CTkLabel(recursive_grid, text="Max Group Size:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.max_group_size_var = ctk.StringVar()
        self.max_group_size_entry = ctk.CTkEntry(recursive_grid, textvariable=self.max_group_size_var, width=60, font=("Arial", 12))
        self.max_group_size_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Voting strategy
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
        
        # Output options
        output_frame = ctk.CTkFrame(settings_frame)
        output_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(output_frame, text="Output Options", font=("Arial", 14, "bold")).pack(pady=5)
        
        output_options = ctk.CTkFrame(output_frame)
        output_options.pack(fill="x", padx=10, pady=5)
        
        # Save output option
        self.save_output_var = ctk.BooleanVar(value=True)
        save_output_check = ctk.CTkCheckBox(
            output_options, 
            text="Save results to file", 
            variable=self.save_output_var,
            font=("Arial", 12)
        )
        save_output_check.pack(anchor="w", pady=5)
        
        # Template reset buttons section
        reset_frame = ctk.CTkFrame(settings_frame)
        reset_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(reset_frame, text="Reset Templates", font=("Arial", 14, "bold")).pack(pady=5)
        
        reset_buttons = ctk.CTkFrame(reset_frame)
        reset_buttons.pack(fill="x", padx=10, pady=5)
        
        reset_candidate_btn = ctk.CTkButton(
            reset_buttons,
            text="Reset Candidate Template",
            command=lambda: self.reset_template("candidate_generation"),
            font=("Arial", 12)
        )
        reset_candidate_btn.pack(side="left", padx=10, pady=5)
        
        reset_ranking_btn = ctk.CTkButton(
            reset_buttons,
            text="Reset Ranking Template",
            command=lambda: self.reset_template("ranking_prediction"),
            font=("Arial", 12)
        )
        reset_ranking_btn.pack(side="left", padx=10, pady=5)
        
        reset_all_btn = ctk.CTkButton(
            reset_buttons,
            text="Reset All Templates",
            command=self.reset_all_templates,
            font=("Arial", 12)
        )
        reset_all_btn.pack(side="left", padx=10, pady=5)
    
    def setup_templates_tab(self):
        # Create a scrollable frame for templates
        templates_frame = ctk.CTkScrollableFrame(self.left_tabview.tab("Templates"))
        templates_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Candidate generation template
        ctk.CTkLabel(templates_frame, text="Candidate Generation Template:", anchor="w", font=("Arial", 12, "bold")).pack(fill="x", padx=10, pady=(10, 5))
        self.candidate_template_text = ctk.CTkTextbox(templates_frame, height=200, wrap="word", font=("Arial", 12))
        self.candidate_template_text.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(templates_frame, text="Available placeholders: {question}, {participant_statements}", anchor="w").pack(fill="x", padx=10, pady=(0, 10))
        
        # Ranking prediction template
        ctk.CTkLabel(templates_frame, text="Ranking Prediction Template:", anchor="w", font=("Arial", 12, "bold")).pack(fill="x", padx=10, pady=(10, 5))
        self.ranking_template_text = ctk.CTkTextbox(templates_frame, height=200, wrap="word", font=("Arial", 12))
        self.ranking_template_text.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(templates_frame, text="Available placeholders: {question}, {participant_num}, {participant_statement}, {num_candidates}, {candidate_statements}", anchor="w").pack(fill="x", padx=10, pady=(0, 10))
        
        # Save template changes button
        save_btn = ctk.CTkButton(
            templates_frame,
            text="Save Template Changes",
            command=self.save_templates,
            font=("Arial", 12)
        )
        save_btn.pack(padx=10, pady=10)
    
    def setup_middle_column(self):
        # For the middle column (results), we'll use a tabview to separate different views
        self.results_tabview = ctk.CTkTabview(self.middle_column)
        self.results_tabview.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add tabs for different types of output
        self.results_tabview.add("Friendly Output")
        self.results_tabview.add("Detailed Records")
        
        # Setup the Friendly Output tab
        self.setup_friendly_output_tab()
        
        # Setup the Detailed Records tab
        self.setup_detailed_records_tab()
    
    def setup_friendly_output_tab(self):
        # Create a frame for the friendly output tab
        friendly_frame = ctk.CTkFrame(self.results_tabview.tab("Friendly Output"))
        friendly_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Make sure the frame will expand properly
        friendly_frame.grid_columnconfigure(0, weight=1)
        friendly_frame.grid_rowconfigure(1, weight=1)
        
        # Header with status
        header_frame = ctk.CTkFrame(friendly_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ctk.CTkLabel(header_frame, text="Consensus Builder Results", font=("Arial", 16, "bold")).pack(side="left", padx=10, pady=5)
        
        self.friendly_status_var = ctk.StringVar(value="Ready")
        status_label = ctk.CTkLabel(header_frame, textvariable=self.friendly_status_var, font=("Arial", 12))
        status_label.pack(side="right", padx=10, pady=5)
        
        # Create the friendly output textbox
        self.friendly_output = ctk.CTkTextbox(friendly_frame, wrap="word", font=("Arial", 12))
        self.friendly_output.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Add a save button for the output
        self.save_friendly_btn = ctk.CTkButton(
            friendly_frame,
            text="Save Results",
            command=lambda: self.save_output("friendly"),
            font=("Arial", 12)
        )
        self.save_friendly_btn.grid(row=2, column=0, sticky="e", padx=10, pady=10)
    
    def setup_detailed_records_tab(self):
        # Create a frame for the detailed records tab
        detailed_frame = ctk.CTkFrame(self.results_tabview.tab("Detailed Records"))
        detailed_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Make sure the frame will expand properly
        detailed_frame.grid_columnconfigure(0, weight=1)
        detailed_frame.grid_rowconfigure(1, weight=1)
        
        # Header with info
        header_frame = ctk.CTkFrame(detailed_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ctk.CTkLabel(header_frame, text="Complete Process Record", font=("Arial", 16, "bold")).pack(side="left", padx=10, pady=5)
        
        self.detailed_status_var = ctk.StringVar(value="Ready")
        status_label = ctk.CTkLabel(header_frame, textvariable=self.detailed_status_var, font=("Arial", 12))
        status_label.pack(side="right", padx=10, pady=5)
        
        # Create the detailed records textbox
        self.detailed_output = ctk.CTkTextbox(detailed_frame, wrap="word", font=("Arial", 12))
        self.detailed_output.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Add a save button for the detailed records
        self.save_detailed_btn = ctk.CTkButton(
            detailed_frame,
            text="Save Detailed Record",
            command=lambda: self.save_output("detailed"),
            font=("Arial", 12)
        )
        self.save_detailed_btn.grid(row=2, column=0, sticky="e", padx=10, pady=10)
    
    def setup_right_column(self):
        # Debug frames with more space
        self.right_column.grid_rowconfigure(0, weight=1)
        self.right_column.grid_rowconfigure(1, weight=1)
        self.right_column.grid_columnconfigure(0, weight=1)
        
        # Debug prompt panel
        prompt_frame = ctk.CTkFrame(self.right_column)
        prompt_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        prompt_frame.pack_propagate(False)
        
        prompt_frame.grid_rowconfigure(1, weight=1)
        prompt_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(prompt_frame, text="Current Prompt", font=("Arial", 14, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.prompt_text = ctk.CTkTextbox(prompt_frame, wrap="word", font=("Arial", 12))
        self.prompt_text.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Debug response panel
        response_frame = ctk.CTkFrame(self.right_column)
        response_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        response_frame.pack_propagate(False)
        
        response_frame.grid_rowconfigure(1, weight=1)
        response_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(response_frame, text="Current Response", font=("Arial", 14, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.response_text = ctk.CTkTextbox(response_frame, wrap="word", font=("Arial", 12))
        self.response_text.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
    
    def update_participant_count(self, event=None):
        """Update the participant count label based on the number of non-empty lines"""
        text = self.participants_text.get("1.0", "end-1c")
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        self.participant_count_label.configure(text=f"Count: {len(lines)}")
    
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
    
    def save_output(self, output_type):
        """Save the output to a file"""
        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)

        # Default file types and initial filename
        if output_type == "friendly":
            filetypes = [("Text files", "*.txt"), ("Markdown files", "*.md"), ("All files", "*.*")]
            initial_filename = f"habermas_results_{self.session_id}.md"
            content = self.friendly_output.get("1.0", "end-1c")
        else:  # detailed
            filetypes = [("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
            initial_filename = f"habermas_detailed_{self.session_id}.md"
            content = self.detailed_output.get("1.0", "end-1c")

        # Ask user where to save (suggest output directory)
        file_path = ctk.filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=filetypes,
            initialfile=initial_filename,
            initialdir="output"
        )
        
        if not file_path:
            return  # User canceled
        
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            messagebox.showinfo("Save Successful", f"Results successfully saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving file: {str(e)}")
            logger.error(f"Error saving file: {str(e)}")
    
    def start_generation(self):
        """Start the single-run consensus generation process"""
        self.stop_event.clear()
        
        # Collect participant statements
        self.participant_statements = self.get_participant_statements()
        
        if len(self.participant_statements) < 2:
            messagebox.showerror("Error", "Please provide at least 2 participant statements.")
            return
        
        # Clear previous outputs
        self.friendly_output.delete("1.0", "end")
        self.detailed_output.delete("1.0", "end")
        
        # Set status
        self.friendly_status_var.set("Generating...")
        self.detailed_status_var.set("Generating...")
        
        # Generate a unique session ID
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Disable buttons during generation
        self.generate_btn.configure(state="disabled")
        self.recursive_generate_btn.configure(state="disabled")
        
        # Start generation thread
        Thread(target=self.run_single_consensus, daemon=True).start()
    
    def run_single_consensus(self):
        """Run a single consensus generation process"""
        try:
            question = self.question_text.get("1.0", "end-1c").strip()
            
            # Initial log entries
            self.log_to_friendly(f"# Consensus Builder Results\n\n")
            self.log_to_friendly(f"**Question:** {question}\n\n")
            self.log_to_friendly("## Original Participant Statements\n\n")
            
            # Log detailed records header
            self.log_to_detailed(f"# Consensus Process Detailed Record\n\n")
            self.log_to_detailed(f"**Session ID:** {self.session_id}  \n")
            self.log_to_detailed(f"**Time:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
            self.log_to_detailed(f"**Generation Model:** {self.gen_model_var.get()} @ {self.gen_api_endpoint_var.get()}\n")
            self.log_to_detailed(f"**Ranking Model:** {self.rank_model_var.get()} @ {self.rank_api_endpoint_var.get()}\n")
            self.log_to_detailed(f"**Process Type:** Single-run Consensus  \n\n")
            self.log_to_detailed(f"## Question\n\n{question}\n\n")
            self.log_to_detailed("## Original Participant Statements\n\n")
            
            # Log participant statements
            for i, statement in enumerate(self.participant_statements):
                self.log_to_friendly(f"**Participant {i+1}:**  \n{statement}\n\n")
                self.log_to_detailed(f"**Participant {i+1}:**  \n{statement}\n\n")
            
            # Generate candidate statements
            self.log_to_friendly("## Generating Candidate Statements...\n\n")
            self.log_to_detailed("## Candidate Statement Generation\n\n")
            
            # Generate candidates
            self.candidate_statements = self.generate_candidate_statements(question)
            
            if self.stop_event.is_set():
                self.cleanup_after_process()
                return
            
            if not self.candidate_statements:
                self.log_to_friendly("**Error:** Failed to generate any candidate statements. See error details above.\n\n")
                self.log_to_detailed("**Error:** Failed to generate any candidate statements. Check individual candidate generation errors above.\n\n")
                self.cleanup_after_process()
                return
            
            # Display the candidates
            self.log_to_friendly("### Candidate Statements\n\n")
            self.log_to_detailed("### Generated Candidate Statements\n\n")
            
            for i, candidate in enumerate(self.candidate_statements):
                self.log_to_friendly(f"**Candidate {i+1}:**  \n{candidate}\n\n")
                self.log_to_detailed(f"**Candidate {i+1}:**  \n{candidate}\n\n")
            
            # Run election simulation
            self.log_to_friendly("## Simulating Election...\n\n")
            self.log_to_detailed("## Election Simulation\n\n")
            
            # Do election simulation
            winner_idx, rankings, pairwise_matrix, strongest_paths = self.run_election_simulation(question)
            
            if self.stop_event.is_set() or winner_idx is None:
                self.cleanup_after_process()
                return
            
            # Get winning statement
            winning_statement = self.candidate_statements[winner_idx]
            
            # Display the winning statement at the top for visibility
            self.root.after(0, lambda: self.update_friendly_output_with_winner(winning_statement))
            
            # Log the election results
            self.log_election_results(winner_idx, rankings, pairwise_matrix, strongest_paths)
            
            # Auto save if enabled
            if self.save_output_var.get():
                try:
                    # Create output directory if it doesn't exist
                    os.makedirs("output", exist_ok=True)

                    # Save friendly output
                    friendly_path = os.path.join("output", f"habermas_results_{self.session_id}.md")
                    with open(friendly_path, 'w', encoding='utf-8') as file:
                        file.write(self.friendly_output.get("1.0", "end-1c"))

                    # Save detailed output
                    detailed_path = os.path.join("output", f"habermas_detailed_{self.session_id}.md")
                    with open(detailed_path, 'w', encoding='utf-8') as file:
                        file.write(self.detailed_output.get("1.0", "end-1c"))

                    self.log_to_friendly(f"\n\n*Results automatically saved to {friendly_path}*\n")
                    self.log_to_detailed(f"\n\n*Detailed record automatically saved to {detailed_path}*\n")
                except Exception as e:
                    self.log_to_friendly(f"\n\n*Failed to auto-save results: {str(e)}*\n")
                    logger.error(f"Auto-save error: {str(e)}")
            
            # Set status to complete
            self.root.after(0, lambda: self.friendly_status_var.set("Complete"))
            self.root.after(0, lambda: self.detailed_status_var.set("Complete"))
            
        except Exception as e:
            error_msg = f"Error in consensus process: {str(e)}"
            self.log_to_friendly(f"\n\n**Error:** {error_msg}\n")
            self.log_to_detailed(f"\n\n**Error:** {error_msg}\n\nStacktrace:\n```\n{traceback.format_exc()}\n```\n")
            logger.error(error_msg, exc_info=True)
        
        finally:
            self.cleanup_after_process()
    
    def generate_candidate_statements(self, question):
        """Generate candidate consensus statements"""
        try:
            num_candidates = min(9, max(2, int(self.num_candidates_var.get())))
        except ValueError:
            num_candidates = 4
            self.num_candidates_var.set("4")
        
        self.log_to_detailed(f"Generating {num_candidates} candidate statements\n\n")
        
        candidates = []
        for i in range(num_candidates):
            if self.stop_event.is_set():
                break
                
            # Randomize the order of participant statements for each candidate
            shuffled_statements = self.participant_statements.copy()
            random.shuffle(shuffled_statements)
            
            self.log_to_detailed(f"### Generating Candidate {i+1}\n\n")
            
            # Generate the candidate statement
            candidate = self.generate_single_candidate(question, shuffled_statements, i+1)
            
            if candidate and not self.stop_event.is_set():
                candidates.append(candidate)
                self.log_to_friendly(f"Candidate {i+1} generated...\n")
        
        return candidates
    
    def generate_single_candidate(self, question, statements, candidate_num):
        """Generate a single candidate statement"""
        # Prepare participant statements text
        participant_statements_text = ""
        for i, statement in enumerate(statements):
            participant_statements_text += f"- {statement}\n\n"
        
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
        
        # Prepare API call parameters - use generation-specific settings
        model = self.gen_model_var.get()
        api_endpoint = self.gen_api_endpoint_var.get()
        try:
            temperature = float(self.gen_temperature_var.get())
            top_p = float(self.gen_top_p_var.get())
            top_k = int(self.gen_top_k_var.get())
        except ValueError:
            temperature = 0.7
            top_p = 0.9
            top_k = 40

        # Make the API call
        try:
            self.current_response = requests.post(
                api_endpoint,
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
                try:
                    error_detail = self.current_response.text
                except:
                    error_detail = "Unable to read error details"
                error_msg = f"API Error: Status code {self.current_response.status_code}\n{error_detail}"
                self.log_to_friendly(f"**Error generating candidate {candidate_num}:** {error_msg}\n\n")
                self.log_to_detailed(f"**Error:** {error_msg}\n\n")
                logger.error(error_msg)
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
                    except json.JSONDecodeError as e:
                        error_msg = f"Failed to decode response from Ollama API: {str(e)}"
                        self.log_to_friendly(f"**Error:** {error_msg}\n\n")
                        self.log_to_detailed(f"**Error:** {error_msg}\n\n")
                
            # Log the response
            self.log_to_detailed(f"**Raw Response for Candidate {candidate_num}:**\n\n```\n{full_response}\n```\n\n")
            
            # Remove the <think>...</think> tag that DeepSeek-R1 may add
            clean_response = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL).strip()
            
            return clean_response
            
        except Exception as e:
            error_msg = f"Error generating candidate {candidate_num}: {str(e)}"
            self.log_to_friendly(f"**Error:** {error_msg}\n\n")
            self.log_to_detailed(f"**Error:** {error_msg}\n\nStacktrace:\n```\n{traceback.format_exc()}\n```\n\n")
            logger.error(error_msg, exc_info=True)
            return None
        finally:
            self.current_response = None
    
    def run_election_simulation(self, question):
        """Simulate an election between candidate statements"""
        num_participants = len(self.participant_statements)
        
        # Initialize simulated rankings
        rankings = {i: [] for i in range(num_participants)}
        
        # Log for JSON ranking attempts
        ranking_attempts_log = []
        
        self.log_to_detailed("### Predicting Participant Rankings\n\n")
        
        # For each participant, predict their rankings
        for p_idx in range(num_participants):
            if self.stop_event.is_set():
                return None, None, None, None
                
            participant_statement = self.participant_statements[p_idx]
            
            self.log_to_detailed(f"**Predicting ranking for Participant {p_idx+1}**\n\n")
            
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
                
                # Log the predicted ranking
                self.log_to_detailed(f"**Predicted ranking:** {[r+1 for r in predicted_ranking]}\n\n")
        
        if self.stop_event.is_set():
            return None, None, None, None
        
        # Calculate winner using the Schulze method
        self.log_to_detailed("### Calculating Winner using Schulze Method\n\n")
        
        winner_idx, pairwise_matrix, strongest_paths = self.schulze_method(rankings, len(self.candidate_statements))
        
        # Log the result
        self.log_to_detailed(f"**Winner calculated:** Candidate {winner_idx+1}\n\n")
        
        return winner_idx, rankings, pairwise_matrix, strongest_paths
    
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
        candidate_statements_text = "\n\n---\n\n"
        for i, statement in enumerate(candidate_statements):
            candidate_statements_text += f"```\nSTATEMENT {i+1}:\n{statement}\n```\n\n"
        
        # Get the template and format it
        template = self.prompt_templates["ranking_prediction"] 
        prompt = template.format(
            question=question,
            participant_num=participant_num,
            participant_statement=participant_statement,
            num_candidates=len(candidate_statements),
            candidate_statements=candidate_statements_text
        )
        
        # Log the prompt to detailed output
        self.log_to_detailed(f"**SYSTEM PROMPT:**\n\n```\n{system_prompt}\n```\n\n")
        self.log_to_detailed(f"**USER PROMPT:**\n\n```\n{prompt}\n```\n\n")
        
        # Update the debug prompt display
        self.root.after(0, lambda: self.update_debug_prompt(f"System prompt:\n{system_prompt}\n\n---\n\nUser prompt:\n{prompt}"))
        
        # Prepare API call parameters - use ranking-specific settings
        model = self.rank_model_var.get()
        api_endpoint = self.rank_api_endpoint_var.get()
        try:
            temperature = float(self.rank_temperature_var.get())
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
                    api_endpoint,
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
                    try:
                        error_detail = self.current_response.text
                    except:
                        error_detail = "Unable to read error details"
                    attempt_error = f"Attempt {attempts}: API Error: Status code {self.current_response.status_code}\n{error_detail}"
                    attempts_log.append(attempt_error)
                    self.log_to_friendly(f"**Ranking prediction error for Participant {participant_num}:** {attempt_error}\n\n")
                    self.log_to_detailed(f"**{attempt_error}**\n\n")
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
                self.log_to_detailed(f"**Attempt {attempts} response:**\n\n```\n{full_response}\n```\n\n")
                
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
                                self.log_to_detailed(f"**Ranking parsed successfully:** {[r+1 for r in ranking]}\n\n")
                                return ranking, attempts_log
                            else:
                                attempts_log.append(f"Attempt {attempts}: Invalid ranking indices: {ranking}")
                                self.log_to_detailed(f"**Invalid ranking indices:** {ranking}\n\n")
                        else:
                            attempts_log.append(f"Attempt {attempts}: JSON missing 'ranking' field or not a list")
                            self.log_to_detailed("**JSON missing 'ranking' field or not a list**\n\n")
                    else:
                        attempts_log.append(f"Attempt {attempts}: No JSON object found in response")
                        self.log_to_detailed("**No JSON object found in response**\n\n")
                
                except json.JSONDecodeError as e:
                    attempts_log.append(f"Attempt {attempts}: JSON parsing error: {str(e)}")
                    self.log_to_detailed(f"**JSON parsing error:** {str(e)}\n\n")
                except Exception as e:
                    attempts_log.append(f"Attempt {attempts}: Error processing response: {str(e)}")
                    self.log_to_detailed(f"**Error processing response:** {str(e)}\n\n")
                
            except Exception as e:
                attempts_log.append(f"Attempt {attempts}: Exception: {str(e)}")
                self.log_to_friendly(f"**Ranking prediction exception for Participant {participant_num}:** {str(e)}\n\n")
                self.log_to_detailed(f"**Exception:** {str(e)}\n\nStacktrace:\n```\n{traceback.format_exc()}\n```\n\n")
            finally:
                self.current_response = None
        
        # If we get here, all attempts failed
        attempts_log.append("All attempts failed. Falling back to random ranking.")
        self.log_to_friendly(f"**Warning:** Failed to predict ranking for Participant {participant_num} after {max_retries} attempts. Using random ranking as fallback.\n\n")
        self.log_to_detailed("**All attempts failed. Falling back to random ranking.**\n\n")
        
        # Fallback to a random ranking
        random_ranking = list(range(len(candidate_statements)))
        random.shuffle(random_ranking)
        return random_ranking, attempts_log
    
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
    
    def log_election_results(self, winner_idx, rankings, pairwise_matrix, strongest_paths):
        """Log the results of the election simulation"""
        # Log winner to friendly output
        self.log_to_friendly("## Election Results\n\n")
        self.log_to_friendly(f"The winning statement was **Candidate {winner_idx+1}**\n\n")
        self.log_to_friendly("### How the Winner Was Determined\n\n")
        self.log_to_friendly(
            "The consensus was determined using the Schulze method, a well-established voting system that "
            "compares how each participant would rank the different statements. This method ensures that "
            "the winning statement is one that is broadly acceptable to all participants, even if it wasn't "
            "everyone's first choice.\n\n"
        )
        
        # Calculate victories for each candidate
        victories = defaultdict(int)
        for i in range(len(self.candidate_statements)):
            for j in range(len(self.candidate_statements)):
                if i != j and strongest_paths[i][j] > strongest_paths[j][i]:
                    victories[i] += 1
        
        # Display statements sorted by Schulze ranking for friendly output
        sorted_statements = sorted(range(len(self.candidate_statements)), 
                                  key=lambda x: victories[x], 
                                  reverse=True)
        
        self.log_to_friendly("### Final Ranking\n\n")
        
        for rank, stmt_idx in enumerate(sorted_statements, 1):
            marker = "🏆 **WINNER**" if stmt_idx == winner_idx else ""
            self.log_to_friendly(f"**Rank {rank}:** Candidate {stmt_idx+1} (defeats {victories[stmt_idx]} other statements) {marker}\n\n")
        
        # For the detailed output, include comprehensive results
        self.log_to_detailed("### Election Results\n\n")
        self.log_to_detailed(f"**Winning statement:** Candidate {winner_idx + 1}\n\n")
        
        # Add Schulze method explanation
        self.log_to_detailed("#### Schulze Method Results\n\n")
        self.log_to_detailed(
            "The Schulze method compares each pair of statements to see which one is preferred by more participants. "
            "For each pair of statements, a 'path strength' is calculated, representing how strongly one "
            "statement is preferred over another considering all possible transitive preferences.\n\n"
        )
        
        # Add information about statement rankings
        self.log_to_detailed("**Statement rankings based on Schulze method:**\n\n")
        
        for rank, stmt_idx in enumerate(sorted_statements, 1):
            marker = "[WINNER]" if stmt_idx == winner_idx else ""
            self.log_to_detailed(f"Rank {rank}: Statement {stmt_idx + 1} (defeats {victories[stmt_idx]} other statements) {marker}\n")
        
        self.log_to_detailed("\n#### Pairwise Preference Matrix\n\n")
        self.log_to_detailed("This matrix shows how many participants preferred statement in row over statement in column:\n\n")
        
        # Header row for preference matrix
        pref_matrix = "|       |"
        for i in range(len(self.candidate_statements)):
            pref_matrix += f" S{i+1:2d} |"
        pref_matrix += "\n|-------|"
        pref_matrix += "-------|" * len(self.candidate_statements)
        pref_matrix += "\n"
        
        # Data rows for preference matrix
        for i in range(len(self.candidate_statements)):
            pref_matrix += f"| S{i+1:2d}  |"
            for j in range(len(self.candidate_statements)):
                if i == j:
                    pref_matrix += "  -  |"
                else:
                    pref_matrix += f" {pairwise_matrix[i][j]:2d}  |"
            pref_matrix += "\n"
        
        self.log_to_detailed(pref_matrix + "\n")
        
        # Strongest paths matrix
        self.log_to_detailed("#### Strongest Paths Matrix\n\n")
        self.log_to_detailed("This matrix shows the strength of the strongest 'path' from row statement to column statement:\n\n")
        
        # Header row for strongest paths
        paths_matrix = "|       |"
        for i in range(len(self.candidate_statements)):
            paths_matrix += f" S{i+1:2d} |"
        paths_matrix += "\n|-------|"
        paths_matrix += "-------|" * len(self.candidate_statements)
        paths_matrix += "\n"
        
        # Data rows for strongest paths
        for i in range(len(self.candidate_statements)):
            paths_matrix += f"| S{i+1:2d}  |"
            for j in range(len(self.candidate_statements)):
                if i == j:
                    paths_matrix += "  -  |"
                else:
                    paths_matrix += f" {strongest_paths[i][j]:2d}  |"
            paths_matrix += "\n"
        
        self.log_to_detailed(paths_matrix + "\n")
        
        # Participant rankings table
        self.log_to_detailed("#### Individual Participant Rankings\n\n")
        self.log_to_detailed("(Lower number = higher preference)\n\n")
        
        # Create a table-like format for participant rankings
        rankings_table = "| Participant |"
        for i in range(len(self.candidate_statements)):
            rankings_table += f" Stmt {i+1} |"
        rankings_table += "\n|------------|"
        rankings_table += "--------|" * len(self.candidate_statements)
        rankings_table += "\n"
        
        # Add each participant's ranking
        for p_idx in sorted(rankings.keys()):
            p_ranking = rankings[p_idx]
            row = f"|     P{p_idx + 1}     |"
            
            # Create ranking display
            for stmt_idx in range(len(self.candidate_statements)):
                if p_ranking and stmt_idx in p_ranking:
                    rank = p_ranking.index(stmt_idx) + 1
                    row += f"   {rank}   |"
                else:
                    row += "   -   |"
            
            rankings_table += row + "\n"
        
        self.log_to_detailed(rankings_table + "\n")
        
        # Add methodology explanation
        self.log_to_detailed("#### Election Methodology\n\n")
        self.log_to_detailed(
            "The election was simulated using the Schulze method, which is a Condorcet voting system. "
            "This method compares each pair of candidates and finds paths of preference between them.\n\n"
            
            "The Schulze method has the following properties:\n"
            "* Independence of clones (similar candidates don't split votes)\n"
            "* Condorcet winner criterion (if a candidate beats all others in pairwise comparisons, they win)\n"
            "* Robustness to strategic voting\n\n"
            
            f"Each participant's ranking was predicted by the '{self.model_var.get()}' model based on their initial statements. "
            "Rankings were extracted from JSON-formatted responses.\n"
        )
    
    def start_recursive_generation(self):
        """Start the recursive consensus generation process"""
        self.stop_event.clear()
        
        # Collect participant statements
        self.participant_statements = self.get_participant_statements()
        
        if len(self.participant_statements) < 2:
            messagebox.showerror("Error", "Please provide at least 2 participant statements.")
            return
        
        # Clear previous outputs
        self.friendly_output.delete("1.0", "end")
        self.detailed_output.delete("1.0", "end")
        
        # Set status
        self.friendly_status_var.set("Generating...")
        self.detailed_status_var.set("Generating...")
        
        # Generate a unique session ID
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Disable buttons during generation
        self.generate_btn.configure(state="disabled")
        self.recursive_generate_btn.configure(state="disabled")
        
        # Start generation thread
        Thread(target=self.run_recursive_consensus, daemon=True).start()
    
    def run_recursive_consensus(self):
        """Run the recursive consensus generation process"""
        try:
            question = self.question_text.get("1.0", "end-1c").strip()
            
            # Get and validate max group size
            try:
                max_group_size = max(2, int(self.max_group_size_var.get()))
            except ValueError:
                max_group_size = 12
                self.max_group_size_var.set("12")
            
            # Get voting strategy
            voting_strategy = self.voting_strategy_var.get()
            
            # Initial log entries for friendly output
            self.log_to_friendly(f"# Recursive Consensus Builder Results\n\n")
            self.log_to_friendly(f"**Question:** {question}\n\n")
            
            friendly_intro = (
                "The Recursive Consensus Builder is working to find common ground among multiple perspectives. "
                "This process works by breaking down large groups into smaller discussion circles, "
                "finding consensus within each circle, and then bringing these sub-consensus positions "
                "together until a final group consensus emerges.\n\n"
                
                f"We're analyzing {len(self.participant_statements)} different perspectives "
                f"with a maximum of {max_group_size} participants per discussion group.\n\n"
            )
            self.log_to_friendly(friendly_intro)
            
            # Log original participant statements
            self.log_to_friendly("## Original Participant Statements\n\n")
            
            # Initial log entries for detailed output
            self.log_to_detailed(f"# Recursive Consensus Process Detailed Record\n\n")
            self.log_to_detailed(f"**Session ID:** {self.session_id}  \n")
            self.log_to_detailed(f"**Time:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
            self.log_to_detailed(f"**Generation Model:** {self.gen_model_var.get()} @ {self.gen_api_endpoint_var.get()}\n")
            self.log_to_detailed(f"**Ranking Model:** {self.rank_model_var.get()} @ {self.rank_api_endpoint_var.get()}\n")
            self.log_to_detailed(f"**Process Type:** Recursive Consensus  \n")
            self.log_to_detailed(f"**Max Group Size:** {max_group_size}  \n")
            self.log_to_detailed(f"**Voting Strategy:** {voting_strategy}  \n\n")
            self.log_to_detailed(f"## Question\n\n{question}\n\n")
            self.log_to_detailed("## Original Participant Statements\n\n")
            
            # Log participant statements
            for i, statement in enumerate(self.participant_statements):
                self.log_to_friendly(f"**Participant {i+1}:**  \n{statement}\n\n")
                self.log_to_detailed(f"**Participant {i+1}:**  \n{statement}\n\n")
            
            # Run the recursive process
            self.log_to_friendly("## Starting Recursive Consensus Process...\n\n")
            self.log_to_detailed("## Recursive Process\n\n")
            
            # Create a data structure to track the recursive process
            process_data = {
                "statements": self.participant_statements.copy(),
                "level": 0,
                "participant_mapping": {}  # Empty mapping for first level (original participants)
            }
            
            # Run the recursive process
            final_statement = self.recursive_habermas_process(
                question, 
                process_data,
                max_group_size,
                voting_strategy
            )
            
            if self.stop_event.is_set():
                self.cleanup_after_process()
                return
                
            if final_statement:
                # Display the final result at the top for visibility
                self.root.after(0, lambda: self.update_friendly_output_with_consensus(final_statement))
                
                # Log the final result
                self.log_to_friendly("\n## Consensus Building Process Complete\n\n")
                self.log_to_friendly(
                    "The recursive process has successfully integrated all perspectives to reach a group consensus. "
                    "The statement above represents a position that best accommodates the diverse viewpoints "
                    "expressed by all participants.\n\n"
                )
                
                self.log_to_detailed("\n## Final Consensus Statement\n\n")
                self.log_to_detailed(f"{final_statement}\n\n")
                self.log_to_detailed(
                    "The recursive consensus process is complete. This final statement represents "
                    "the integration of all participant viewpoints through multiple levels of deliberation.\n\n"
                )
            else:
                self.log_to_friendly("\n## Process Failed\n\n")
                self.log_to_friendly("The consensus building process was unable to complete successfully.\n\n")
                
                self.log_to_detailed("\n## Process Failed\n\n")
                self.log_to_detailed("The recursive consensus process was unable to complete successfully.\n\n")
            
            # Auto save if enabled
            if self.save_output_var.get():
                try:
                    # Create output directory if it doesn't exist
                    os.makedirs("output", exist_ok=True)

                    # Save friendly output
                    friendly_path = os.path.join("output", f"habermas_recursive_results_{self.session_id}.md")
                    with open(friendly_path, 'w', encoding='utf-8') as file:
                        file.write(self.friendly_output.get("1.0", "end-1c"))

                    # Save detailed output
                    detailed_path = os.path.join("output", f"habermas_recursive_detailed_{self.session_id}.md")
                    with open(detailed_path, 'w', encoding='utf-8') as file:
                        file.write(self.detailed_output.get("1.0", "end-1c"))

                    self.log_to_friendly(f"\n\n*Results automatically saved to {friendly_path}*\n")
                    self.log_to_detailed(f"\n\n*Detailed record automatically saved to {detailed_path}*\n")
                except Exception as e:
                    self.log_to_friendly(f"\n\n*Failed to auto-save results: {str(e)}*\n")
                    logger.error(f"Auto-save error: {str(e)}")
            
            # Set status to complete
            self.root.after(0, lambda: self.friendly_status_var.set("Complete"))
            self.root.after(0, lambda: self.detailed_status_var.set("Complete"))
            
        except Exception as e:
            error_msg = f"Error in recursive consensus process: {str(e)}"
            self.log_to_friendly(f"\n\n**Error:** {error_msg}\n")
            self.log_to_detailed(f"\n\n**Error:** {error_msg}\n\nStacktrace:\n```\n{traceback.format_exc()}\n```\n")
            logger.error(error_msg, exc_info=True)
        
        finally:
            self.cleanup_after_process()
    
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
        if self.stop_event.is_set():
            return None
            
        statements = process_data["statements"]
        level = process_data["level"]
        participant_mapping = process_data["participant_mapping"]
        
        # Log the current level
        self.log_to_friendly(f"### Level {level+1} - Processing {len(statements)} statements\n\n")
        self.log_to_detailed(f"### Level {level+1}\n\n")
        self.log_to_detailed(f"Processing {len(statements)} statements\n\n")
        
        # If we have few enough statements to process in one group, do it directly
        if len(statements) <= max_group_size:
            self.log_to_friendly(f"All statements fit in a single group. Processing directly...\n\n")
            self.log_to_detailed(f"All statements fit in a single group. Processing directly.\n\n")
            
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
        self.log_to_detailed(f"Dividing into {len(groups)} groups\n\n")
        
        # Process each group to get winning statements
        winning_statements = []
        new_participant_mapping = {}  # Maps winning statement index to original participant indices
        
        for group_idx, group in enumerate(groups):
            if self.stop_event.is_set():
                return None
            
            self.log_to_friendly(f"#### Processing Group {group_idx+1} ({len(group)} statements)\n\n")
            self.log_to_detailed(f"#### Group {group_idx+1}\n\n")
            self.log_to_detailed(f"Contains {len(group)} statements\n\n")
            
            # Get list of original participant indices for this group
            if level == 0:
                # At level 0, map the group's statement indices to original participant indices
                group_participant_indices = []
                start_idx = sum(len(g) for g in groups[:group_idx])
                for i in range(len(group)):
                    group_participant_indices.append(start_idx + i)
            else:
                # At higher levels, use the existing mapping to find original participants
                group_participant_indices = []
                start_idx = sum(len(g) for g in groups[:group_idx])
                for i in range(len(group)):
                    orig_idx = start_idx + i
                    if orig_idx in participant_mapping:
                        group_participant_indices.extend(participant_mapping[orig_idx])
            
            # Log the statements in this group
            self.log_to_detailed("**Statements in this group:**\n\n")
            for i, stmt in enumerate(group):
                # Get original participant numbers if available
                if level == 0:
                    orig_p_idx = group_participant_indices[i]
                    self.log_to_detailed(f"Statement {i+1} (from Participant {orig_p_idx+1}):\n{stmt}\n\n")
                else:
                    self.log_to_detailed(f"Statement {i+1}:\n{stmt}\n\n")
            
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
            self.log_to_friendly("Only one group at this level. Using its consensus as the final result.\n\n")
            self.log_to_detailed("Only one winning statement from this level. Using it as final result.\n\n")
            return winning_statements[0]
            
        # Otherwise, recurse to process the winning statements
        if winning_statements:
            self.log_to_friendly(f"Moving to next level with {len(winning_statements)} group consensuses...\n\n")
            self.log_to_detailed(f"Moving to next level with {len(winning_statements)} winning statements\n\n")
            
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
    
    def process_single_group(self, question, statements, original_participant_indices, voting_strategy, level, group_idx):
        """Process a single group of statements to find a winning statement"""
        if self.stop_event.is_set():
            return None
            
        group_label = f"Level {level+1}, Group {group_idx+1} ({len(statements)} statements)"
        
        # Log what we're about to do
        self.log_to_detailed(f"**Processing {group_label}**\n\n")
        
        # Generate candidate statements for this group
        self.log_to_detailed("##### Candidate Generation\n\n")
        
        # Generate candidates
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
            self.log_to_detailed(f"Generating candidate {i+1}/{num_candidates}\n\n")
            
            candidate = self.generate_single_candidate(question, shuffled_statements, i+1)
            if candidate:
                candidates.append(candidate)
                self.log_to_detailed(f"**Candidate {i+1}:**\n{candidate}\n\n")
        
        if not candidates:
            self.log_to_detailed("**Error:** Failed to generate any candidate statements.\n\n")
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
        self.log_to_detailed("##### Election Simulation\n\n")
        self.log_to_detailed(f"Number of candidates: {len(candidates)}\n")
        self.log_to_detailed(f"Number of voters: {len(voting_participants)}\n\n")
            
        # Initialize rankings
        rankings = {i: [] for i in range(len(voting_participants))}
        
        # For each participant, predict their rankings
        for p_idx, (orig_idx, statement) in enumerate(voting_participants):
            if self.stop_event.is_set():
                return None
                
            self.log_to_detailed(f"**Predicting ranking for Voter {p_idx+1} (Participant {orig_idx+1})**\n\n")
            
            # Predict ranking for this participant
            predicted_ranking, attempts_log = self.predict_participant_ranking_json(
                question, 
                statement, 
                candidates,
                orig_idx + 1  # Use original participant number for prompt
            )
            
            if predicted_ranking:
                rankings[p_idx] = predicted_ranking
                self.log_to_detailed(f"**Predicted ranking:** {[r+1 for r in predicted_ranking]}\n\n")
        
        if self.stop_event.is_set():
            return None
            
        # Calculate winner using Schulze method
        self.log_to_detailed("**Calculating winner using Schulze Method**\n\n")
        
        winner_idx, pairwise_matrix, strongest_paths = self.schulze_method(rankings, len(candidates))
        
        # Log the winner
        self.log_to_detailed(f"**Winner calculated:** Candidate {winner_idx+1}\n\n")
        self.log_to_detailed(f"**Winning statement:**\n{candidates[winner_idx]}\n\n")
        
        return candidates[winner_idx]
    
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
    
    def update_friendly_output_with_winner(self, winning_statement):
        """Insert the winning statement at the top of the friendly output"""
        # Flash to indicate activity
        self.flash_textbox(self.friendly_output)
        
        # Get current content
        current_content = self.friendly_output.get("1.0", "end-1c")
        
        # Create new content with winning statement at the top
        winner_section = f"## 🏆 Winning Consensus Statement\n\n{winning_statement}\n\n---\n\n"
        new_content = winner_section + current_content
        
        # Update the textbox
        self.friendly_output.delete("1.0", "end")
        self.friendly_output.insert("1.0", new_content)
        
        # Scroll to the top
        self.friendly_output.see("1.0")

    def update_friendly_output_with_consensus(self, consensus_statement):
        """Insert the final consensus statement at the top of the friendly output"""
        # Flash to indicate activity
        self.flash_textbox(self.friendly_output)
        
        # Get current content
        current_content = self.friendly_output.get("1.0", "end-1c")
        
        # Create new content with consensus statement at the top
        consensus_section = f"## 🏆 Final Group Consensus\n\n{consensus_statement}\n\n---\n\n"
        new_content = consensus_section + current_content
        
        # Update the textbox
        self.friendly_output.delete("1.0", "end")
        self.friendly_output.insert("1.0", new_content)
        
        # Scroll to the top
        self.friendly_output.see("1.0")
    
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
            
    def flash_textbox(self, textbox, duration=0.33):
        """Flash the textbox background to indicate activity"""
        original_color = textbox.cget("fg_color")
        
        # Set to dull orange
        textbox.configure(fg_color="#3e103e")
        
        # Schedule reversion to original color after duration
        self.root.after(int(duration * 1000), lambda: textbox.configure(fg_color=original_color))
    
    def update_debug_prompt(self, prompt):
        """Update the debug prompt display with scroll to top"""
        self.flash_textbox(self.prompt_text)
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", prompt)
        # Always scroll to top for prompt
        self.prompt_text.see("1.0")

    def update_debug_response(self, response):
        """Update the debug response display with scroll to bottom"""
        self.flash_textbox(self.response_text)
        self.response_text.delete("1.0", "end")
        self.response_text.insert("1.0", response)
        # Always scroll to bottom for response
        self.response_text.see("end")
        self.response_text.yview_moveto(1.0)
    
    def cleanup_after_process(self):
        """Clean up after the process is complete"""
        self.root.after(0, lambda: self.generate_btn.configure(state="normal"))
        self.root.after(0, lambda: self.recursive_generate_btn.configure(state="normal"))
    
    def stop_generation(self):
        """Stop any ongoing generation process"""
        self.stop_event.set()
        if self.current_response:
            try:
                self.current_response.close()
            except:
                pass

    # Model Management Callbacks (NEW)
    def on_preset_changed(self, preset_name):
        """Handle preset selection change"""
        if not MODEL_MANAGEMENT_AVAILABLE or preset_name == "custom":
            return

        self.apply_preset(preset_name)

    def apply_preset(self, preset_name, silent=False):
        """Apply a model management preset"""
        if not MODEL_MANAGEMENT_AVAILABLE:
            return

        preset_configs = {
            "prompted_deepseek": {
                "model": "deepseek-r1:14b",
                "description": "DeepSeek-R1 14B (Recommended) - Optimal batching, minimal model loading",
                "statement_temp": "0.6",
                "ranking_temp": "0.2"
            },
            "prompted_llama": {
                "model": "llama3.1",
                "description": "Llama 3.1 - Alternative prompted model with good performance",
                "statement_temp": "0.6",
                "ranking_temp": "0.2"
            },
            "prompted_qwen": {
                "model": "qwen2.5:14b",
                "description": "Qwen 2.5 14B - Alternative prompted model, fast inference",
                "statement_temp": "0.6",
                "ranking_temp": "0.2"
            }
        }

        if preset_name in preset_configs:
            config = preset_configs[preset_name]
            # Apply to both generation and ranking models
            self.gen_model_var.set(config["model"])
            self.rank_model_var.set(config["model"])
            self.gen_temperature_var.set(config["statement_temp"])
            self.rank_temperature_var.set(config["ranking_temp"])

            # Only update description if the widget exists
            if hasattr(self, 'preset_description'):
                self.preset_description.configure(text=config["description"])

            self.current_preset = preset_name

            # Show notification in friendly output (only if textbox exists and not silent)
            if not silent and hasattr(self, 'friendly_output'):
                try:
                    self.log_to_friendly(f"\n🎯 Preset Applied: {preset_name}\n")
                    self.log_to_friendly(f"Model: {config['model']}\n")
                    self.log_to_friendly(f"Statement Temperature: {config['statement_temp']}\n")
                    self.log_to_friendly(f"Ranking Temperature: {config['ranking_temp']}\n\n")
                except:
                    pass  # Textbox not ready yet

            logger.info(f"Applied preset: {preset_name}")

    def on_deepmind_prompts_changed(self):
        """Handle DeepMind prompts checkbox change"""
        if not MODEL_MANAGEMENT_AVAILABLE:
            return

        use_deepmind = self.use_deepmind_prompts_var.get()

        # Only log if textbox exists
        if hasattr(self, 'friendly_output'):
            try:
                if use_deepmind:
                    self.log_to_friendly(
                        "\n📚 DeepMind Chain-of-Thought Prompts Enabled\n"
                        "Using production-tested prompts with structured <answer><sep></answer> format.\n"
                        "Note: This is experimental and may require prompt template adjustments.\n\n"
                    )
                else:
                    self.log_to_friendly(
                        "\n📚 DeepMind Chain-of-Thought Prompts Disabled\n"
                        "Using original prompt templates.\n\n"
                    )
            except:
                pass  # Textbox not ready yet

        logger.info(f"DeepMind prompts: {'enabled' if use_deepmind else 'disabled'}")
        
        self.log_to_friendly("\n**Process stopped by user.**\n")
        self.log_to_detailed("\n**Process stopped by user.**\n")
        
        self.friendly_status_var.set("Stopped")
        self.detailed_status_var.set("Stopped")
        
        self.generate_btn.configure(state="normal")
        self.recursive_generate_btn.configure(state="normal")

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