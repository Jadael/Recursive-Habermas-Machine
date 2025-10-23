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
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Missing Dependency",
        "The customtkinter package is required but not installed.\n\n"
        "Please install it using pip:\n"
        "pip install customtkinter"
    )
    sys.exit(1)

# Try importing other dependencies
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
        generate_opinion_critique_cot_prompt,
        generate_opinion_only_ranking_prompt,
        extract_arrow_ranking,
        validate_arrow_ranking,
        schulze_method,
        format_ranking_results,
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
    logger.warning("Using legacy mode")


class HabermasMachineIntegrated:
    def __init__(self, root):
        self.root = root
        self.root.title("Habermas Machine - AI-Assisted Consensus Builder v2.0")
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

        # Model management
        self.model_manager = None
        self.use_model_management = MODEL_MANAGEMENT_AVAILABLE
        self.current_preset = "prompted_deepseek" if MODEL_MANAGEMENT_AVAILABLE else None

        # Default prompt templates (original)
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
        self.model_var.set("deepseek-r1:14b")
        self.temperature_var.set("0.6")
        self.ranking_temperature_var.set("0.2")
        self.max_retries_var.set("3")
        self.max_group_size_var.set("12")
        self.num_candidates_var.set("4")
        self.question_text.insert("1.0", "Should voting be compulsory?")

        # Set default preset if available
        if MODEL_MANAGEMENT_AVAILABLE:
            self.preset_var.set("prompted_deepseek")
            self.apply_preset("prompted_deepseek")

        # Set prompt templates in the UI
        for key, template in self.prompt_templates.items():
            if key == "candidate_generation":
                self.candidate_template_text.delete("1.0", "end")
                self.candidate_template_text.insert("1.0", template)
            elif key == "ranking_prediction":
                self.ranking_template_text.delete("1.0", "end")
                self.ranking_template_text.insert("1.0", template)

        # Load sample data
        self.load_sample_data()

    def load_sample_data(self):
        """Load sample participant statements for testing"""
        if MODEL_MANAGEMENT_AVAILABLE:
            # Use the structured sample data from the package
            sample_participants = COMPULSORY_VOTING_OPINIONS
        else:
            # Fallback to legacy sample data
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
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=3)
        self.root.grid_columnconfigure(2, weight=2)
        self.root.grid_rowconfigure(0, weight=1)

        # Create main frames
        self.left_column = ctk.CTkFrame(self.root)
        self.middle_column = ctk.CTkFrame(self.root)
        self.right_column = ctk.CTkFrame(self.root)

        self.left_column.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.middle_column.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.right_column.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        # Set up the columns
        self.setup_left_column()
        self.setup_middle_column()
        self.setup_right_column()

    def setup_left_column(self):
        self.left_column.grid_columnconfigure(0, weight=1)
        self.left_column.grid_rowconfigure(0, weight=1)

        # Create tabview for left column
        self.left_tabview = ctk.CTkTabview(self.left_column)
        self.left_tabview.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Add tabs
        self.left_tabview.add("Inputs")
        self.left_tabview.add("Settings")
        self.left_tabview.add("Templates")

        # Setup each tab
        self.setup_inputs_tab()
        self.setup_settings_tab()
        self.setup_templates_tab()

    def setup_settings_tab(self):
        """Setup settings tab with model management integration"""
        settings_frame = ctk.CTkScrollableFrame(self.left_tabview.tab("Settings"))
        settings_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Model Management Section (NEW!)
        if MODEL_MANAGEMENT_AVAILABLE:
            model_mgmt_frame = ctk.CTkFrame(settings_frame)
            model_mgmt_frame.pack(fill="x", pady=10, padx=5)

            ctk.CTkLabel(
                model_mgmt_frame,
                text="Model Configuration",
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
                text="DeepSeek-R1 14B (Recommended) - Batched workflow, minimal model loading",
                font=("Arial", 10),
                wraplength=400
            )
            self.preset_description.pack(pady=5, padx=10)

            # Use DeepMind Prompts option
            self.use_deepmind_prompts_var = ctk.BooleanVar(value=True)
            deepmind_check = ctk.CTkCheckBox(
                model_mgmt_frame,
                text="Use DeepMind Chain-of-Thought Prompts (Recommended)",
                variable=self.use_deepmind_prompts_var,
                command=self.on_deepmind_prompts_changed,
                font=("Arial", 11)
            )
            deepmind_check.pack(pady=5, padx=10, anchor="w")

            # Separator
            separator = ctk.CTkFrame(settings_frame, height=2, fg_color="gray30")
            separator.pack(fill="x", pady=10, padx=5)

        # Model entry (can override preset)
        model_frame = ctk.CTkFrame(settings_frame)
        model_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(model_frame, text="Model:", anchor="w", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        self.model_var = ctk.StringVar()
        self.model_entry = ctk.CTkEntry(model_frame, textvariable=self.model_var, width=200, font=("Arial", 12))
        self.model_entry.pack(side="left", padx=10, fill="x", expand=True)

        if MODEL_MANAGEMENT_AVAILABLE:
            ctk.CTkLabel(
                model_frame,
                text="(Override preset if needed)",
                font=("Arial", 9),
                text_color="gray50"
            ).pack(side="left", padx=5)

        # Generation parameters
        gen_params_frame = ctk.CTkFrame(settings_frame)
        gen_params_frame.pack(fill="x", pady=10, padx=5)

        ctk.CTkLabel(gen_params_frame, text="Statement Generation Parameters", font=("Arial", 14, "bold")).pack(pady=5)

        params_grid = ctk.CTkFrame(gen_params_frame)
        params_grid.pack(fill="x", padx=10, pady=5, expand=True)

        # Temperature
        ctk.CTkLabel(params_grid, text="Temperature:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.temperature_var = ctk.StringVar()
        self.temperature_entry = ctk.CTkEntry(params_grid, textvariable=self.temperature_var, width=60, font=("Arial", 12))
        self.temperature_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        if MODEL_MANAGEMENT_AVAILABLE:
            ctk.CTkLabel(
                params_grid,
                text="(0.6 recommended for synthesis)",
                font=("Arial", 9),
                text_color="gray50"
            ).grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Number of candidates
        ctk.CTkLabel(params_grid, text="Candidate Statements:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.num_candidates_var = ctk.StringVar()
        self.num_candidates_entry = ctk.CTkEntry(params_grid, textvariable=self.num_candidates_var, width=60, font=("Arial", 12))
        self.num_candidates_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Ranking prediction parameters
        rank_params_frame = ctk.CTkFrame(settings_frame)
        rank_params_frame.pack(fill="x", pady=10, padx=5)

        ctk.CTkLabel(rank_params_frame, text="Ranking Prediction Parameters", font=("Arial", 14, "bold")).pack(pady=5)

        rank_grid = ctk.CTkFrame(rank_params_frame)
        rank_grid.pack(fill="x", padx=10, pady=5, expand=True)

        # Ranking temperature
        ctk.CTkLabel(rank_grid, text="Temperature:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.ranking_temperature_var = ctk.StringVar()
        self.ranking_temperature_entry = ctk.CTkEntry(rank_grid, textvariable=self.ranking_temperature_var, width=60, font=("Arial", 12))
        self.ranking_temperature_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        if MODEL_MANAGEMENT_AVAILABLE:
            ctk.CTkLabel(
                rank_grid,
                text="(0.2 recommended for consistent rankings)",
                font=("Arial", 9),
                text_color="gray50"
            ).grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Max retries
        ctk.CTkLabel(rank_grid, text="Max JSON Retries:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.max_retries_var = ctk.StringVar()
        self.max_retries_entry = ctk.CTkEntry(rank_grid, textvariable=self.max_retries_var, width=60, font=("Arial", 12))
        self.max_retries_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

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

        ctk.CTkRadioButton(
            strategy_frame,
            text="Own groups only",
            variable=self.voting_strategy_var,
            value="own_groups_only",
            font=("Arial", 12)
        ).pack(anchor="w", pady=2)

        ctk.CTkRadioButton(
            strategy_frame,
            text="All participants vote in all elections",
            variable=self.voting_strategy_var,
            value="all_elections",
            font=("Arial", 12)
        ).pack(anchor="w", pady=2)

        # Output options
        output_frame = ctk.CTkFrame(settings_frame)
        output_frame.pack(fill="x", pady=10, padx=5)

        ctk.CTkLabel(output_frame, text="Output Options", font=("Arial", 14, "bold")).pack(pady=5)

        output_options = ctk.CTkFrame(output_frame)
        output_options.pack(fill="x", padx=10, pady=5)

        # Save output option
        self.save_output_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            output_options,
            text="Auto-save results to file",
            variable=self.save_output_var,
            font=("Arial", 11)
        ).pack(anchor="w", pady=2)

        if MODEL_MANAGEMENT_AVAILABLE:
            # Show statistics option
            self.show_stats_var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(
                output_options,
                text="Show performance statistics",
                variable=self.show_stats_var,
                font=("Arial", 11)
            ).pack(anchor="w", pady=2)

    def on_preset_changed(self, preset_name):
        """Handle preset selection change"""
        if not MODEL_MANAGEMENT_AVAILABLE or preset_name == "custom":
            return

        self.apply_preset(preset_name)

    def apply_preset(self, preset_name):
        """Apply a model management preset"""
        if not MODEL_MANAGEMENT_AVAILABLE:
            return

        preset_configs = {
            "prompted_deepseek": {
                "model": "deepseek-r1:14b",
                "description": "DeepSeek-R1 14B (Recommended) - Batched workflow, minimal model loading",
                "statement_temp": "0.6",
                "ranking_temp": "0.2"
            },
            "prompted_llama": {
                "model": "llama3.1",
                "description": "Llama 3.1 - Alternative prompted model",
                "statement_temp": "0.6",
                "ranking_temp": "0.2"
            },
            "prompted_qwen": {
                "model": "qwen2.5:14b",
                "description": "Qwen 2.5 14B - Alternative prompted model",
                "statement_temp": "0.6",
                "ranking_temp": "0.2"
            }
        }

        if preset_name in preset_configs:
            config = preset_configs[preset_name]
            self.model_var.set(config["model"])
            self.temperature_var.set(config["statement_temp"])
            self.ranking_temperature_var.set(config["ranking_temp"])
            self.preset_description.configure(text=config["description"])
            self.current_preset = preset_name

            logger.info(f"Applied preset: {preset_name}")

    def on_deepmind_prompts_changed(self):
        """Handle DeepMind prompts checkbox change"""
        if not MODEL_MANAGEMENT_AVAILABLE:
            return

        use_deepmind = self.use_deepmind_prompts_var.get()

        if use_deepmind:
            # Show info about DeepMind prompts
            self.add_to_results(
                "\n🔬 Using DeepMind Chain-of-Thought Prompts\n" +
                "These production-tested prompts use structured <answer><sep></answer> format " +
                "for more reliable parsing.\n",
                "friendly"
            )

        logger.info(f"DeepMind prompts: {'enabled' if use_deepmind else 'disabled'}")

    def setup_inputs_tab(self):
        """Setup inputs tab (same as original, kept for compatibility)"""
        inputs_frame = ctk.CTkScrollableFrame(self.left_tabview.tab("Inputs"))
        inputs_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Question input
        question_label = ctk.CTkLabel(inputs_frame, text="Question:", font=("Arial", 14, "bold"))
        question_label.pack(anchor="w", pady=(10, 5), padx=10)

        self.question_text = ctk.CTkTextbox(inputs_frame, height=60, font=("Arial", 12))
        self.question_text.pack(fill="x", padx=10, pady=5)

        # Participant statements
        participants_label = ctk.CTkLabel(inputs_frame, text="Participant Statements:", font=("Arial", 14, "bold"))
        participants_label.pack(anchor="w", pady=(10, 5), padx=10)

        # Participant count display
        self.participant_count_label = ctk.CTkLabel(
            inputs_frame,
            text="Participants: 0",
            font=("Arial", 11),
            text_color="gray70"
        )
        self.participant_count_label.pack(anchor="w", padx=10, pady=2)

        self.participants_text = ctk.CTkTextbox(inputs_frame, height=400, font=("Arial", 11))
        self.participants_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.participants_text.bind("<KeyRelease>", lambda e: self.update_participant_count())

        # Bulk import button
        import_button = ctk.CTkButton(
            inputs_frame,
            text="Bulk Import from File",
            command=self.bulk_import_statements,
            font=("Arial", 12)
        )
        import_button.pack(pady=10, padx=10)

        # Action buttons
        button_frame = ctk.CTkFrame(inputs_frame)
        button_frame.pack(fill="x", pady=10, padx=10)

        # Single run button
        self.generate_button = ctk.CTkButton(
            button_frame,
            text="Generate Consensus (Single Run)",
            command=self.start_consensus_generation,
            font=("Arial", 13, "bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.generate_button.pack(fill="x", pady=5)

        # Recursive button
        self.recursive_button = ctk.CTkButton(
            button_frame,
            text="Recursive Consensus Builder",
            command=self.start_recursive_consensus,
            font=("Arial", 13, "bold"),
            fg_color="blue",
            hover_color="darkblue"
        )
        self.recursive_button.pack(fill="x", pady=5)

        # Stop button
        self.stop_button = ctk.CTkButton(
            button_frame,
            text="Stop Generation",
            command=self.stop_generation,
            font=("Arial", 12),
            fg_color="red",
            hover_color="darkred",
            state="disabled"
        )
        self.stop_button.pack(fill="x", pady=5)

    def setup_templates_tab(self):
        """Setup templates tab with DeepMind option"""
        templates_frame = ctk.CTkScrollableFrame(self.left_tabview.tab("Templates"))
        templates_frame.pack(fill="both", expand=True, padx=5, pady=5)

        if MODEL_MANAGEMENT_AVAILABLE:
            # Info about templates
            info_label = ctk.CTkLabel(
                templates_frame,
                text="💡 Tip: DeepMind Chain-of-Thought prompts are automatically used when enabled in Settings.",
                font=("Arial", 10),
                wraplength=400,
                text_color="gray70"
            )
            info_label.pack(pady=5, padx=10)

        # Candidate generation template
        candidate_label = ctk.CTkLabel(
            templates_frame,
            text="Candidate Generation Template:",
            font=("Arial", 13, "bold")
        )
        candidate_label.pack(anchor="w", pady=(10, 5), padx=10)

        self.candidate_template_text = ctk.CTkTextbox(templates_frame, height=200, font=("Arial", 10))
        self.candidate_template_text.pack(fill="x", padx=10, pady=5)

        # Ranking prediction template
        ranking_label = ctk.CTkLabel(
            templates_frame,
            text="Ranking Prediction Template:",
            font=("Arial", 13, "bold")
        )
        ranking_label.pack(anchor="w", pady=(10, 5), padx=10)

        self.ranking_template_text = ctk.CTkTextbox(templates_frame, height=250, font=("Arial", 10))
        self.ranking_template_text.pack(fill="x", padx=10, pady=5)

        # Reset button
        reset_button = ctk.CTkButton(
            templates_frame,
            text="Reset to Defaults",
            command=self.reset_templates,
            font=("Arial", 11)
        )
        reset_button.pack(pady=10, padx=10)

    def setup_middle_column(self):
        """Setup middle column with results tabs"""
        self.middle_column.grid_columnconfigure(0, weight=1)
        self.middle_column.grid_rowconfigure(0, weight=1)

        # Create tabview for results
        self.middle_tabview = ctk.CTkTabview(self.middle_column)
        self.middle_tabview.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Add tabs
        self.middle_tabview.add("Friendly Output")
        self.middle_tabview.add("Detailed Records")

        if MODEL_MANAGEMENT_AVAILABLE:
            self.middle_tabview.add("Performance Stats")

        # Setup result textboxes
        self.friendly_results = ctk.CTkTextbox(
            self.middle_tabview.tab("Friendly Output"),
            font=("Arial", 12),
            wrap="word"
        )
        self.friendly_results.pack(fill="both", expand=True, padx=5, pady=5)

        self.detailed_results = ctk.CTkTextbox(
            self.middle_tabview.tab("Detailed Records"),
            font=("Courier New", 10),
            wrap="word"
        )
        self.detailed_results.pack(fill="both", expand=True, padx=5, pady=5)

        if MODEL_MANAGEMENT_AVAILABLE:
            self.stats_results = ctk.CTkTextbox(
                self.middle_tabview.tab("Performance Stats"),
                font=("Courier New", 11),
                wrap="word"
            )
            self.stats_results.pack(fill="both", expand=True, padx=5, pady=5)

    def setup_right_column(self):
        """Setup right column with debug info"""
        self.right_column.grid_columnconfigure(0, weight=1)
        self.right_column.grid_rowconfigure(0, weight=1)

        # Create tabview for debug info
        self.right_tabview = ctk.CTkTabview(self.right_column)
        self.right_tabview.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Add tabs
        self.right_tabview.add("Current Prompt")
        self.right_tabview.add("Current Response")

        # Setup debug textboxes
        self.current_prompt_text = ctk.CTkTextbox(
            self.right_tabview.tab("Current Prompt"),
            font=("Courier New", 9),
            wrap="word"
        )
        self.current_prompt_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.current_response_text = ctk.CTkTextbox(
            self.right_tabview.tab("Current Response"),
            font=("Courier New", 9),
            wrap="word"
        )
        self.current_response_text.pack(fill="both", expand=True, padx=5, pady=5)

    def update_participant_count(self):
        """Update the participant count display"""
        text = self.participants_text.get("1.0", "end").strip()
        if not text:
            count = 0
        else:
            # Count non-empty lines
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            count = len(lines)

        self.participant_count_label.configure(text=f"Participants: {count}")

    def add_to_results(self, text, output_type="friendly"):
        """Add text to results (thread-safe)"""
        def update():
            if output_type == "friendly":
                self.friendly_results.insert("end", text)
                self.friendly_results.see("end")
            elif output_type == "detailed":
                self.detailed_results.insert("end", text)
                self.detailed_results.see("end")
            elif output_type == "stats" and MODEL_MANAGEMENT_AVAILABLE:
                self.stats_results.insert("end", text)
                self.stats_results.see("end")

        self.root.after(0, update)

    def clear_results(self):
        """Clear all result textboxes"""
        self.friendly_results.delete("1.0", "end")
        self.detailed_results.delete("1.0", "end")
        if MODEL_MANAGEMENT_AVAILABLE:
            self.stats_results.delete("1.0", "end")

    def start_consensus_generation(self):
        """Start single-run consensus generation"""
        # Get inputs
        question = self.question_text.get("1.0", "end").strip()
        participants_text = self.participants_text.get("1.0", "end").strip()

        if not question or not participants_text:
            messagebox.showwarning("Missing Input", "Please provide both a question and participant statements.")
            return

        # Parse participants
        self.participant_statements = [
            line.strip()
            for line in participants_text.split('\n')
            if line.strip()
        ]

        if len(self.participant_statements) == 0:
            messagebox.showwarning("No Participants", "Please add at least one participant statement.")
            return

        # Clear previous results
        self.clear_results()

        # Show starting message
        self.add_to_results(f"=== Habermas Machine Consensus Generation ===\n\n", "friendly")
        self.add_to_results(f"Question: {question}\n", "friendly")
        self.add_to_results(f"Participants: {len(self.participant_statements)}\n\n", "friendly")

        if MODEL_MANAGEMENT_AVAILABLE and self.use_deepmind_prompts_var.get():
            self.add_to_results("Using DeepMind Chain-of-Thought Prompts\n\n", "friendly")

        # Disable button
        self.generate_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.stop_event.clear()

        # Run in thread
        thread = Thread(target=self.run_consensus_generation, args=(question,))
        thread.daemon = True
        thread.start()

    def run_consensus_generation(self, question):
        """Run the consensus generation workflow"""
        try:
            # Implementation would go here
            # This is a placeholder - the full implementation would include
            # all the consensus generation logic using either the new model management
            # or the legacy approach

            self.add_to_results("⚠ Consensus generation implementation in progress...\n", "friendly")
            self.add_to_results("This integrated version will use the model management system.\n", "friendly")

        except Exception as e:
            logger.error(f"Error in consensus generation: {e}")
            logger.error(traceback.format_exc())
            self.add_to_results(f"\n❌ Error: {str(e)}\n", "friendly")
        finally:
            # Re-enable button
            self.root.after(0, lambda: self.generate_button.configure(state="normal"))
            self.root.after(0, lambda: self.stop_button.configure(state="disabled"))

    def start_recursive_consensus(self):
        """Start recursive consensus generation"""
        messagebox.showinfo("Coming Soon", "Recursive consensus with model management integration coming soon!")

    def stop_generation(self):
        """Stop current generation"""
        self.stop_event.set()
        self.add_to_results("\n⚠ Stopping generation...\n", "friendly")

    def bulk_import_statements(self):
        """Import statements from a file"""
        from tkinter import filedialog

        filename = filedialog.askopenfilename(
            title="Select file with participant statements",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()

                self.participants_text.delete("1.0", "end")
                self.participants_text.insert("1.0", content)
                self.update_participant_count()

                messagebox.showinfo("Success", "Statements imported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import file:\n{str(e)}")

    def reset_templates(self):
        """Reset templates to defaults"""
        self.prompt_templates = self.default_templates.copy()

        self.candidate_template_text.delete("1.0", "end")
        self.candidate_template_text.insert("1.0", self.prompt_templates["candidate_generation"])

        self.ranking_template_text.delete("1.0", "end")
        self.ranking_template_text.insert("1.0", self.prompt_templates["ranking_prediction"])

        messagebox.showinfo("Reset", "Templates reset to defaults!")


def main():
    root = ctk.CTk()
    app = HabermasMachineIntegrated(root)
    root.mainloop()


if __name__ == "__main__":
    main()
