import tkinter as tk
import customtkinter as ctk
from threading import Thread
import random
import json
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import os
from PIL import Image, ImageTk
import re
import requests

class HabermasChorusExtension:
    """Extension class that adds Chorus functionality to the Habermas Machine"""
    
    def __init__(self, habermas_machine):
        """Initialize the extension with reference to the main app"""
        self.app = habermas_machine
        self.value_statements = []
        self.sample_statements_loaded = False
        
        # Default Chorus prompt templates
        self.default_chorus_templates = {
            "response_simulation": """You are simulating how an associate would respond to a proposed workplace policy based on their value statement.

Associate's Value Statement:
{value_statement}

Associate's Department: {department}
Associate's Role: {role}
Associate's Location: {location}

Proposed Policy:
Title: {proposal_title}
Description: {proposal_description}

Based SOLELY on the associate's value statement and metadata, simulate how they would respond to this proposal. 

Your response MUST be formatted as a valid JSON object with the following structure:
{{
  "sentiment": "favorable|neutral|unfavorable",
  "score": 7.5,
  "concerns": ["concern 1", "concern 2"],
  "suggestions": ["suggestion 1", "suggestion 2"],
  "statement": "Their simulated response statement"
}}

Where:
- sentiment: Must be exactly one of: "favorable", "neutral", or "unfavorable"
- score: A number from 1-10 representing level of support (10 being highest)
- concerns: An array of specific concerns, if any (can be empty array [])
- suggestions: An array of suggestions for improvement, if any (can be empty array [])
- statement: A 1-3 sentence response in their voice expressing their reaction

IMPORTANT: Your entire response must be ONLY the JSON object, with no additional text before or after."""
        }
        
        # Create chorus templates that will be edited
        self.chorus_templates = self.default_chorus_templates.copy()
        
        # Add the Chorus tab to the UI
        self.add_chorus_tab()
        
        # Initialize figures for charts
        self.sentiment_fig = None
        self.sentiment_canvas = None
        self.concerns_fig = None
        self.concerns_canvas = None
        self.demographic_fig = None
        self.demographic_canvas = None
        
        # Initialize results storage
        self.simulation_results = []
        
    def add_chorus_tab(self):
        """Add the Habermas Chorus tab to the UI"""
        # Create a new tab in the existing tabview if it doesn't exist
        if "Chorus" not in self.app.left_tabview._segmented_button.get():
            self.app.left_tabview.add("Chorus")
        
        chorus_tab = self.app.left_tabview.tab("Chorus")
        
        # Configure the tab
        chorus_tab.grid_columnconfigure(0, weight=1)
        chorus_tab.grid_rowconfigure(0, weight=0)  # Repository section - fixed height
        chorus_tab.grid_rowconfigure(1, weight=0)  # Proposal section - fixed height
        chorus_tab.grid_rowconfigure(2, weight=1)  # Results section - expandable
        
        # Create the value repository section
        self.setup_value_repository_section(chorus_tab)
        
        # Create the proposal submission section
        self.setup_proposal_section(chorus_tab)
        
        # Create the results visualization section
        self.setup_results_section(chorus_tab)
        
        # Initialize the results view
        self.setup_results_tabs()
    
    def setup_value_repository_section(self, parent):
        """Create the value statement repository UI"""
        repo_frame = ctk.CTkFrame(parent)
        repo_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        repo_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        ctk.CTkLabel(repo_frame, text="Value Statement Repository", anchor="w", 
                    font=("Arial", 14, "bold")).pack(fill="x", padx=10, pady=5)
        
        # Stats display
        stats_frame = ctk.CTkFrame(repo_frame)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        self.statement_count_var = ctk.StringVar(value="Total Statements: 0")
        self.coverage_var = ctk.StringVar(value="Associate Coverage: 0%")
        
        ctk.CTkLabel(stats_frame, textvariable=self.statement_count_var).pack(side="left", padx=20)
        ctk.CTkLabel(stats_frame, textvariable=self.coverage_var).pack(side="left", padx=20)
        
        # Buttons for repository management
        btn_frame = ctk.CTkFrame(repo_frame)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            btn_frame,
            text="View Repository",
            command=self.view_repository,
            font=("Arial", 12)
        ).pack(side="left", padx=10, pady=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Add Sample Statements",
            command=self.add_sample_statements,
            font=("Arial", 12)
        ).pack(side="left", padx=10, pady=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Add Statement",
            command=self.add_new_statement,
            font=("Arial", 12),
            fg_color="#1f5d3c"  # Green color
        ).pack(side="right", padx=10, pady=5)
    
    def setup_proposal_section(self, parent):
        """Create the proposal submission UI"""
        proposal_frame = ctk.CTkFrame(parent)
        proposal_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        proposal_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        ctk.CTkLabel(proposal_frame, text="Submit Proposal for Feedback", anchor="w", 
                    font=("Arial", 14, "bold")).pack(fill="x", padx=10, pady=5)
        
        # Proposal input
        ctk.CTkLabel(proposal_frame, text="Proposal Title:", anchor="w").pack(fill="x", padx=10, pady=(5, 0))
        self.proposal_title = ctk.CTkEntry(proposal_frame, font=("Arial", 12))
        self.proposal_title.pack(fill="x", padx=10, pady=(0, 5))
        
        ctk.CTkLabel(proposal_frame, text="Proposal Description:", anchor="w").pack(fill="x", padx=10, pady=(5, 0))
        self.proposal_text = ctk.CTkTextbox(proposal_frame, height=100, font=("Arial", 12))
        self.proposal_text.pack(fill="x", padx=10, pady=(0, 5))
        
        # Default text for demo
        self.proposal_title.insert(0, "New Remote Work Policy")
        self.proposal_text.insert("1.0", "We are considering implementing a hybrid work policy where associates would be required to work in the office 3 days per week and can choose to work remotely for the remaining 2 days. This would begin next quarter.")
        
        # Filter options
        filter_frame = ctk.CTkFrame(proposal_frame)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(filter_frame, text="Filter by:", font=("Arial", 12)).pack(side="left", padx=10)
        
        self.dept_var = ctk.StringVar(value="All Departments")
        dept_dropdown = ctk.CTkOptionMenu(
            filter_frame, 
            variable=self.dept_var,
            values=["All Departments", "Customer Service", "IT", "HR", "Finance", "Operations"]
        )
        dept_dropdown.pack(side="left", padx=10)
        
        self.role_var = ctk.StringVar(value="All Roles")
        role_dropdown = ctk.CTkOptionMenu(
            filter_frame, 
            variable=self.role_var,
            values=["All Roles", "Associate", "Team Lead", "Manager", "Director"]
        )
        role_dropdown.pack(side="left", padx=10)
        
        self.location_var = ctk.StringVar(value="All Locations")
        location_dropdown = ctk.CTkOptionMenu(
            filter_frame, 
            variable=self.location_var,
            values=["All Locations", "HQ", "Regional Offices", "Remote"]
        )
        location_dropdown.pack(side="left", padx=10)
        
        # Submit button
        ctk.CTkButton(
            proposal_frame,
            text="Generate Feedback",
            command=self.run_chorus_simulation,
            font=("Arial", 12),
            fg_color="#1f5d3c"  # Green color
        ).pack(pady=10)
    
    def setup_results_section(self, parent):
        """Create the results visualization UI"""
        results_frame = ctk.CTkFrame(parent)
        results_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(0, weight=0)  # Header
        results_frame.grid_rowconfigure(1, weight=1)  # Charts
        
        # Header
        header_frame = ctk.CTkFrame(results_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ctk.CTkLabel(header_frame, text="Simulation Results", font=("Arial", 14, "bold")).pack(side="left", padx=10, pady=5)
        
        self.chorus_status_var = ctk.StringVar(value="Ready")
        status_label = ctk.CTkLabel(header_frame, textvariable=self.chorus_status_var, font=("Arial", 12))
        status_label.pack(side="right", padx=10, pady=5)
        
        # Create tabview for different result views
        self.results_tabview = ctk.CTkTabview(results_frame)
        self.results_tabview.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Add tabs for different result views
        self.results_tabview.add("Summary")
        self.results_tabview.add("Sentiment Analysis")
        self.results_tabview.add("Key Concerns")
        self.results_tabview.add("Suggestions")
        
    def setup_results_tabs(self):
        """Set up each of the results tabs"""
        # Setup summary tab
        summary_tab = self.results_tabview.tab("Summary")
        summary_tab.grid_columnconfigure(0, weight=1)
        summary_tab.grid_rowconfigure(0, weight=1)
        
        self.summary_text = ctk.CTkTextbox(summary_tab, wrap="word", font=("Arial", 12))
        self.summary_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.summary_text.insert("1.0", "Run a simulation to see results.")
        
        # Setup sentiment analysis tab
        sentiment_tab = self.results_tabview.tab("Sentiment Analysis")
        sentiment_tab.grid_columnconfigure(0, weight=1)
        sentiment_tab.grid_rowconfigure(0, weight=1)
        
        self.sentiment_frame = ctk.CTkFrame(sentiment_tab)
        self.sentiment_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Setup concerns tab
        concerns_tab = self.results_tabview.tab("Key Concerns")
        concerns_tab.grid_columnconfigure(0, weight=1)
        concerns_tab.grid_rowconfigure(0, weight=1)
        
        self.concerns_frame = ctk.CTkFrame(concerns_tab)
        self.concerns_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Setup suggestions tab
        suggestions_tab = self.results_tabview.tab("Suggestions")
        suggestions_tab.grid_columnconfigure(0, weight=1)
        suggestions_tab.grid_rowconfigure(0, weight=1)
        
        self.suggestions_text = ctk.CTkTextbox(suggestions_tab, wrap="word", font=("Arial", 12))
        self.suggestions_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.suggestions_text.insert("1.0", "Run a simulation to see improvement suggestions.")
    
    def view_repository(self):
        """Display the value statement repository in a new window"""
        if not self.value_statements:
            tk.messagebox.showinfo("Repository Empty", "The repository is empty. Add sample statements first.")
            return
            
        repo_window = ctk.CTkToplevel(self.app.root)
        repo_window.title("Value Statement Repository")
        repo_window.geometry("800x600")
        
        # Configure the window
        repo_window.grid_columnconfigure(0, weight=1)
        repo_window.grid_rowconfigure(0, weight=0)  # Header
        repo_window.grid_rowconfigure(1, weight=1)  # List
        
        # Header
        header_frame = ctk.CTkFrame(repo_window)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Value Statement Repository", 
                    font=("Arial", 16, "bold")).pack(side="left", padx=10, pady=5)
        
        # Create scrollable frame for statements
        statements_frame = ctk.CTkScrollableFrame(repo_window)
        statements_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Add each statement to the frame
        for i, statement in enumerate(self.value_statements):
            stmt_frame = ctk.CTkFrame(statements_frame)
            stmt_frame.pack(fill="x", padx=5, pady=5, expand=True)
            
            # Associate info
            info_text = f"Associate {i+1} | {statement['department']} | {statement['role']} | {statement['location']}"
            ctk.CTkLabel(stmt_frame, text=info_text, font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            # Statement text
            ctk.CTkLabel(stmt_frame, text=statement['statement'], wraplength=700, justify="left").pack(anchor="w", padx=10, pady=(0, 10))
    
    def add_sample_statements(self):
        """Add sample value statements to the repository"""
        sample_statements = [
            {
                "department": "Customer Service",
                "role": "Associate",
                "location": "HQ",
                "statement": "I believe in a healthy work-life balance. I'm most productive when I have flexibility in my schedule, but I also value in-person collaboration with my team. I live 45 minutes from the office, so commuting daily is a significant time commitment for me."
            },
            {
                "department": "IT",
                "role": "Team Lead",
                "location": "Regional Offices",
                "statement": "I prioritize team cohesion and effective communication. While I appreciate the focus time that remote work allows, I've found that certain collaborative tasks are more efficient in person. Technology enablement is critical for any work arrangement."
            },
            {
                "department": "HR",
                "role": "Manager",
                "location": "HQ",
                "statement": "I value inclusive policies that accommodate different working styles and personal circumstances. I believe our workplace should be equitable and accessible to all, regardless of their personal situation or preferences."
            },
            {
                "department": "Finance",
                "role": "Director",
                "location": "HQ",
                "statement": "I prioritize measurable results and accountability. I believe that clear expectations and metrics for success are essential regardless of work location. I'm concerned about maintaining our company culture with distributed teams."
            },
            {
                "department": "Operations",
                "role": "Associate",
                "location": "Remote",
                "statement": "I care deeply about environmental impact and believe reducing commutes is beneficial. I've arranged my home workspace to be productive and prefer to minimize unnecessary travel. I have caregiving responsibilities that make remote work essential for me."
            },
            {
                "department": "Customer Service",
                "role": "Team Lead",
                "location": "Regional Offices",
                "statement": "I value fairness and consistency in how policies are applied. I believe that customer needs should drive our decisions about work location. I'm concerned about the potential for inequity between roles that can and cannot work remotely."
            },
            {
                "department": "IT",
                "role": "Manager",
                "location": "Remote",
                "statement": "I prioritize innovation and believe diverse perspectives drive better solutions. I've found that a mix of collaborative time and independent work leads to the best outcomes for complex projects. I'm concerned about maintaining security with remote work."
            },
            {
                "department": "Operations",
                "role": "Director",
                "location": "HQ",
                "statement": "I value efficiency and resource optimization. I believe our office space should be utilized effectively, and that some in-person time is essential for building relationships and trust among teams."
            }
        ]
        
        # Add sample statements if not already added
        if not self.sample_statements_loaded:
            self.value_statements = sample_statements
            self.sample_statements_loaded = True
            self.update_repository_stats()
            tk.messagebox.showinfo("Success", "Sample statements added to repository.")
        else:
            tk.messagebox.showinfo("Already Loaded", "Sample statements are already loaded.")
    
    def add_new_statement(self):
        """Open a dialog to add a new value statement"""
        add_window = ctk.CTkToplevel(self.app.root)
        add_window.title("Add Value Statement")
        add_window.geometry("600x500")
        add_window.grab_set()  # Make window modal
        
        # Configure the window
        add_window.grid_columnconfigure(0, weight=1)
        add_window.grid_rowconfigure(3, weight=1)  # Statement text area expands
        
        # Header
        ctk.CTkLabel(add_window, text="Add Value Statement", 
                    font=("Arial", 16, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Associate info section
        info_frame = ctk.CTkFrame(add_window)
        info_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        # Department
        ctk.CTkLabel(info_frame, text="Department:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        dept_var = ctk.StringVar(value="Customer Service")
        dept_dropdown = ctk.CTkOptionMenu(
            info_frame, 
            variable=dept_var,
            values=["Customer Service", "IT", "HR", "Finance", "Operations"]
        )
        dept_dropdown.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Role
        ctk.CTkLabel(info_frame, text="Role:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        role_var = ctk.StringVar(value="Associate")
        role_dropdown = ctk.CTkOptionMenu(
            info_frame, 
            variable=role_var,
            values=["Associate", "Team Lead", "Manager", "Director"]
        )
        role_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # Location
        ctk.CTkLabel(info_frame, text="Location:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        location_var = ctk.StringVar(value="HQ")
        location_dropdown = ctk.CTkOptionMenu(
            info_frame, 
            variable=location_var,
            values=["HQ", "Regional Offices", "Remote"]
        )
        location_dropdown.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # Statement text
        ctk.CTkLabel(add_window, text="Value Statement:", 
                    anchor="w").grid(row=2, column=0, padx=10, pady=(10, 0), sticky="w")
        
        statement_text = ctk.CTkTextbox(add_window, height=200, font=("Arial", 12))
        statement_text.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # Example text
        example_text = "Describe your priorities, concerns, and perspectives about your work environment. For example: I value work-life balance and flexibility, but also appreciate in-person collaboration. I'm concerned about commute time and prefer a mix of remote and office work."
        statement_text.insert("1.0", example_text)
        
        # Button frame
        button_frame = ctk.CTkFrame(add_window)
        button_frame.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        
        # Cancel button
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=add_window.destroy,
            font=("Arial", 12)
        ).pack(side="left", padx=10, pady=10)
        
        # Save button
        def save_statement():
            statement = {
                "department": dept_var.get(),
                "role": role_var.get(),
                "location": location_var.get(),
                "statement": statement_text.get("1.0", "end-1c")
            }
            
            # Check if the default example is still there
            if statement["statement"] == example_text:
                tk.messagebox.showwarning("Warning", "Please replace the example text with your own statement.")
                return
                
            self.value_statements.append(statement)
            self.update_repository_stats()
            add_window.destroy()
            tk.messagebox.showinfo("Success", "Statement added to repository.")
        
        ctk.CTkButton(
            button_frame,
            text="Save Statement",
            command=save_statement,
            font=("Arial", 12),
            fg_color="#1f5d3c"  # Green color
        ).pack(side="right", padx=10, pady=10)
    
    def update_repository_stats(self):
        """Update the repository statistics display"""
        self.statement_count_var.set(f"Total Statements: {len(self.value_statements)}")
        
        # Calculate percentage coverage (for demo purposes)
        total_associates = 54  # Pretend total company size
        coverage = min(100, round((len(self.value_statements) / total_associates) * 100))
        self.coverage_var.set(f"Associate Coverage: {coverage}%")
    
    def run_chorus_simulation(self):
        """Run the Habermas Chorus simulation"""
        if not self.value_statements:
            tk.messagebox.showinfo("Repository Empty", "Please add sample statements first.")
            return
            
        self.chorus_status_var.set("Generating...")
        
        # Start a new thread to avoid freezing the UI
        Thread(target=self.process_chorus_simulation, daemon=True).start()

    def process_chorus_simulation(self):
        """Process the chorus simulation in a separate thread using the LLM"""
        try:
            proposal_title = self.proposal_title.get()
            proposal_text = self.proposal_text.get("1.0", "end-1c")
            
            # Reset previous results
            self.simulation_results = []
            
            # Get filters
            dept_filter = self.dept_var.get()
            role_filter = self.role_var.get()
            location_filter = self.location_var.get()
            
            # Filter statements based on selected criteria
            filtered_statements = self.value_statements.copy()
            if dept_filter != "All Departments":
                filtered_statements = [s for s in filtered_statements if s["department"] == dept_filter]
            if role_filter != "All Roles":
                filtered_statements = [s for s in filtered_statements if s["role"] == role_filter]
            if location_filter != "All Locations":
                filtered_statements = [s for s in filtered_statements if s["location"] == location_filter]
            
            if not filtered_statements:
                self.app.root.after(0, lambda: tk.messagebox.showinfo("No Matching Statements", 
                                                                     "No statements match the selected filters. Try different criteria."))
                self.app.root.after(0, lambda: self.chorus_status_var.set("Ready"))
                return
                
            # Progress counter
            total_statements = len(filtered_statements)
            processed = 0
            
            # Update status
            self.app.root.after(0, lambda: self.chorus_status_var.set(f"Processing 0/{total_statements}..."))
            
            # Switch to the right tab to see the live updates
            self.app.right_column.lift()
            
            # Process each value statement to generate simulated response
            for value_statement in filtered_statements:
                if self.app.stop_event.is_set():
                    break
                
                # First update the LLM prompt panel to show what we're about to do
                resp_template = self.chorus_templates["response_simulation"]
                prompt = resp_template.format(
                    value_statement=value_statement["statement"],
                    department=value_statement["department"],
                    role=value_statement["role"],
                    location=value_statement["location"],
                    proposal_title=proposal_title,
                    proposal_description=proposal_text
                )
                
                # Update debug prompt display
                self.app.root.after(0, lambda p=prompt: self.app.update_debug_prompt(p))
                self.app.root.after(0, lambda: self.app.response_text.delete("1.0", "end"))
                self.app.root.after(0, lambda: self.app.flash_textbox(self.app.prompt_text))
                
                # Artificial pause to let the user see the prompt change
                time.sleep(0.5)
                
                # Generate simulated response using the LLM and Habermas template system
                response = self.generate_simulated_response(value_statement, proposal_title, proposal_text)
                if response:
                    self.simulation_results.append(response)
                
                # Update progress
                processed += 1
                self.app.root.after(0, lambda p=processed, t=total_statements: 
                                   self.chorus_status_var.set(f"Processing {p}/{t}..."))
                
                # Artificial pause to let the user see the response before moving to next
                time.sleep(0.5)
            
            # Update UI with actual results
            self.app.root.after(0, lambda: self.update_chorus_results(proposal_title, proposal_text))
            
        except Exception as e:
            print(f"Error in chorus simulation: {str(e)}")
            self.app.log_to_detailed(f"**Error in chorus simulation:** {str(e)}\n\n")
        finally:
            self.app.root.after(0, lambda: self.chorus_status_var.set("Complete"))
            
    def generate_simulated_response(self, value_statement, proposal_title, proposal_text):
        """Generate a simulated response using the LLM"""
        try:
            # Format the prompt
            prompt = self.chorus_templates["response_simulation"].format(
                value_statement=value_statement["statement"],
                department=value_statement["department"],
                role=value_statement["role"],
                location=value_statement["location"],
                proposal_title=proposal_title,
                proposal_description=proposal_text
            )
            
            # Log the prompt for debugging
            self.app.log_to_detailed(f"**Simulating response for {value_statement['department']}, {value_statement['role']} associate**\n\n")
            self.app.log_to_detailed(f"**Prompt:**\n```\n{prompt}\n```\n\n")
            
            # Prepare API call parameters
            model = self.app.model_var.get()
            try:
                temperature = float(self.app.temperature_var.get())
                top_p = float(self.app.top_p_var.get())
                top_k = int(self.app.top_k_var.get())
            except ValueError:
                temperature = 0.7
                top_p = 0.9
                top_k = 40
                
            # Make the API call (using the app's existing Ollama connection)
            try:
                self.app.current_response = requests.post(
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
                
                if self.app.current_response.status_code != 200:
                    error_msg = f"API Error: Status code {self.app.current_response.status_code}"
                    self.app.log_to_detailed(f"**Error:** {error_msg}\n\n")
                    # For the demo, fall back to mock data if API fails
                    return self.generate_mock_response(value_statement)
                
                # This is the key part - display the streamed response
                full_response = ""
                for line in self.app.current_response.iter_lines():
                    if self.app.stop_event.is_set():
                        break
                        
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if 'response' in data:
                                # Handle streamed text
                                response_text = data['response']
                                full_response += response_text
                                
                                # This is the critical part - update the debug response display
                                # in real time as the text comes in
                                self.app.root.after(0, lambda r=full_response: self.app.update_debug_response(r))
                                
                                # Also make debug panel visible and flash it to draw attention
                                self.app.root.after(0, lambda: self.app.flash_textbox(self.app.response_text))
                                
                                # Process UI events to ensure display updates
                                self.app.root.update_idletasks()
                        except json.JSONDecodeError:
                            self.app.log_to_detailed("**Error:** Failed to decode response from Ollama API\n\n")
                
                # Log the response
                self.app.log_to_detailed(f"**Raw Response:**\n\n```\n{full_response}\n```\n\n")
                
                # Clean up the response
                clean_response = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL).strip()
                
                # Parse the JSON response
                try:
                    # Try to find a JSON object within the text using more robust regex
                    match = re.search(r'(\{[\s\S]*\})', clean_response)
                    if match:
                        json_str = match.group(1)
                        # Debug the JSON string
                        self.app.log_to_detailed(f"**JSON string to parse:**\n```\n{json_str}\n```\n\n")
                        
                        # Clean the JSON string - this is critical for parsing
                        json_str = json_str.strip()
                        
                        # Try to parse the JSON
                        try:
                            response_data = json.loads(json_str)
                            
                            # Add metadata for easier processing
                            response_data["department"] = value_statement["department"]
                            response_data["role"] = value_statement["role"]
                            response_data["location"] = value_statement["location"]
                            
                            self.app.log_to_detailed(f"**USING REAL LLM RESPONSE - Successfully extracted JSON**\n\n")
                            return response_data
                        except json.JSONDecodeError as e:
                            self.app.log_to_detailed(f"**JSON parsing error on final object:** {str(e)}\n\n")
                            self.app.log_to_detailed(f"**Error at position {e.pos}:** Character '{json_str[e.pos]}'\n\n")
                            
                            # Try a more manual approach to clean problematic JSON
                            try:
                                # Use ast.literal_eval as a fallback
                                import ast
                                # Try to clean up the JSON string
                                cleaned_json_str = json_str.replace("'", '"').replace("\n", "").strip()
                                response_data = ast.literal_eval(cleaned_json_str)
                                
                                # Convert to proper dict if needed
                                if not isinstance(response_data, dict):
                                    response_data = dict(response_data)
                                
                                # Add metadata
                                response_data["department"] = value_statement["department"]
                                response_data["role"] = value_statement["role"]
                                response_data["location"] = value_statement["location"]
                                
                                self.app.log_to_detailed(f"**USING REAL LLM RESPONSE - Recovered with ast.literal_eval**\n\n")
                                return response_data
                            except Exception as ast_error:
                                self.app.log_to_detailed(f"**AST parsing error:** {str(ast_error)}\n\n")
                                # Fall back to mock data as last resort
                                return self.generate_mock_response(value_statement)
                    else:
                        self.app.log_to_detailed("**Error:** No JSON object found in response\n\n")
                        # Fall back to mock data for demo purposes
                        return self.generate_mock_response(value_statement)
                
                except Exception as e:
                    self.app.log_to_detailed(f"**Error processing response:** {str(e)}\n\n")
                    # Fall back to mock data for demo purposes
                    return self.generate_mock_response(value_statement)
                    
            except Exception as e:
                error_msg = f"Error generating response: {str(e)}"
                self.app.log_to_detailed(f"**Error:** {error_msg}\n\n")
                # Fall back to mock data for demo purposes
                return self.generate_mock_response(value_statement)
            finally:
                self.app.current_response = None
                
        except Exception as e:
            self.app.log_to_detailed(f"**Error in simulate_response:** {str(e)}\n\n")
            # Fall back to mock data for demo purposes
            return self.generate_mock_response(value_statement)
    
    def generate_mock_response(self, value_statement):
        """Generate a mock response for demo purposes if LLM fails"""
        # Create a mock response based on value statement content
        # This helps ensure the demo still works if Ollama isn't available
        mock_data = {
            "department": value_statement["department"],
            "role": value_statement["role"],
            "location": value_statement["location"]
        }
        
        # Analyze value statement for keywords to determine mock sentiment
        statement_lower = value_statement["statement"].lower()
        
        # Check for keywords that might indicate preferences
        if "remote" in statement_lower and "essential" in statement_lower:
            sentiment = "unfavorable"
            score = 2.5
        elif "balance" in statement_lower and "flexibility" in statement_lower:
            sentiment = "neutral"
            score = 5.0
        elif "in-person" in statement_lower or "office space" in statement_lower:
            sentiment = "favorable"
            score = 7.5
        else:
            # Random with weighted distribution
            sentiment_options = ["favorable", "neutral", "unfavorable"]
            sentiment = random.choices(sentiment_options, weights=[0.4, 0.3, 0.3])[0]
            
            if sentiment == "favorable":
                score = random.uniform(6.5, 9.0)
            elif sentiment == "neutral":
                score = random.uniform(4.0, 6.5)
            else:
                score = random.uniform(1.0, 4.0)
        
        # Common concerns based on role and location
        concerns = []
        if value_statement["location"] == "Remote":
            concerns.append("Significant change to current working arrangement")
        
        if "commute" in statement_lower or "45 minutes" in statement_lower:
            concerns.append("Long commute times")
        
        if "caregiv" in statement_lower:
            concerns.append("Caregiving responsibilities")
            
        # Add random general concerns if none specific were found
        if not concerns:
            possible_concerns = [
                "Work-life balance impact", 
                "Team coordination challenges",
                "Office space limitations",
                "Productivity concerns"
            ]
            concerns = random.sample(possible_concerns, k=min(2, len(possible_concerns)))
            
        # Generate suggestions
        suggestions = []
        if sentiment != "favorable":
            suggestions = [
                "Allow flexible scheduling of in-office days",
                "Reduce required office days to 2 per week"
            ]
            
        # Create mock response statement
        if sentiment == "favorable":
            statement = f"I support the hybrid work policy as it aligns with my values around {random.choice(['collaboration', 'team cohesion', 'office utilization'])}. The balance of 3 days in-office seems reasonable."
        elif sentiment == "neutral":
            statement = f"I see both benefits and drawbacks to this policy. While I value in-person collaboration, I'm concerned about {concerns[0] if concerns else 'the lack of flexibility'}."
        else:
            statement = f"I have significant concerns about this policy, particularly regarding {concerns[0] if concerns else 'work-life balance'}. I would strongly prefer more flexibility or fewer required in-office days."
            
        # Assemble complete mock response
        mock_data.update({
            "sentiment": sentiment,
            "score": round(score, 1),
            "concerns": concerns,
            "suggestions": suggestions,
            "statement": statement
        })
        
        self.app.log_to_detailed("**Using mock response due to API/parsing failure**\n\n")
        return mock_data
    
    def update_chorus_results(self, proposal_title, proposal_text):
        """Update the chorus results with actual simulation data"""
        if not self.simulation_results:
            # If no results, show error message
            self.summary_text.delete("1.0", "end")
            self.summary_text.insert("1.0", "# No Results\n\nThe simulation did not produce any results. Please try again.")
            return
            
        # Calculate statistics from actual results
        total = len(self.simulation_results)
        favorable = sum(1 for r in self.simulation_results if r.get("sentiment") == "favorable")
        neutral = sum(1 for r in self.simulation_results if r.get("sentiment") == "neutral")
        unfavorable = sum(1 for r in self.simulation_results if r.get("sentiment") == "unfavorable")
        
        favorable_pct = round((favorable / total) * 100) if total > 0 else 0
        neutral_pct = round((neutral / total) * 100) if total > 0 else 0
        unfavorable_pct = round((unfavorable / total) * 100) if total > 0 else 0
        
        # Count and rank concerns
        all_concerns = []
        for result in self.simulation_results:
            if "concerns" in result and result["concerns"]:
                all_concerns.extend(result["concerns"])
                
        concern_counts = {}
        for concern in all_concerns:
            if concern in concern_counts:
                concern_counts[concern] += 1
            else:
                concern_counts[concern] = 1
                
        # Get top concerns
        top_concerns = sorted(concern_counts.items(), key=lambda x: x[1], reverse=True)[:4]
        
        # Calculate average scores by location
        location_scores = {}
        for result in self.simulation_results:
            location = result.get("location", "Unknown")
            score = result.get("score", 5.0)
            
            if location not in location_scores:
                location_scores[location] = []
                
            location_scores[location].append(score)
            
        avg_location_scores = {loc: sum(scores)/len(scores) for loc, scores in location_scores.items()}
        
        # Generate key insight based on data
        key_insight = ""
        if len(avg_location_scores) > 1:
            max_loc = max(avg_location_scores.items(), key=lambda x: x[1])
            min_loc = min(avg_location_scores.items(), key=lambda x: x[1])
            
            if max_loc[1] - min_loc[1] > 2:
                key_insight = f"Location-based disparities emerged as a significant issue, with {max_loc[0]} associates (avg. score: {max_loc[1]:.1f}) being more supportive than {min_loc[0]} associates (avg. score: {min_loc[1]:.1f})."
        
        if not key_insight and top_concerns:
            key_insight = f"The most significant concern was '{top_concerns[0][0]}', mentioned by {top_concerns[0][1]} associates."
        
        # Generate the summary text
        summary_text = f"""
# Feedback Summary for: {proposal_title}

Based on simulated responses from {total} associates, the proposal received **{'positive' if favorable_pct > unfavorable_pct + 10 else 'mixed' if abs(favorable_pct - unfavorable_pct) <= 10 else 'negative'} reception**{' with some significant concerns.' if unfavorable_pct > 20 or neutral_pct > 30 else '.'}

## Quick Statistics:
- 🟢 Favorable: {favorable_pct}%
- 🟡 Neutral: {neutral_pct}% 
- 🔴 Unfavorable: {unfavorable_pct}%

## Top Themes:
"""

        # Add top concerns
        for i, (concern, count) in enumerate(top_concerns[:4], 1):
            concern_pct = round((count / total) * 100)
            summary_text += f"{i}. {concern} ({concern_pct}%)\n"
            
        # Add key insight if available
        if key_insight:
            summary_text += f"\n## Key Insight:\n{key_insight}\n"
            
        # Add a sample quote from the results
        if self.simulation_results:
            # Try to find a detailed statement
            statements = [r.get("statement", "") for r in self.simulation_results if len(r.get("statement", "")) > 50]
            if statements:
                summary_text += f"\n## Sample Feedback:\n\"{random.choice(statements)}\"\n"
            
        # Update the summary text
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", summary_text)
        
        # Update other tabs with actual data
        self.update_sentiment_chart_with_data()
        self.update_concerns_chart_with_data()
        self.update_suggestions_list_with_data()
        
        # Switch to Summary tab to show results
        self.results_tabview.set("Summary")
    
    def update_sentiment_chart_with_data(self):
        """Update the sentiment analysis chart with actual data"""
        sentiment_tab = self.results_tabview.tab("Sentiment Analysis")
        
        # Clear existing frame content
        for widget in self.sentiment_frame.winfo_children():
            widget.destroy()
        
        # Create new frame for charts
        chart_frame = ctk.CTkFrame(self.sentiment_frame)
        chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Calculate sentiment statistics
        total = len(self.simulation_results)
        if total == 0:
            # If no data, display message
            ctk.CTkLabel(chart_frame, text="No data available for visualization", 
                        font=("Arial", 14, "bold")).pack(pady=50)
            return
            
        favorable = sum(1 for r in self.simulation_results if r.get("sentiment") == "favorable")
        neutral = sum(1 for r in self.simulation_results if r.get("sentiment") == "neutral")
        unfavorable = sum(1 for r in self.simulation_results if r.get("sentiment") == "unfavorable")
        
        # Calculate department statistics
        dept_counts = {}
        for result in self.simulation_results:
            dept = result.get("department", "Unknown")
            sentiment = result.get("sentiment", "neutral")
            
            if dept not in dept_counts:
                dept_counts[dept] = {"favorable": 0, "neutral": 0, "unfavorable": 0, "total": 0}
                
            dept_counts[dept][sentiment] += 1
            dept_counts[dept]["total"] += 1
        
        # Calculate percentages for departments
        departments = []
        dept_favorable = []
        dept_neutral = []
        dept_unfavorable = []
        
        for dept, counts in dept_counts.items():
            if counts["total"] > 0:
                departments.append(dept)
                dept_favorable.append((counts["favorable"] / counts["total"]) * 100)
                dept_neutral.append((counts["neutral"] / counts["total"]) * 100)
                dept_unfavorable.append((counts["unfavorable"] / counts["total"]) * 100)
        
        # Create the sentiment chart
        if len(departments) <= 5:
            # Use 1x2 layout for fewer departments
            self.sentiment_fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6))
        else:
            # Use 2x1 layout for more departments
            self.sentiment_fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
            
        self.sentiment_fig.patch.set_facecolor('#2b2b2b')  # Dark background
        
        # Overall sentiment pie chart
        labels = ['Favorable', 'Neutral', 'Unfavorable']
        sizes = [favorable, neutral, unfavorable]
        colors = ['#4CAF50', '#FFC107', '#F44336']
        explode = (0.1, 0, 0)  # Explode the favorable slice
        
        ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                shadow=True, startangle=90, textprops={'color': 'white'})
        ax1.set_title('Overall Sentiment', color='white')
        
        # Sentiment by department bar chart (if departments exist)
        if departments:
            x = np.arange(len(departments))
            width = 0.25
            
            ax2.bar(x - width, dept_favorable, width, label='Favorable', color='#4CAF50')
            ax2.bar(x, dept_neutral, width, label='Neutral', color='#FFC107')
            ax2.bar(x + width, dept_unfavorable, width, label='Unfavorable', color='#F44336')
            
            ax2.set_ylabel('Percentage', color='white')
            ax2.set_title('Sentiment by Department', color='white')
            ax2.set_xticks(x)
            ax2.set_xticklabels(departments, rotation=45, ha='right', color='white')
            ax2.legend(loc='upper left')
            ax2.tick_params(axis='y', colors='white')
            ax2.spines['bottom'].set_color('white')
            ax2.spines['top'].set_color('white')
            ax2.spines['left'].set_color('white')
            ax2.spines['right'].set_color('white')
        
        plt.tight_layout()
        
        # Embed the matplotlib figure in the tkinter window
        canvas = FigureCanvasTkAgg(self.sentiment_fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Keep a reference to the canvas to prevent garbage collection
        self.sentiment_canvas = canvas
        
        # Add a second chart for scores by metadata
        self.create_scores_chart(chart_frame)
    
    def update_concerns_chart_with_data(self):
        """Update the key concerns chart with actual data"""
        concerns_tab = self.results_tabview.tab("Key Concerns")
        
        # Clear existing frame content
        for widget in self.concerns_frame.winfo_children():
            widget.destroy()
        
        # Check if we have results
        if not self.simulation_results:
            ctk.CTkLabel(self.concerns_frame, text="No data available for analysis", 
                        font=("Arial", 14, "bold")).pack(pady=50)
            return
            
        # Create scrollable frame for concerns
        concerns_scroll = ctk.CTkScrollableFrame(self.concerns_frame)
        concerns_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Count all concerns from the results
        all_concerns = []
        for result in self.simulation_results:
            if "concerns" in result and result["concerns"]:
                all_concerns.extend(result["concerns"])
                
        # Count frequencies
        concern_counts = {}
        for concern in all_concerns:
            concern = concern.strip()
            if concern in concern_counts:
                concern_counts[concern] += 1
            else:
                concern_counts[concern] = 1
                
        # Calculate percentages
        total_results = len(self.simulation_results)
        concern_percentages = {concern: (count / total_results) * 100 
                               for concern, count in concern_counts.items()}
        
        # Find statements that mention each concern
        concern_statements = {concern: [] for concern in concern_counts.keys()}
        
        for result in self.simulation_results:
            statement = result.get("statement", "")
            if statement and "concerns" in result:
                for concern in result["concerns"]:
                    concern = concern.strip()
                    if concern in concern_statements:
                        concern_statements[concern].append(statement)
        
        # If no concerns were found
        if not concern_counts:
            ctk.CTkLabel(concerns_scroll, text="No specific concerns were identified in the responses", 
                        font=("Arial", 14)).pack(pady=50)
            return
            
        # Add concern progress bars
        for concern, percentage in sorted(concern_percentages.items(), key=lambda x: x[1], reverse=True):
            concern_frame = ctk.CTkFrame(concerns_scroll)
            concern_frame.pack(fill="x", padx=5, pady=5, expand=True)
            
            # Concern text
            ctk.CTkLabel(concern_frame, text=concern, font=("Arial", 12, "bold"), 
                        anchor="w").pack(fill="x", padx=10, pady=(10, 5))
            
            # Progress bar frame
            bar_frame = ctk.CTkFrame(concern_frame)
            bar_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            # Progress bar
            progressbar = ctk.CTkProgressBar(bar_frame)
            progressbar.pack(side="left", fill="x", expand=True, padx=(0, 10))
            progressbar.set(percentage / 100)
            
            # Percentage label
            ctk.CTkLabel(bar_frame, text=f"{percentage:.1f}%").pack(side="right", padx=5)
            
            # Add example quotes if available
            statements = concern_statements.get(concern, [])
            if statements:
                quote_frame = ctk.CTkFrame(concern_frame)
                quote_frame.pack(fill="x", padx=10, pady=(0, 10))
                
                # Find a good sample quote (not too long, not too short)
                good_quotes = [s for s in statements if 30 <= len(s) <= 150]
                if good_quotes:
                    quote = random.choice(good_quotes)
                else:
                    quote = random.choice(statements)
                
                ctk.CTkLabel(quote_frame, text=f"\"{quote}\"", wraplength=600, 
                           font=("Arial", 12, "italic"), anchor="w").pack(fill="x", padx=10)
    
    def create_scores_chart(self, parent_frame):
        """Create a chart showing average scores by location and role"""
        # Calculate average scores by different metadata
        scores_by_location = {}
        scores_by_role = {}
        
        for result in self.simulation_results:
            score = result.get("score", 5.0)
            location = result.get("location", "Unknown")
            role = result.get("role", "Unknown")
            
            if location not in scores_by_location:
                scores_by_location[location] = []
            scores_by_location[location].append(score)
            
            if role not in scores_by_role:
                scores_by_role[role] = []
            scores_by_role[role].append(score)
            
        # Calculate averages
        avg_by_location = {loc: sum(scores)/len(scores) for loc, scores in scores_by_location.items()}
        avg_by_role = {role: sum(scores)/len(scores) for role, scores in scores_by_role.items()}
        
        # Create a new figure for the scores chart
        scores_fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        scores_fig.patch.set_facecolor('#2b2b2b')  # Dark background
        
        # Location scores
        locations = list(avg_by_location.keys())
        location_scores = list(avg_by_location.values())
        colors = ['#4CAF50' if score >= 6.5 else '#FFC107' if score >= 4.0 else '#F44336' 
                 for score in location_scores]
        
        ax1.bar(locations, location_scores, color=colors)
        ax1.set_ylim(0, 10)
        ax1.set_ylabel('Average Score (1-10)', color='white')
        ax1.set_title('Support by Location', color='white')
        ax1.set_xticklabels([''] + locations, rotation=45, ha='right', color='white')
        ax1.tick_params(axis='y', colors='white')
        ax1.spines['bottom'].set_color('white')
        ax1.spines['top'].set_color('white')
        ax1.spines['left'].set_color('white')
        ax1.spines['right'].set_color('white')
        
        # Role scores
        roles = list(avg_by_role.keys())
        role_scores = list(avg_by_role.values())
        colors = ['#4CAF50' if score >= 6.5 else '#FFC107' if score >= 4.0 else '#F44336' 
                 for score in role_scores]
        
        ax2.bar(roles, role_scores, color=colors)
        ax2.set_ylim(0, 10)
        ax2.set_title('Support by Role', color='white')
        ax2.set_xticklabels([''] + roles, rotation=45, ha='right', color='white')
        ax2.tick_params(axis='y', colors='white')
        ax2.spines['bottom'].set_color('white')
        ax2.spines['top'].set_color('white')
        ax2.spines['left'].set_color('white')
        ax2.spines['right'].set_color('white')
        
        plt.tight_layout()
        
        # Add some spacing
        spacer = ctk.CTkFrame(parent_frame, height=20)
        spacer.pack(fill="x")
        
        # Create a frame for the scores chart
        scores_frame = ctk.CTkFrame(parent_frame)
        scores_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add title
        ctk.CTkLabel(scores_frame, text="Support Level Analysis (1-10 scale)", 
                    font=("Arial", 14, "bold")).pack(padx=10, pady=5)
        
        # Embed the matplotlib figure
        canvas = FigureCanvasTkAgg(scores_fig, master=scores_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Keep a reference to prevent garbage collection
        self.scores_canvas = canvas
    
    def update_suggestions_list_with_data(self):
        """Update the suggestions list with actual data"""
        if not self.simulation_results:
            self.suggestions_text.delete("1.0", "end")
            self.suggestions_text.insert("1.0", "# No Data\n\nNo simulation results available to generate suggestions.")
            return
            
        # Extract all suggestions from the results
        all_suggestions = []
        for result in self.simulation_results:
            if "suggestions" in result and result["suggestions"]:
                all_suggestions.extend(result["suggestions"])
                
        # Count suggestion frequencies
        suggestion_counts = {}
        for suggestion in all_suggestions:
            suggestion = suggestion.strip()
            if suggestion in suggestion_counts:
                suggestion_counts[suggestion] += 1
            else:
                suggestion_counts[suggestion] = 1
        
        # Group similar suggestions using keyword matching
        grouped_suggestions = {
            "Flexibility": [],
            "Implementation": [],
            "Commute": [],
            "Accommodation": [],
            "Technology": [],
            "Other": []
        }
        
        for suggestion, count in suggestion_counts.items():
            suggestion_lower = suggestion.lower()
            if any(keyword in suggestion_lower for keyword in ["flexible", "flexibility", "schedule", "choice"]):
                grouped_suggestions["Flexibility"].append((suggestion, count))
            elif any(keyword in suggestion_lower for keyword in ["phased", "gradual", "pilot", "trial"]):
                grouped_suggestions["Implementation"].append((suggestion, count))
            elif any(keyword in suggestion_lower for keyword in ["commute", "traffic", "transit", "travel"]):
                grouped_suggestions["Commute"].append((suggestion, count))
            elif any(keyword in suggestion_lower for keyword in ["accommodation", "exempt", "exception"]):
                grouped_suggestions["Accommodation"].append((suggestion, count))
            elif any(keyword in suggestion_lower for keyword in ["technology", "equipment", "tool"]):
                grouped_suggestions["Technology"].append((suggestion, count))
            else:
                grouped_suggestions["Other"].append((suggestion, count))
        
        # Identify top suggestion and generate key recommendation
        top_suggestion = max(suggestion_counts.items(), key=lambda x: x[1], default=("", 0))
        key_recommendation = ""
        
        # Check for common themes in suggestions
        reduced_days = any("2 day" in s.lower() or "fewer day" in s.lower() or "reduce day" in s.lower() 
                          for s in suggestion_counts.keys())
        
        flexible_schedule = any("flexib" in s.lower() for s in suggestion_counts.keys())
        
        if reduced_days and flexible_schedule:
            key_recommendation = "The data suggests modifying the policy to **2 required in-office days** with additional flexible days coordinated at the team level would significantly increase favorability while maintaining the benefits of in-office collaboration."
        elif reduced_days:
            key_recommendation = "Consider reducing the required in-office days from 3 to 2 per week, as this was the most frequent suggestion across departments."
        elif flexible_schedule:
            key_recommendation = "Consider allowing more flexibility in which days associates come to the office rather than mandating specific days for everyone."
        elif top_suggestion[0]:
            key_recommendation = f"The most common suggestion was: {top_suggestion[0]}"
            
        # Generate suggestions text
        suggestions_text = "# Improvement Suggestions\n\n"
        suggestions_text += "Based on the simulated feedback, here are key suggestions to improve associate reception:\n\n"
        
        # Add categorized suggestions
        section_count = 1
        for category, suggestions in grouped_suggestions.items():
            if suggestions:
                suggestions.sort(key=lambda x: x[1], reverse=True)
                suggestions_text += f"## {section_count}. {category} Recommendations\n"
                for suggestion, count in suggestions[:3]:  # Top 3 per category
                    percentage = round((count / len(self.simulation_results)) * 100)
                    suggestions_text += f"- **{suggestion}** ({percentage}% of respondents)\n"
                suggestions_text += "\n"
                section_count += 1
        
        # Add key recommendation if available
        if key_recommendation:
            suggestions_text += "## Key Recommendation\n"
            suggestions_text += key_recommendation + "\n"
        
        self.suggestions_text.delete("1.0", "end")
        self.suggestions_text.insert("1.0", suggestions_text)

# Helper methods for implementing Chorus with LLM
def generate_simulated_response(statement, proposal, model, temperature=0.7):
    """
    Generate a simulated response from an associate based on their value statement and a proposal
    
    In a real implementation, this would:
    1. Use the LLM to predict how the associate would respond
    2. Include sentiment analysis
    3. Extract key concerns and suggestions
    
    For demo purposes, this returns mock data
    """
    # Mock implementation
    # In a real version, this would use the app.make_api_call method
    mock_responses = [
        {"sentiment": "favorable", "concerns": [], "suggestions": []},
        {"sentiment": "neutral", "concerns": ["commute time"], "suggestions": ["flexible days"]},
        {"sentiment": "unfavorable", "concerns": ["work-life balance", "childcare"], "suggestions": ["reduce days"]}
    ]
    
    return random.choice(mock_responses)
