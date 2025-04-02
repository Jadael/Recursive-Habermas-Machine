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
import traceback

class HabermasChorusExtension:
    """Extension class that adds Chorus functionality to the Habermas Machine"""
    
    def __init__(self, habermas_machine):
        """Initialize the extension with reference to the main app"""
        self.app = habermas_machine
        self.value_statements = []
        self.sample_statements_loaded = False
        self.filter_initialized = False
        
        # Default Chorus prompt templates
        self.default_chorus_templates = {
            "response_simulation": """You are simulating how an associate would respond to a proposal based on their statement.

Associate's Statement:
{value_statement}

Associate's Department: {department}
Associate's Role: {role}
Associate's Location: {location}

Proposal: {proposal_title}
Description: {proposal_description}

Based SOLELY on the associate's value statement and metadata, simulate how they would respond to this proposal. 

Your response MUST be formatted as a valid JSON object with the following structure:
{{
  "sentiment": "favorable|neutral|unfavorable",
  "score": 1|2|3|4|5|6|7|8|9|10,
  "concerns": ["keyword 1", "keyword 2"],
  "suggestions": ["suggestion 1", "suggestion 2"],
  "statement": "Their simulated response statement"
}}

Where:
- sentiment: Must be exactly one of: "favorable", "neutral", or "unfavorable"
- score: A number from 1-10 representing level of support (10 being highest)
- concerns: An array of specific one-word concerns as keywords, if any (can be empty array [])
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
        self.proposal_title.insert(0, "New Work Policy Proposal")
        self.proposal_text.insert("1.0", "This proposal aims to update our current workplace policies to better align with organizational goals and employee needs. Please provide your feedback based on your values and perspectives.")
        
        # Filter options
        filter_frame = ctk.CTkFrame(proposal_frame)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(filter_frame, text="Filter by:", font=("Arial", 12)).pack(side="left", padx=10)
        
        # Initialize filter variables
        self.dept_var = ctk.StringVar(value="All Departments")
        self.role_var = ctk.StringVar(value="All Roles")
        self.location_var = ctk.StringVar(value="All Locations")
        
        # Create dropdown frames to allow us to update them later
        self.dept_dropdown_frame = ctk.CTkFrame(filter_frame)
        self.dept_dropdown_frame.pack(side="left", padx=10)
        
        self.role_dropdown_frame = ctk.CTkFrame(filter_frame)
        self.role_dropdown_frame.pack(side="left", padx=10)
        
        self.location_dropdown_frame = ctk.CTkFrame(filter_frame)
        self.location_dropdown_frame.pack(side="left", padx=10)
        
        # Create initial dropdowns with default values
        self.dept_dropdown = ctk.CTkOptionMenu(
            self.dept_dropdown_frame, 
            variable=self.dept_var,
            values=["All Departments"]
        )
        self.dept_dropdown.pack(fill="both")
        
        self.role_dropdown = ctk.CTkOptionMenu(
            self.role_dropdown_frame, 
            variable=self.role_var,
            values=["All Roles"]
        )
        self.role_dropdown.pack(fill="both")
        
        self.location_dropdown = ctk.CTkOptionMenu(
            self.location_dropdown_frame, 
            variable=self.location_var,
            values=["All Locations"]
        )
        self.location_dropdown.pack(fill="both")
        
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
    
    def update_filter_dropdowns(self):
        """Update the filter dropdowns based on the current value statements"""
        if not self.value_statements:
            return
            
        # Extract unique values for each metadata field
        departments = set()
        roles = set()
        locations = set()
        
        for statement in self.value_statements:
            departments.add(statement.get("department", "Unknown"))
            roles.add(statement.get("role", "Unknown"))
            locations.add(statement.get("location", "Unknown"))
        
        # Create sorted lists with "All" option first
        dept_values = ["All Departments"] + sorted(list(departments))
        role_values = ["All Roles"] + sorted(list(roles))
        location_values = ["All Locations"] + sorted(list(locations))
        
        # Update the dropdowns with new values
        self.dept_dropdown.configure(values=dept_values)
        self.role_dropdown.configure(values=role_values)
        self.location_dropdown.configure(values=location_values)
        
        # Reset to "All" if the current value isn't in the new list
        if self.dept_var.get() not in dept_values:
            self.dept_var.set("All Departments")
        if self.role_var.get() not in role_values:
            self.role_var.set("All Roles")
        if self.location_var.get() not in location_values:
            self.location_var.set("All Locations")
    
    def add_sample_statements(self):
        """Add sample value statements to the repository"""
        sample_statements = [
            {
                "name": "Kermit the Frog",
                "department": "Operations",
                "role": "Director",
                "location": "HQ",
                "statement": "Hi-ho! Kermit the Frog here. I value being able to keep the show running despite the constant chaos. It's not easy being green and in charge! I need everyone to meet deadlines so we don't disappoint our audience. I appreciate when Miss Piggy doesn't karate chop other performers, when the Electric Mayhem shows up on time, and when we can get through just ONE rehearsal without an explosion or Crazy Harry blowing something up. I worry about keeping everyone's spirits up when reviews are bad, and I need time to play my banjo when stress levels get too high. Most importantly, I need Fozzie to stop asking if his jokes are funny when I'm trying to prevent the theater from flooding."
            },
            {
                "name": "Miss Piggy",
                "department": "Customer Service",
                "role": "Team Lead",
                "location": "HQ",
                "statement": "Moi does not appreciate being asked to fill out tedious forms. As the star of this organization, I DEMAND priority treatment, my own dressing room, and top billing in all company communications. I refuse to work with frogs who don't appreciate my talent or bears with terrible jokes. I value APPLAUSE and ADORATION from management! My unique perspective? I deserve better than this, and I'm willing to deliver a karate chop to anyone who says otherwise! HIIIII-YAH! I expect flexibility for my numerous publicity appearances and acting auditions. My beauty routine requires at least two hours each morning, so don't even THINK about early meetings."
            },
            {
                "name": "Fozzie Bear",
                "department": "HR",
                "role": "Associate",
                "location": "Regional Offices",
                "statement": "Hiya! Wocka wocka! I value a workplace where people laugh at my jokes! Or at least don't throw tomatoes at me. Did you hear the one about the workplace policy? It was so boring, even the paper couldn't take it stationary! Wocka wocka! I think meetings should start with a joke to lighten the mood. I worry about performing—I mean working—in front of tough crowds like Statler and Waldorf. I need reassurance that I'm doing a good job, and maybe some help writing better jokes? Also, my rubber chicken should qualify for the dependent care benefits program. My mother always said I'm special even when nobody laughs, so maybe create a position where that's okay? Fozzie Bear, ladies and gentlemen! Thank you! Thank you!"
            },
            {
                "name": "Gonzo",
                "department": "IT",
                "role": "Manager",
                "location": "Remote",
                "statement": "I value a workplace that lets me perform death-defying stunts with my computer equipment! Why type when you can bungee-jump while dictating emails? I need management to understand that sometimes I have to cancel meetings because I'm being shot out of a cannon. My best coding is done while hanging upside down, and my chicken Camilla deserves to be included in all team meetings. I propose replacing desk chairs with trampolines and installing trapeze swings in the hallways. Risk assessments? Those just get in the way of innovation! When servers crash, I want to crash with them—literally, through a wall of flaming servers! THAT'S entertainment... I mean, IT management!"
            },
            {
                "name": "Animal",
                "department": "Operations",
                "role": "Associate",
                "location": "Regional Offices",
                "statement": "DRUMS! DRUMS! WOMAN! DRUMS! NO MEETINGS! ANIMAL HATE PAPERWORK! WANT DRUM BREAK EVERY HOUR! NO PANTS POLICY! FOOD! FOOD! ANIMAL HUNGRY AT DESK! NEED DRUM IN BATHROOM! WOMAN! BOSS MAN TALK TOO MUCH! ANIMAL NEED CHAIN ON DESK! NO CHAIN, ANIMAL RUN WILD! COFFEE! COFFEE! MORE COFFEE! NO EARLY! LATE GOOD! DRUM ALL NIGHT! SLEEP AT WORK! WO-MAAAAAN!"
            },
            {
                "name": "Scooter",
                "department": "Operations",
                "role": "Associate",
                "location": "HQ",
                "statement": "I really value clear communication and advance notice for schedule changes so I can make sure everything's ready for showtime. It's important to me that we respect everyone's time and talents. My uncle who owns the theater—I mean company—taught me that good preparation prevents poor performance. I appreciate when managers provide constructive feedback instead of just throwing things. I think our workplace would improve with more organized storage systems and better emergency protocols for when acts go wrong. I'm happy to work late when needed, but some work-life balance would be nice so I can occasionally see my family (besides my uncle, of course)."
            },
            {
                "name": "Rowlf",
                "department": "Finance",
                "role": "Team Lead",
                "location": "HQ",
                "statement": "You know, I just want a workplace where I can tickle the ivories between spreadsheets. Numbers are a lot like music—it's all about finding the right rhythm. I don't need much, just a piano in the break room and maybe a policy that lets dogs nap under their desks after lunch. I think meetings could use more musical interludes—improves morale, you know? I've been around the block a few times, played every dive bar in town before landing this gig, so I value managers who understand sometimes you gotta howl at the moon a little to keep your sanity. Oh, and those quarterly reports would sound a lot better as ballads, just saying."
            },
            {
                "name": "Sam Eagle",
                "department": "HR",
                "role": "Director",
                "location": "HQ",
                "statement": "I believe in AMERICAN VALUES in the workplace! This means PATRIOTISM, DECENCY, and absolutely NO MORE Fozzie Bear joke emails! I propose mandatory flag salutes before meetings and the elimination of casual Fridays—professional attire ONLY! Lunch breaks should be limited to AMERICAN foods—no more of the Swedish Chef's incomprehensible foreign cuisine! I value PROPER PROCEDURES and DIGNIFIED CONDUCT, which means no more Animal in the supply closet! Remote work is for those lacking COMMITMENT to the AMERICAN WAY! The Muppet health plan should NOT cover rubber chicken-related injuries! These are my values, which are CORRECT and AMERICAN, unlike the rest of you weirdos!"
            },
            {
                "name": "Statler",
                "department": "Finance",
                "role": "Director",
                "location": "Remote",
                "statement": "What's this form for? Another harebrained HR scheme? In my day, we didn't have 'workplace values'—we had WORK! This looks like something dreamed up by consultants to justify their existence. You want my professional values? How about not wasting my time with ridiculous surveys! I value my retirement fund not being squandered on team-building exercises and fancy coffee machines. If management spent less time asking about our feelings and more time fixing that draft in the balcony, maybe I'd stop falling asleep during meetings! This whole exercise deserves a loud 'DO-HO-HO-HO!' Waste of time, just like this company!"
            },
            {
                "name": "Waldorf",
                "department": "Operations",
                "role": "Manager",
                "location": "Remote",
                "statement": "I tried to retire 30 years ago, but my pension's worth less than Fozzie's joke book! Now I'm stuck managing operations from my balcony seat. My workplace values? I value when the show is OVER! DO-HO-HO-HO! I suppose I value meetings that end early and expense reports that get approved without questions about my back pain medication. The young folks complain about work-life balance—I haven't had balance since 1976! I'd like a workplace where I don't have to explain technology to dinosaurs even older than me. And why is this form so small? I can barely read it! Is that part of your accessibility values? DO-HO-HO-HO!"
            },
            {
                "name": "Swedish Chef",
                "department": "IT",
                "role": "Team Lead",
                "location": "Regional Offices",
                "statement": "Børk! Børk! Børk! Zee vorkploose moost be like zee kitchen! Yuuu put de codey-wodey in de systemy-wistemy und BOOM! It vorks! No vorks? Throw de chicken at de computer! Børk! Børk! I velue de time for der experimenty mit der microsofty und der googly boogly. No likey der meetings vith no foody. All meetings moost have sneckies! Techno-bubble needs der flippity floppity und der BOOM CHICKA BOOM! Und most importanty, no pooter der herdy berdy in der fishy dishy vithout der proper backuppy. Børk! Børk! Børk!"
            },
            {
                "name": "Beaker",
                "department": "IT",
                "role": "Associate",
                "location": "HQ",
                "statement": "Meep meep meep meep! Meep meep meep meep meep meep meep. Meep meep? Meep meep meep meep meep meep, meep meep meep meep meep! MEEP MEEP MEEP! Meep meep meep, meep meep meep meep meep meep. Meep, meep meep meep meep meep meep meep meep-meep meep meep meep meep. Meep meep meep meep, meep meep; meep meep meep meep meep meep meep. Meep meep meep meep meep... meep meep meep meep meep meep meep. Meep meep meep? MEEEEEEEEEEP!"
            },
            {
                "name": "Dr. Bunsen Honeydew",
                "department": "IT",
                "role": "Director",
                "location": "HQ",
                "statement": "Greetings! I value a workplace that allows for scientific experimentation on—I mean WITH—my colleagues! I propose replacing our current feedback system with my new invention, the Performance-o-Meter, which administers mild electric shocks for substandard work! I believe coffee breaks should be used for testing new chemical compounds I've developed. Our servers would run 0.0037% more efficiently if we could harness the kinetic energy from Beaker's anxiety-induced trembling! I need budget approval for more bunsen burners at workstations and a company policy permitting the occasional workplace explosion in the name of progress. And finally, helmets should be mandatory during all meetings where I'm presenting new ideas!"
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
        
        # Get existing metadata values
        departments = set(["Customer Service", "IT", "HR", "Finance", "Operations"])
        roles = set(["Associate", "Team Lead", "Manager", "Director"])
        locations = set(["HQ", "Regional Offices", "Remote"])
        
        # Add values from existing statements
        for statement in self.value_statements:
            if "department" in statement:
                departments.add(statement["department"])
            if "role" in statement:
                roles.add(statement["role"])
            if "location" in statement:
                locations.add(statement["location"])
        
        # Department
        ctk.CTkLabel(info_frame, text="Department:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        dept_var = ctk.StringVar(value=next(iter(departments)) if departments else "")
        dept_entry = ctk.CTkComboBox(
            info_frame, 
            variable=dept_var,
            values=sorted(list(departments))
        )
        dept_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Role
        ctk.CTkLabel(info_frame, text="Role:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        role_var = ctk.StringVar(value=next(iter(roles)) if roles else "")
        role_entry = ctk.CTkComboBox(
            info_frame, 
            variable=role_var,
            values=sorted(list(roles))
        )
        role_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # Location
        ctk.CTkLabel(info_frame, text="Location:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        location_var = ctk.StringVar(value=next(iter(locations)) if locations else "")
        location_entry = ctk.CTkComboBox(
            info_frame, 
            variable=location_var,
            values=sorted(list(locations))
        )
        location_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
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
        """Update the repository statistics display and filter dropdowns"""
        self.statement_count_var.set(f"Total Statements: {len(self.value_statements)}")
        
        # Calculate percentage coverage (for demo purposes)
        total_associates = 54  # Pretend total company size
        coverage = min(100, round((len(self.value_statements) / total_associates) * 100))
        self.coverage_var.set(f"Associate Coverage: {coverage}%")
        
        # Update filter dropdowns with current metadata values
        self.update_filter_dropdowns()
    
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
                
                # Generate simulated response using the LLM
                response = self.generate_simulated_response(value_statement, proposal_title, proposal_text)
                if response:
                    self.simulation_results.append(response)
                
                # Update progress
                processed += 1
                self.app.root.after(0, lambda p=processed, t=total_statements: 
                                   self.chorus_status_var.set(f"Processing {p}/{t}..."))
                
                # Artificial pause to let the user see the response before moving to next
                time.sleep(0.5)
            
            # Update UI with results
            self.app.root.after(0, lambda: self.update_chorus_results(proposal_title, proposal_text))
            
        except Exception as e:
            error_msg = f"Error in chorus simulation: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            self.app.log_to_detailed(f"**Error in chorus simulation:** {error_msg}\n\n")
            self.app.log_to_detailed(f"**Traceback:**\n```\n{traceback.format_exc()}\n```\n\n")
            
            # Display error in UI
            self.app.root.after(0, lambda: self.summary_text.delete("1.0", "end"))
            self.app.root.after(0, lambda: self.summary_text.insert("1.0", f"# Error in Simulation\n\nAn error occurred: {error_msg}\n\nPlease check that Ollama is running correctly and try again."))
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
                    self.app.root.after(0, lambda: self.summary_text.delete("1.0", "end"))
                    self.app.root.after(0, lambda: self.summary_text.insert("1.0", f"# API Connection Error\n\n{error_msg}\n\nPlease check that Ollama is running correctly and try again."))
                    return None
                
                # Process the streamed response
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
                                
                                # Update the debug response display in real time
                                self.app.root.after(0, lambda r=full_response: self.app.update_debug_response(r))
                                
                                # Make debug panel visible and flash it to draw attention
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
                            
                            # Validate the required fields are present
                            required_fields = ["sentiment", "score", "concerns", "suggestions", "statement"]
                            for field in required_fields:
                                if field not in response_data:
                                    self.app.log_to_detailed(f"**Warning: Missing required field '{field}' in response data**\n\n")
                                    
                                    # Add default empty values for missing fields
                                    if field in ["concerns", "suggestions"]:
                                        response_data[field] = []
                                    elif field == "sentiment":
                                        response_data[field] = "neutral"
                                    elif field == "score":
                                        response_data[field] = 5.0
                                    elif field == "statement":
                                        response_data[field] = "(No response statement provided)"
                            
                            # Ensure sentiment is one of the allowed values
                            if response_data["sentiment"] not in ["favorable", "neutral", "unfavorable"]:
                                self.app.log_to_detailed(f"**Warning: Invalid sentiment '{response_data['sentiment']}', defaulting to 'neutral'**\n\n")
                                response_data["sentiment"] = "neutral"
                                
                            # Ensure score is a number between 1-10
                            try:
                                score = float(response_data["score"])
                                if score < 1 or score > 10:
                                    self.app.log_to_detailed(f"**Warning: Score {score} outside valid range (1-10), clamping**\n\n")
                                    response_data["score"] = max(1, min(10, score))
                            except (ValueError, TypeError):
                                self.app.log_to_detailed(f"**Warning: Invalid score value, defaulting to 5.0**\n\n")
                                response_data["score"] = 5.0
                            
                            # Ensure concerns and suggestions are lists
                            for field in ["concerns", "suggestions"]:
                                if not isinstance(response_data[field], list):
                                    self.app.log_to_detailed(f"**Warning: '{field}' is not a list, converting**\n\n")
                                    if isinstance(response_data[field], str):
                                        # Try to convert a string to a list if it looks like one
                                        if response_data[field].startswith("[") and response_data[field].endswith("]"):
                                            try:
                                                response_data[field] = json.loads(response_data[field])
                                            except:
                                                response_data[field] = [response_data[field]]
                                        else:
                                            response_data[field] = [response_data[field]]
                                    else:
                                        response_data[field] = []
                            
                            self.app.log_to_detailed(f"**Successfully extracted and validated response data**\n\n")
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
                                
                                self.app.log_to_detailed(f"**Recovered with ast.literal_eval**\n\n")
                                return response_data
                            except Exception as ast_error:
                                self.app.log_to_detailed(f"**AST parsing error:** {str(ast_error)}\n\n")
                                self.app.root.after(0, lambda: tk.messagebox.showerror(
                                    "JSON Parsing Error", 
                                    f"Could not parse LLM response for {value_statement['role']} in {value_statement['department']}.\n\nSkipping this response."
                                ))
                                return None
                    else:
                        self.app.log_to_detailed("**Error:** No JSON object found in response\n\n")
                        self.app.root.after(0, lambda: tk.messagebox.showerror(
                            "JSON Response Error", 
                            f"LLM did not return proper JSON format for {value_statement['role']} in {value_statement['department']}.\n\nSkipping this response."
                        ))
                        return None
                
                except Exception as e:
                    self.app.log_to_detailed(f"**Error processing response:** {str(e)}\n\n")
                    self.app.log_to_detailed(f"**Traceback:**\n```\n{traceback.format_exc()}\n```\n\n")
                    return None
                    
            except Exception as e:
                error_msg = f"Error generating response: {str(e)}"
                self.app.log_to_detailed(f"**Error:** {error_msg}\n\n")
                self.app.log_to_detailed(f"**Traceback:**\n```\n{traceback.format_exc()}\n```\n\n")
                return None
            finally:
                self.app.current_response = None
                
        except Exception as e:
            self.app.log_to_detailed(f"**Error in simulate_response:** {str(e)}\n\n")
            self.app.log_to_detailed(f"**Traceback:**\n```\n{traceback.format_exc()}\n```\n\n")
            return None
    
    def update_chorus_results(self, proposal_title, proposal_text):
        """Update the chorus results with simulation data"""
        if not self.simulation_results:
            # If no results, show error message
            self.summary_text.delete("1.0", "end")
            self.summary_text.insert("1.0", "# No Results\n\nThe simulation did not produce any results. Please try again with different parameters or check if Ollama is running correctly.")
            return
            
        # Calculate statistics from results
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
            concern = concern.strip()
            if concern in concern_counts:
                concern_counts[concern] += 1
            else:
                concern_counts[concern] = 1
                
        # Get top concerns
        top_concerns = sorted(concern_counts.items(), key=lambda x: x[1], reverse=True)[:4]
        
        # Calculate average scores by demographic factors
        location_scores = {}
        department_scores = {}
        role_scores = {}
        
        for result in self.simulation_results:
            location = result.get("location", "Unknown")
            department = result.get("department", "Unknown")
            role = result.get("role", "Unknown")
            score = result.get("score", 5.0)
            
            if location not in location_scores:
                location_scores[location] = []
            location_scores[location].append(score)
            
            if department not in department_scores:
                department_scores[department] = []
            department_scores[department].append(score)
            
            if role not in role_scores:
                role_scores[role] = []
            role_scores[role].append(score)
            
        avg_location_scores = {loc: sum(scores)/len(scores) for loc, scores in location_scores.items()}
        avg_department_scores = {dept: sum(scores)/len(scores) for dept, scores in department_scores.items()}
        avg_role_scores = {role: sum(scores)/len(scores) for role, scores in role_scores.items()}
        
        # Analyze for significant differences between demographics
        key_insights = []
        
        # Check for location disparities
        if len(avg_location_scores) > 1:
            max_loc = max(avg_location_scores.items(), key=lambda x: x[1])
            min_loc = min(avg_location_scores.items(), key=lambda x: x[1])
            
            if max_loc[1] - min_loc[1] > 2:
                key_insights.append(f"Significant disparity between {max_loc[0]} associates (avg. score: {max_loc[1]:.1f}) and {min_loc[0]} associates (avg. score: {min_loc[1]:.1f}).")
        
        # Check for department disparities
        if len(avg_department_scores) > 1:
            max_dept = max(avg_department_scores.items(), key=lambda x: x[1])
            min_dept = min(avg_department_scores.items(), key=lambda x: x[1])
            
            if max_dept[1] - min_dept[1] > 2:
                key_insights.append(f"{max_dept[0]} department (avg. score: {max_dept[1]:.1f}) significantly more favorable than {min_dept[0]} department (avg. score: {min_dept[1]:.1f}).")
        
        # Add insight about top concern if we have any
        if top_concerns:
            key_insights.append(f"The most significant concern was '{top_concerns[0][0]}', mentioned by {top_concerns[0][1]} associates.")
        
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
        if top_concerns:
            for i, (concern, count) in enumerate(top_concerns, 1):
                concern_pct = round((count / total) * 100)
                summary_text += f"{i}. {concern} ({concern_pct}%)\n"
        else:
            summary_text += "No specific concerns were frequently mentioned.\n"
            
        # Add key insights if available
        if key_insights:
            summary_text += f"\n## Key Insights:\n"
            for insight in key_insights:
                summary_text += f"- {insight}\n"
            
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
                
        if not suggestion_counts:
            self.suggestions_text.delete("1.0", "end")
            self.suggestions_text.insert("1.0", "# No Suggestions\n\nNo specific suggestions were provided in the feedback.")
            return
        
        # Identify common keywords in suggestions to create categories dynamically
        keywords = {}
        for suggestion in suggestion_counts.keys():
            suggestion_lower = suggestion.lower()
            words = re.findall(r'\b\w+\b', suggestion_lower)
            for word in words:
                if len(word) > 3:  # Only consider words longer than 3 characters
                    if word in keywords:
                        keywords[word] += 1
                    else:
                        keywords[word] = 1
        
        # Find top keywords to use as categories
        top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:5]
        top_keywords = [k for k, v in top_keywords if v > 1]  # Only use keywords that appear multiple times
        
        # Create categories dynamically based on common keywords
        categories = {}
        for keyword in top_keywords:
            categories[keyword.title()] = []
        
        # Add an "Other" category
        categories["Other"] = []
        
        # Group suggestions into categories
        for suggestion, count in suggestion_counts.items():
            suggestion_lower = suggestion.lower()
            
            # Check which category this suggestion fits into
            categorized = False
            for keyword in top_keywords:
                if keyword in suggestion_lower:
                    categories[keyword.title()].append((suggestion, count))
                    categorized = True
                    break
                    
            # If not categorized, put in "Other"
            if not categorized:
                categories["Other"].append((suggestion, count))
        
        # Remove empty categories
        categories = {k: v for k, v in categories.items() if v}
        
        # Identify top suggestion and generate key recommendation
        top_suggestion = max(suggestion_counts.items(), key=lambda x: x[1], default=("", 0))
        
        # Generate a dynamic key recommendation based on the data
        key_recommendation = ""
        if top_suggestion[0]:
            # Calculate what percentage of responses included this suggestion
            suggestion_percentage = round((top_suggestion[1] / len(self.simulation_results)) * 100)
            key_recommendation = f"The most frequent suggestion ({suggestion_percentage}% of responses) was: \"{top_suggestion[0]}\""
            
        # Generate suggestions text
        suggestions_text = "# Improvement Suggestions\n\n"
        
        if all_suggestions:
            suggestions_text += "Based on the simulated feedback, here are key suggestions to improve reception:\n\n"
            
            # Add categorized suggestions
            section_count = 1
            for category, suggestions in categories.items():
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
        else:
            suggestions_text += "No specific suggestions were provided in the feedback responses."
        
        self.suggestions_text.delete("1.0", "end")
        self.suggestions_text.insert("1.0", suggestions_text)
