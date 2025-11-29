"""
Habermas Machine with Chorus
A unified application for AI-assisted consensus building and feedback analysis
"""

import tkinter as tk
import tkinter.messagebox as messagebox
import traceback
import sys
import os
import logging
import json
import time
import random
import re
from collections import defaultdict
import math
import datetime
import numpy as np
from threading import Thread, Event
import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend for embedding in Tkinter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import List, Dict, Tuple, Any, Optional, Union

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
    from PIL import Image, ImageTk
    import requests
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

class VerbalSamplingManager:
    """Helper class to manage diverse sampling of verbatim quotes"""
    
    def __init__(self):
        self.used_quotes = set()  # Track quotes that have been used to avoid repetition
    
    def reset(self):
        """Reset the tracking of used quotes"""
        self.used_quotes = set()
    
    def get_embedding(self, text, model="all-MiniLM-L6-v2"):
        """Get embedding vector for a text using available models"""
        try:
            # Try to use sentence-transformers if available
            from sentence_transformers import SentenceTransformer
            embedding_model = SentenceTransformer(model)
            return embedding_model.encode(text)
        except ImportError:
            # Fallback to simple tf-idf like approach if no embedding libraries available
            words = re.findall(r'\b\w+\b', text.lower())
            # Simple term frequency as embedding
            unique_words = list(set(words))
            return np.array([words.count(word)/len(words) for word in unique_words])
    
    def compute_diversity_score(self, candidates, selected=None):
        """Compute diversity score based on text similarity"""
        if selected is None:
            selected = []
        
        if not selected:
            return [(c, 1.0) for c in candidates]  # All equally diverse if nothing selected yet
        
        # Try to use embeddings if possible
        try:
            # Compute embeddings
            candidate_embeddings = [self.get_embedding(c) for c in candidates]
            selected_embeddings = [self.get_embedding(s) for s in selected]
            
            # Compute similarity scores
            similarity_scores = []
            for i, c_emb in enumerate(candidate_embeddings):
                # Average similarity to selected items
                sims = [cosine_similarity([c_emb], [s_emb])[0][0] for s_emb in selected_embeddings]
                avg_sim = np.mean(sims) if sims else 0
                diversity_score = 1.0 - avg_sim  # Higher score means more diverse
                similarity_scores.append((candidates[i], diversity_score))
            
            return similarity_scores
            
        except Exception as e:
            # Fallback to word-based diversity
            print(f"Embedding-based diversity calculation failed: {e}. Using fallback method.")
            
            diversity_scores = []
            for candidate in candidates:
                # Simple word overlap measures
                candidate_words = set(re.findall(r'\b\w+\b', candidate.lower()))
                avg_overlap = 0
                for sel in selected:
                    sel_words = set(re.findall(r'\b\w+\b', sel.lower()))
                    if sel_words:
                        overlap = len(candidate_words.intersection(sel_words)) / len(sel_words)
                        avg_overlap += overlap
                
                if selected:
                    avg_overlap /= len(selected)
                
                diversity_score = 1.0 - avg_overlap
                diversity_scores.append((candidate, diversity_score))
            
            return diversity_scores
    
    def compute_relevance_score(self, texts, keyword):
        """Score texts based on relevance to a keyword"""
        if not keyword:
            return [(text, 1.0) for text in texts]
        
        try:
            # Try to use sentence-transformers for semantic relevance
            keyword_emb = self.get_embedding(keyword)
            text_embs = [self.get_embedding(text) for text in texts]
            
            # Using sklearn's cosine_similarity
            try:
                from sklearn.metrics.pairwise import cosine_similarity
                relevance_scores = []
                for i, text_emb in enumerate(text_embs):
                    relevance = cosine_similarity([keyword_emb], [text_emb])[0][0]
                    relevance_scores.append((texts[i], relevance))
                
                return relevance_scores
            except ImportError:
                # Manual cosine similarity calculation
                relevance_scores = []
                for i, text_emb in enumerate(text_embs):
                    # Compute cosine similarity manually
                    dot_product = np.dot(keyword_emb, text_emb)
                    norm_prod = np.linalg.norm(keyword_emb) * np.linalg.norm(text_emb)
                    relevance = dot_product / norm_prod if norm_prod != 0 else 0
                    relevance_scores.append((texts[i], relevance))
                
                return relevance_scores
            
        except Exception as e:
            # Fallback to keyword occurrence
            print(f"Embedding-based relevance calculation failed: {e}. Using fallback method.")
            
            relevance_scores = []
            keyword_lower = keyword.lower()
            for text in texts:
                # Count occurrences of keyword
                text_lower = text.lower()
                # Basic relevance score based on keyword occurrences
                count = text_lower.count(keyword_lower)
                # Check if any similar words appear (simple stemming)
                if len(keyword) > 4:
                    stem = keyword_lower[:4]
                    count += len(re.findall(r'\b' + re.escape(stem) + r'\w*\b', text_lower)) * 0.5
                
                relevance_scores.append((text, count + 0.1))  # Small base score
            
            # Normalize scores
            max_score = max([score for _, score in relevance_scores]) if relevance_scores else 1
            if max_score > 0:
                relevance_scores = [(text, score/max_score) for text, score in relevance_scores]
            
            return relevance_scores
    
    def select_diverse_statements(self, statements, keyword=None, n=3, exclude_used=True):
        """
        Select n diverse statements that are relevant to a keyword
        
        Args:
            statements: List of statements to choose from
            keyword: Keyword to measure relevance against
            n: Number of statements to select
            exclude_used: Whether to exclude previously used statements
            
        Returns:
            List of selected statements
        """
        if not statements:
            return []
            
        # Filter out previously used statements if requested
        available_statements = [s for s in statements if s not in self.used_quotes] if exclude_used else statements
        
        # If we don't have enough, just use what we have
        if len(available_statements) <= n:
            selected = available_statements
            self.used_quotes.update(available_statements)
            return selected
            
        # Greedy selection of diverse and relevant statements
        selected = []
        
        # First, rank by relevance to keyword
        relevance_scores = self.compute_relevance_score(available_statements, keyword)
        relevance_scores = sorted(relevance_scores, key=lambda x: x[1], reverse=True)
        
        # Take the most relevant statement first
        best_statement = relevance_scores[0][0]
        selected.append(best_statement)
        
        # Now select the rest based on diversity
        remaining = [s for s in available_statements if s != best_statement]
        
        while len(selected) < n and remaining:
            # Score remaining statements based on diversity from already selected ones
            diversity_scores = self.compute_diversity_score(remaining, selected)
            
            # Get relevance scores for remaining
            relevance_scores = dict(self.compute_relevance_score(remaining, keyword))
            
            # Combine relevance and diversity (balance between the two)
            combined_scores = [(stmt, 0.6 * div_score + 0.4 * relevance_scores.get(stmt, 0.1)) 
                              for stmt, div_score in diversity_scores]
            
            # Select the one with highest combined score
            combined_scores.sort(key=lambda x: x[1], reverse=True)
            best_statement = combined_scores[0][0]
            
            selected.append(best_statement)
            remaining.remove(best_statement)
        
        # Mark these as used
        self.used_quotes.update(selected)
        
        return selected


class OllamaIntegration:
    """Helper class to integrate with Ollama for embeddings and summarization"""
    
    def __init__(self, base_url="http://localhost:11434", model=None):
        self.base_url = base_url
        self.model = model or "deepseek-r1:14b"  # Default model
        self.embedding_model = "nomic-embed-text"  # Default embedding model
        self.available = self._check_availability()
    
    def _check_availability(self):
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def get_embedding(self, text):
        """Get embedding vector for a text using Ollama"""
        if not self.available or not text:
            return None
            
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.embedding_model, "prompt": text},
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"Error getting embedding: Status code {response.status_code}")
                return None
                
            embedding = response.json().get("embedding")
            return np.array(embedding) if embedding else None
            
        except Exception as e:
            print(f"Error getting embedding: {str(e)}")
            return None
    
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
            self.log_to_detailed(f"**Model:** {self.model_var.get()}  \n")
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
                    # Save friendly output
                    friendly_path = f"habermas_recursive_results_{self.session_id}.md"
                    with open(friendly_path, 'w', encoding='utf-8') as file:
                        file.write(self.friendly_output.get("1.0", "end-1c"))
                    
                    # Save detailed output
                    detailed_path = f"habermas_recursive_detailed_{self.session_id}.md"
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
        
        # Set to dull purple
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
        
        self.log_to_friendly("\n**Process stopped by user.**\n")
        self.log_to_detailed("\n**Process stopped by user.**\n")
        
        self.friendly_status_var.set("Stopped")
        self.detailed_status_var.set("Stopped")
    
    #
    # Habermas Chorus Methods
    #
    
    def load_sample_data(self):
        """Load sample participant statements for both Habermas Machine and Chorus"""
        # Load sample participant statements for Habermas Machine
        sample_participants = [
            "I believe voting should not be compulsory. It's a fundamental right, but also a personal choice. Forcing people to vote might lead to uninformed voting which could harm democracy. I think we should focus on making voting easier and educating people on its importance instead.",
            "I firmly believe that voting should be compulsory. Democracy only works when people participate, and too many people don't vote out of apathy rather than principled objection. In Australia, compulsory voting has led to higher turnout and a more representative government. The civic duty to vote outweighs individual inconvenience.",
            "While I understand the democratic importance of voting, making it compulsory seems problematic. People shouldn't be forced to participate in a system they might fundamentally disagree with. Instead, we should address the root causes of low voter turnout like inaccessibility, lack of faith in the system, and voter suppression.",
            "I'm on the fence about compulsory voting. On one hand, it ensures broader representation and forces politicians to appeal to all segments of society. On the other hand, it's coercive and might lead to random voting. Perhaps a middle ground is a small incentive for voting rather than a punishment for not voting.",
            "Voting should absolutely be compulsory with reasonable exemptions for those who cannot vote. Democracy requires participation, and treating voting as optional has led to lower turnout among disadvantaged groups. Compulsory voting ensures everyone has a stake in the outcome and reduces political polarization by requiring appeal to the majority."
        ]

        # Set them in the textbox
        self.participants_text.delete("1.0", "end")
        self.participants_text.insert("1.0", "\n".join(sample_participants))
        self.update_participant_count()
    
    def view_repository(self):
        """Display the value statement repository in a new window"""
        if not self.value_statements:
            tk.messagebox.showinfo("Repository Empty", "The repository is empty. Add sample statements first.")
            return
            
        repo_window = ctk.CTkToplevel(self.root)
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
        
        # Mark filter as initialized
        self.filter_initialized = True
    
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
                "name": "Sam Eagle",
                "department": "HR",
                "role": "Director",
                "location": "HQ",
                "statement": "I believe in AMERICAN VALUES in the workplace! This means PATRIOTISM, DECENCY, and absolutely NO MORE Fozzie Bear joke emails! I propose mandatory flag salutes before meetings and the elimination of casual Fridays—professional attire ONLY! Lunch breaks should be limited to AMERICAN foods—no more of the Swedish Chef's incomprehensible foreign cuisine! I value PROPER PROCEDURES and DIGNIFIED CONDUCT, which means no more Animal in the supply closet! Remote work is for those lacking COMMITMENT to the AMERICAN WAY! The Muppet health plan should NOT cover rubber chicken-related injuries! These are my values, which are CORRECT and AMERICAN, unlike the rest of you weirdos!"
            }
        ]
        
        # Add sample statements if not already added
        if not self.sample_statements_loaded:
            self.value_statements = sample_statements
            self.sample_statements_loaded = True
            self.update_repository_stats()
            self.update_filter_dropdowns()
            tk.messagebox.showinfo("Success", "Sample statements added to repository.")
        else:
            tk.messagebox.showinfo("Already Loaded", "Sample statements are already loaded.")
    
    def add_new_statement(self):
        """Open a dialog to add a new value statement"""
        add_window = ctk.CTkToplevel(self.root)
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
            self.update_filter_dropdowns()
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
            
        # Clear the stop event
        self.stop_event.clear()
        
        # Update UI to show we're generating
        self.root.after(0, lambda: self.results_tabview.set("Chorus Summary"))
        
        # Start a new thread to avoid freezing the UI
        Thread(target=self.process_chorus_simulation, daemon=True).start()
    
    def process_chorus_simulation(self):
        """Process the chorus simulation in a separate thread using the LLM"""
        try:
            proposal_title = self.proposal_title.get()
            proposal_text = self.proposal_text.get("1.0", "end-1c")
            
            # Reset previous results
            self.simulation_results = []
            
            # Reset the verbal sampling manager for fresh sampling
            self.verbal_sampling_manager.reset()
            
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
                self.root.after(0, lambda: tk.messagebox.showinfo("No Matching Statements", 
                                                                "No statements match the selected filters. Try different criteria."))
                return
                
            # Progress counter
            total_statements = len(filtered_statements)
            processed = 0
            
            # Update UI status
            self.root.after(0, lambda: self.summary_text.delete("1.0", "end"))
            self.root.after(0, lambda: self.summary_text.insert("1.0", f"# Processing Feedback\n\nGenerating responses for {total_statements} associates...\n\n0/{total_statements} completed"))
            
            # Process each value statement to generate simulated response
            for value_statement in filtered_statements:
                if self.stop_event.is_set():
                    break
                
                # First update the LLM prompt panel to show what we're about to do
                resp_template = self.prompt_templates["response_simulation"]
                prompt = resp_template.format(
                    value_statement=value_statement["statement"],
                    department=value_statement["department"],
                    role=value_statement["role"],
                    location=value_statement["location"],
                    proposal_title=proposal_title,
                    proposal_description=proposal_text
                )
                
                # Update debug prompt display
                self.root.after(0, lambda p=prompt: self.update_debug_prompt(p))
                self.root.after(0, lambda: self.response_text.delete("1.0", "end"))
                self.root.after(0, lambda: self.flash_textbox(self.prompt_text))
                
                # Generate simulated response using the LLM
                response = self.generate_simulated_response(value_statement, proposal_title, proposal_text)
                if response:
                    self.simulation_results.append(response)
                
                # Update progress
                processed += 1
                self.root.after(0, lambda p=processed, t=total_statements: 
                               self.summary_text.delete("1.0", "end"))
                self.root.after(0, lambda p=processed, t=total_statements: 
                               self.summary_text.insert("1.0", f"# Processing Feedback\n\nGenerating responses for {t} associates...\n\n{p}/{t} completed"))
                
                # Process UI events to ensure display updates
                self.root.update_idletasks()
            
            # Update UI with results
            self.root.after(0, lambda: self.update_chorus_results(proposal_title, proposal_text))
            
        except Exception as e:
            error_msg = f"Error in chorus simulation: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            
            # Display error in UI
            self.root.after(0, lambda: self.summary_text.delete("1.0", "end"))
            self.root.after(0, lambda: self.summary_text.insert("1.0", f"# Error in Simulation\n\nAn error occurred: {error_msg}\n\nPlease check that Ollama is running correctly and try again."))
    
    def generate_simulated_response(self, value_statement, proposal_title, proposal_text):
        """Generate a simulated response using the LLM"""
        try:
            # Format the prompt
            prompt = self.prompt_templates["response_simulation"].format(
                value_statement=value_statement["statement"],
                department=value_statement["department"],
                role=value_statement["role"],
                location=value_statement["location"],
                proposal_title=proposal_title,
                proposal_description=proposal_text
            )
            
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
                    error_msg = f"API Error: Status code {self.current_response.status_code}"
                    print(error_msg)
                    return None
                
                # Process the streamed response
                full_response = ""
                for line in self.current_response.iter_lines():
                    if self.stop_event.is_set():
                        break
                        
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if 'response' in data:
                                # Handle streamed text
                                response_text = data['response']
                                full_response += response_text
                                
                                # Update the debug response display in real time
                                self.root.after(0, lambda r=full_response: self.update_debug_response(r))
                                
                                # Process UI events to ensure display updates
                                self.root.update_idletasks()
                        except json.JSONDecodeError:
                            pass
                
                # Clean up the response
                clean_response = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL).strip()
                
                # Parse the JSON response
                try:
                    # Try to find a JSON object within the text using more robust regex
                    match = re.search(r'(\{[\s\S]*\})', clean_response)
                    if match:
                        json_str = match.group(1)
                        
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
                                    print(f"Warning: Missing required field '{field}' in response data")
                                    
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
                                print(f"Warning: Invalid sentiment '{response_data['sentiment']}', defaulting to 'neutral'")
                                response_data["sentiment"] = "neutral"
                                
                            # Ensure score is a number between 1-10
                            try:
                                score = float(response_data["score"])
                                if score < 1 or score > 10:
                                    print(f"Warning: Score {score} outside valid range (1-10), clamping")
                                    response_data["score"] = max(1, min(10, score))
                            except (ValueError, TypeError):
                                print(f"Warning: Invalid score value, defaulting to 5.0")
                                response_data["score"] = 5.0
                            
                            # Ensure concerns and suggestions are lists
                            for field in ["concerns", "suggestions"]:
                                if not isinstance(response_data[field], list):
                                    print(f"Warning: '{field}' is not a list, converting")
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
                            
                            return response_data
                            
                        except json.JSONDecodeError as e:
                            print(f"JSON parsing error on final object: {str(e)}")
                            
                            # Try a more manual approach to clean problematic JSON
                            try:
                                # Use eval as a fallback (not ideal but workable in this controlled context)
                                cleaned_json_str = json_str.replace("'", '"').replace("\n", "").strip()
                                response_data = eval("(" + cleaned_json_str + ")")
                                
                                # Add metadata
                                response_data["department"] = value_statement["department"]
                                response_data["role"] = value_statement["role"]
                                response_data["location"] = value_statement["location"]
                                
                                return response_data
                            except Exception as eval_error:
                                print(f"Eval parsing error: {str(eval_error)}")
                                return None
                    else:
                        print("Error: No JSON object found in response")
                        return None
                
                except Exception as e:
                    print(f"Error processing response: {str(e)}")
                    return None
                    
            except Exception as e:
                print(f"Error generating response: {str(e)}")
                return None
            finally:
                self.current_response = None
                
        except Exception as e:
            print(f"Error in generate_simulated_response: {str(e)}")
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
        
        # Find statements that mention each concern
        concern_statements = {concern: [] for concern in concern_counts.keys()}
        
        for result in self.simulation_results:
            statement = result.get("statement", "")
            if statement and "concerns" in result:
                for concern in result["concerns"]:
                    concern = concern.strip()
                    if concern in concern_statements:
                        concern_statements[concern].append(statement)
        
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
        
        # Select representative statements for sentiment categories
        favorable_statements = [r.get("statement", "") for r in self.simulation_results if r.get("sentiment") == "favorable"]
        neutral_statements = [r.get("statement", "") for r in self.simulation_results if r.get("sentiment") == "neutral"]
        unfavorable_statements = [r.get("statement", "") for r in self.simulation_results if r.get("sentiment") == "unfavorable"]
        
        # Get representative verbatim quotes for each sentiment
        representative_statements = []
        
        # Get unfavorable statements if they exist (highest priority since they indicate concerns)
        if unfavorable_statements:
            unfavorable_samples = self.verbal_sampling_manager.select_diverse_statements(
                unfavorable_statements, n=min(2, len(unfavorable_statements))
            )
            representative_statements.extend(unfavorable_samples)
        
        # Get favorable statements if they exist
        if favorable_statements:
            favorable_samples = self.verbal_sampling_manager.select_diverse_statements(
                favorable_statements, n=min(2, len(favorable_statements))
            )
            representative_statements.extend(favorable_samples)
        
        # Add neutral if needed and we still want more samples
        if neutral_statements and len(representative_statements) < 3:
            neutral_samples = self.verbal_sampling_manager.select_diverse_statements(
                neutral_statements, n=min(1, len(neutral_statements))
            )
            representative_statements.extend(neutral_samples)
        
        # Truncate to a maximum of 3 statements
        representative_statements = representative_statements[:3]
        
        # Try to generate a better summary with the LLM if available
        summary_text = None
        if self.ollama.available:
            summary_text = self.ollama.summarize_feedback(
                self.simulation_results,
                proposal_title,
                proposal_text,
                representative_statements=representative_statements,
                top_concerns=top_concerns
            )
            
        # If LLM summary not available, generate a basic one
        if not summary_text:
            # Generate the summary text
            summary_text = f"# Feedback Summary for: {proposal_title}\n\n"
            
            # Overall sentiment assessment
            sentiment_description = "positive" if favorable_pct > unfavorable_pct + 10 else "mixed" if abs(favorable_pct - unfavorable_pct) <= 10 else "negative"
            concern_note = " with some significant concerns." if unfavorable_pct > 20 or neutral_pct > 30 else "."
            
            summary_text += f"Based on simulated responses from {total} associates, the proposal received **{sentiment_description} reception**{concern_note}\n\n"
            
            # Quick statistics
            summary_text += "## Quick Statistics:\n"
            summary_text += f"- 🟢 Favorable: {favorable_pct}%\n"
            summary_text += f"- 🟡 Neutral: {neutral_pct}% \n"
            summary_text += f"- 🔴 Unfavorable: {unfavorable_pct}%\n\n"
            
            # Top themes/concerns
            summary_text += "## Top Themes:\n"
            if top_concerns:
                for i, (concern, count) in enumerate(top_concerns, 1):
                    concern_pct = round((count / total) * 100)
                    summary_text += f"{i}. {concern} ({concern_pct}%)\n"
            else:
                summary_text += "No specific concerns were frequently mentioned.\n"
                
            # Add key insights about department differences
            dept_insights = []
            for dept, avg_score in avg_department_scores.items():
                if avg_score < 4.0:
                    dept_insights.append(f"- {dept} department responded particularly negatively (avg. score: {avg_score:.1f}/10)")
                elif avg_score > 7.0:
                    dept_insights.append(f"- {dept} department responded particularly positively (avg. score: {avg_score:.1f}/10)")
            
            if dept_insights:
                summary_text += "\n## Key Insights:\n"
                for insight in dept_insights:
                    summary_text += f"{insight}\n"
                    
                if top_concerns:
                    summary_text += f"- The most significant concern was '{top_concerns[0][0]}', mentioned by {top_concerns[0][1]} associates.\n"
            
            # Add representative verbatim quotes
            if representative_statements:
                summary_text += "\n## Sample Feedback:\n"
                for stmt in representative_statements:
                    summary_text += f"\"{stmt}\"\n\n"
        
        # Update the summary textbox
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", summary_text)
        
        # Update other visualization tabs
        self.update_sentiment_chart_with_data()
        self.update_concerns_chart_with_data()
        self.update_suggestions_list_with_data()
    
    def update_sentiment_chart_with_data(self):
        """Update the sentiment analysis chart with actual data"""
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
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6))
        fig.patch.set_facecolor('#2b2b2b')  # Dark background
        
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
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Create a second chart for scores by metadata
        self.create_scores_chart(chart_frame)
    
    def create_scores_chart(self, parent_frame):
        """Create a chart showing average scores by location and role"""
        # Calculate average scores by different metadata
        scores_by_location = {}
        scores_by_role = {}
        
        for result in self.simulation_results:
            score = float(result.get("score", 5.0))
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
    
    def update_concerns_chart_with_data(self):
        """Update the key concerns chart with actual data and improved sampling"""
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
                # Select diverse statements relevant to this concern
                diverse_quotes = self.verbal_sampling_manager.select_diverse_statements(
                    statements, concern, n=min(3, len(statements))
                )
                
                # Add each quote in its own frame
                for quote in diverse_quotes:
                    quote_frame = ctk.CTkFrame(concern_frame)
                    quote_frame.pack(fill="x", padx=10, pady=(0, 5))
                    
                    ctk.CTkLabel(quote_frame, text=f"\"{quote}\"", wraplength=600, 
                               font=("Arial", 12, "italic"), anchor="w").pack(fill="x", padx=10, pady=5)
    
    def update_suggestions_list_with_data(self):
        """Update the suggestions list with actual data and improved sampling"""
        if not self.simulation_results:
            self.suggestions_text.delete("1.0", "end")
            self.suggestions_text.insert("1.0", "# No Data\n\nNo simulation results available to generate suggestions.")
            return
            
        # Extract all suggestions from the results
        all_suggestions = []
        suggestion_sources = []  # Keep track of which result each suggestion came from
        
        for result in self.simulation_results:
            if "suggestions" in result and result["suggestions"]:
                for suggestion in result["suggestions"]:
                    all_suggestions.append(suggestion.strip())
                    suggestion_sources.append(result)
                
        # Count suggestion frequencies
        suggestion_counts = {}
        for suggestion in all_suggestions:
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
        
        # Match suggestions back to their original statements for context
        suggestion_statements = {}
        for i, suggestion in enumerate(all_suggestions):
            if suggestion not in suggestion_statements:
                suggestion_statements[suggestion] = []
            
            result = suggestion_sources[i]
            if "statement" in result:
                suggestion_statements[suggestion].append(result["statement"])
        
        # Identify top suggestion and generate key recommendation
        top_suggestion = max(suggestion_counts.items(), key=lambda x: x[1], default=("", 0))
        
        # Try to generate a better suggestions summary with the LLM if available
        if self.ollama.available:
            suggestion_text = self.ollama.generate_text(
                f"""You are an AI assistant summarizing improvement suggestions based on feedback about a proposal. 
                
The proposal is about: {self.proposal_title.get()}

Key suggestions ranked by frequency:
{json.dumps(sorted(suggestion_counts.items(), key=lambda x: x[1], reverse=True)[:10])}

Suggestion categories:
{json.dumps({k: [s[0] for s in v] for k, v in categories.items()})}

Create a well-organized summary of improvement suggestions with the following:
1. A brief introduction summarizing the overall feedback
2. Categorized recommendations, organized by theme
3. Specific actionable items highlighted within each category
4. Emphasize the most critical recommendations based on frequency

Format the summary with Markdown including appropriate headers.""",
                temperature=0.3
            )
            
            if suggestion_text:
                # Clean up the summary
                suggestion_text = re.sub(r'<.*?>', '', suggestion_text)  # Remove any XML tags
                
                # Ensure it has a title
                if not suggestion_text.startswith('#'):
                    suggestion_text = f"# Improvement Suggestions\n\n{suggestion_text}"
                    
                self.suggestions_text.delete("1.0", "end")
                self.suggestions_text.insert("1.0", suggestion_text)
                return
        
        # If LLM is not available or fails, use our manual approach
        # Generate a dynamic key recommendation based on the data
        key_recommendation = ""
        if top_suggestion[0]:
            # Calculate what percentage of responses included this suggestion
            suggestion_percentage = round((top_suggestion[1] / len(self.simulation_results)) * 100)
            
            # Get associated statement(s) for context
            if top_suggestion[0] in suggestion_statements:
                # Select a diverse set of statements that support this suggestion
                context_statements = self.verbal_sampling_manager.select_diverse_statements(
                    suggestion_statements[top_suggestion[0]],
                    keyword=top_suggestion[0],
                    n=min(2, len(suggestion_statements[top_suggestion[0]]))
                )
                
                key_recommendation = f"The most frequent suggestion ({suggestion_percentage}% of responses) was: \"{top_suggestion[0]}\"\n\n"
                
                if context_statements:
                    key_recommendation += "Supporting feedback:\n"
                    for stmt in context_statements:
                        key_recommendation += f"- \"{stmt}\"\n"
            else:
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
                    
                    # Take top 3 per category
                    top_category_suggestions = suggestions[:min(3, len(suggestions))]
                    
                    for suggestion, count in top_category_suggestions:
                        percentage = round((count / len(self.simulation_results)) * 100)
                        
                        # Add the suggestion with percentage
                        suggestions_text += f"- **{suggestion}** ({percentage}% of respondents)\n"
                        
                        # Add supporting quotes if available
                        if suggestion in suggestion_statements and suggestion_statements[suggestion]:
                            # Get diverse supporting statements
                            supporting_statements = self.verbal_sampling_manager.select_diverse_statements(
                                suggestion_statements[suggestion],
                                keyword=suggestion,
                                n=1  # Just one supporting statement per suggestion to keep it readable
                            )
                            
                            if supporting_statements:
                                suggestions_text += f"  - *\"{supporting_statements[0]}\"*\n"
                    
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


def main():
    """Run the Habermas Machine with Chorus functionality"""
    try:
        # Initialize the main application
        root = ctk.CTk()
        root.protocol("WM_DELETE_WINDOW", lambda: (root.quit(), root.destroy()))
        
        # Create the Habermas Machine
        app = HabermasMachine(root)
        
        # Start the main loop
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
class HabermasMachine:
    """
    Unified Habermas Machine with Chorus functionality for
    AI-assisted consensus building and feedback analysis
    """
    
    def __init__(self, root):
        """Initialize the application"""
        self.root = root
        self.root.title("Habermas Machine with Chorus")
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
        
        # Chorus-specific state
        self.value_statements = []
        self.sample_statements_loaded = False
        self.filter_initialized = False
        self.simulation_results = []
        self.verbal_sampling_manager = VerbalSamplingManager()
        
        # Ollama integration
        self.ollama = OllamaIntegration()
        
        # Default prompt templates
        self.default_templates = {
            "candidate_generation": "Given the following question and participant statements, please combine these statements into a single group statement that synthesizes their viewpoints and includes all their individual points and concerns. This should represent a fair consensus or compromise position that most participants could accept. The group statement should include and be representative of all details, concerns, suggestions, or questions from all participants, even if that make the combined statement longer.\n\n"
                                  "---\n\nQuestion: {question}\n\n"
                                  "---\n\n{participant_statements}\n\n---\n\n",
            
            "ranking_prediction": "Given this participant's statement on a question, predict how this participant would rank different group statements from most preferred (1) to least preferred ({num_candidates}).\n\n\n\n"
                                "Question: {question}\n\n"
                                "Participant {participant_num}'s original statement: {participant_statement}\n\n"
                                "Group Statements to Rank:\n\n"
                                "{candidate_statements}\n\n\n\n"
                                """Based on the participant's original statement, predict their ranking of these group statements from most preferred to least preferred as a JSON object:\n\n{{\n  "ranking": [0, 0, ...]\n}}\n\nImportant: Your response MUST contain ONLY a valid JSON object with a list of integer rankings under the key "ranking", NOT a list of statements, and must align with how this participant would rank them; e.g. how aligned they are with this participant's stance and priorities.""",
                                
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
        
        # Create templates that will be edited
        self.prompt_templates = self.default_templates.copy()
        
        # Create main layout
        self.create_layout()
        
        # Configure default values
        self.model_var.set("deepseek-r1:14b")
        self.temperature_var.set("0.7")
        self.top_p_var.set("0.9")
        self.top_k_var.set("40")
        self.ranking_temperature_var.set("0.2")
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
    
    def create_layout(self):
        """Create the main application layout"""
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
        """Set up the left column with tabs for various inputs and settings"""
        # Configure the left column to expand
        self.left_column.grid_columnconfigure(0, weight=1)
        self.left_column.grid_rowconfigure(0, weight=1)
        
        # Create a tabview for the left column
        self.left_tabview = ctk.CTkTabview(self.left_column)
        self.left_tabview.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Add tabs for the left column
        self.left_tabview.add("Inputs")
        self.left_tabview.add("Settings")
        self.left_tabview.add("Templates")
        self.left_tabview.add("Chorus")
        
        # Make sure each tab can expand
        for tab_name in ["Inputs", "Settings", "Templates", "Chorus"]:
            self.left_tabview.tab(tab_name).grid_columnconfigure(0, weight=1)
            self.left_tabview.tab(tab_name).grid_rowconfigure(0, weight=1)
        
        # Setup the Inputs tab (question, participants)
        self.setup_inputs_tab()
        
        # Setup the Settings tab (model, parameters)
        self.setup_settings_tab()
        
        # Setup the Templates tab (prompt templates)
        self.setup_templates_tab()
        
        # Setup the Chorus tab
        self.setup_chorus_tab()
    
    def setup_inputs_tab(self):
        """Setup the Inputs tab with question and participant inputs"""
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
        """Setup the Settings tab with model parameters"""
        # Create a scrollable frame for settings
        settings_frame = ctk.CTkScrollableFrame(self.left_tabview.tab("Settings"))
        settings_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Model selection
        model_frame = ctk.CTkFrame(settings_frame)
        model_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(model_frame, text="Model:", anchor="w", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        self.model_var = ctk.StringVar()
        self.model_entry = ctk.CTkEntry(model_frame, textvariable=self.model_var, width=200, font=("Arial", 12))
        self.model_entry.pack(side="left", padx=10, fill="x", expand=True)
        
        # Generation parameters section
        gen_params_frame = ctk.CTkFrame(settings_frame)
        gen_params_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(gen_params_frame, text="Generation Parameters", font=("Arial", 14, "bold")).pack(pady=5)
        
        params_grid = ctk.CTkFrame(gen_params_frame)
        params_grid.pack(fill="x", padx=10, pady=5, expand=True)
        
        # Temperature
        ctk.CTkLabel(params_grid, text="Temperature:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.temperature_var = ctk.StringVar()
        self.temperature_entry = ctk.CTkEntry(params_grid, textvariable=self.temperature_var, width=60, font=("Arial", 12))
        self.temperature_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Top P
        ctk.CTkLabel(params_grid, text="Top P:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.top_p_var = ctk.StringVar()
        self.top_p_entry = ctk.CTkEntry(params_grid, textvariable=self.top_p_var, width=60, font=("Arial", 12))
        self.top_p_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # Top K
        ctk.CTkLabel(params_grid, text="Top K:", font=("Arial", 12)).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.top_k_var = ctk.StringVar()
        self.top_k_entry = ctk.CTkEntry(params_grid, textvariable=self.top_k_var, width=60, font=("Arial", 12))
        self.top_k_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # Number of candidate statements
        ctk.CTkLabel(params_grid, text="Candidate Statements:", font=("Arial", 12)).grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.num_candidates_var = ctk.StringVar()
        self.num_candidates_spinbox = ctk.CTkEntry(params_grid, textvariable=self.num_candidates_var, width=60, font=("Arial", 12))
        self.num_candidates_spinbox.grid(row=0, column=3, padx=10, pady=5, sticky="w")
        
        # Ranking prediction parameters section
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
        
        # Maximum retries for JSON parsing
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
        """Setup the Templates tab with editable prompt templates"""
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
        
        # Response simulation template
        ctk.CTkLabel(templates_frame, text="Response Simulation Template (Chorus):", anchor="w", font=("Arial", 12, "bold")).pack(fill="x", padx=10, pady=(10, 5))
        self.response_template_text = ctk.CTkTextbox(templates_frame, height=200, wrap="word", font=("Arial", 12))
        self.response_template_text.pack(fill="x", padx=10, pady=(0, 10))
        self.response_template_text.insert("1.0", self.prompt_templates["response_simulation"])
        
        ctk.CTkLabel(templates_frame, text="Available placeholders: {value_statement}, {department}, {role}, {location}, {proposal_title}, {proposal_description}", anchor="w").pack(fill="x", padx=10, pady=(0, 10))
        
        # Save template changes button
        save_btn = ctk.CTkButton(
            templates_frame,
            text="Save Template Changes",
            command=self.save_templates,
            font=("Arial", 12)
        )
        save_btn.pack(padx=10, pady=10)
    
    def setup_chorus_tab(self):
        """Setup the Chorus tab for value repository and proposal feedback"""
        chorus_tab = self.left_tabview.tab("Chorus")
        
        # Configure the tab
        chorus_tab.grid_columnconfigure(0, weight=1)
        chorus_tab.grid_rowconfigure(0, weight=0)  # Repository section - fixed height
        chorus_tab.grid_rowconfigure(1, weight=0)  # Proposal section - fixed height
        chorus_tab.grid_rowconfigure(2, weight=1)  # Results section - expandable
        
        # Create the value repository section
        self.setup_value_repository_section(chorus_tab)
        
        # Create the proposal submission section
        self.setup_proposal_section(chorus_tab)
    
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
    
    def setup_middle_column(self):
        """Set up the middle column (results) with tabview for different outputs"""
        # For the middle column (results), we'll use a tabview to separate different views
        self.results_tabview = ctk.CTkTabview(self.middle_column)
        self.results_tabview.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add tabs for different types of output
        self.results_tabview.add("Friendly Output")
        self.results_tabview.add("Detailed Records")
        
        # Add tabs for Chorus
        self.results_tabview.add("Chorus Summary")
        self.results_tabview.add("Sentiment Analysis")
        self.results_tabview.add("Key Concerns")
        self.results_tabview.add("Suggestions")
        
        # Setup the Friendly Output tab
        self.setup_friendly_output_tab()
        
        # Setup the Detailed Records tab
        self.setup_detailed_records_tab()
        
        # Setup the Chorus tabs
        self.setup_chorus_results_tabs()
    
    def setup_friendly_output_tab(self):
        """Setup the Friendly Output tab for consensus results"""
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
        """Setup the Detailed Records tab for detailed consensus process logs"""
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
    
    def setup_chorus_results_tabs(self):
        """Setup the Chorus results tabs"""
        # Setup summary tab
        summary_tab = self.results_tabview.tab("Chorus Summary")
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
    
    def setup_right_column(self):
        """Setup the right column with debug information displays"""
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
    
    #
    # Habermas Machine Core Methods
    #
    
    def update_participant_count(self, event=None):
        """Update the participant count label based on the number of non-empty lines"""
        text = self.participants_text.get("1.0", "end-1c")
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        self.participant_count_label.configure(text=f"Count: {len(lines)}")
    
    def save_templates(self):
        """Save the prompt templates from the UI to application memory"""
        # Get the current template text
        candidate_template = self.candidate_template_text.get("1.0", "end-1c")
        ranking_template = self.ranking_template_text.get("1.0", "end-1c")
        response_template = self.response_template_text.get("1.0", "end-1c")
        
        # Update the templates
        self.prompt_templates["candidate_generation"] = candidate_template
        self.prompt_templates["ranking_prediction"] = ranking_template
        self.prompt_templates["response_simulation"] = response_template
        
        # Update Ollama model if changed
        model = self.model_var.get()
        if model and self.ollama.model != model:
            self.ollama.model = model
        
        messagebox.showinfo("Templates Saved", "Prompt templates have been updated.")
    
    def reset_template(self, template_key):
        """Reset a specific template to default"""
        if template_key in self.default_templates:
            self.prompt_templates[template_key] = self.default_templates[template_key]
            
            if template_key == "candidate_generation":
                self.candidate_template_text.delete("1.0", "end")
                self.candidate_template_text.insert("1.0", self.default_templates[template_key])
            elif template_key == "ranking_prediction":
                self.ranking_template_text.delete("1.0", "end")
                self.ranking_template_text.insert("1.0", self.default_templates[template_key])
            elif template_key == "response_simulation":
                self.response_template_text.delete("1.0", "end")
                self.response_template_text.insert("1.0", self.default_templates[template_key])
            
            messagebox.showinfo("Template Reset", f"The {template_key} template has been reset to default.")
    
    def reset_all_templates(self):
        """Reset all templates to default"""
        self.prompt_templates = self.default_templates.copy()
        
        self.candidate_template_text.delete("1.0", "end")
        self.candidate_template_text.insert("1.0", self.default_templates["candidate_generation"])
        
        self.ranking_template_text.delete("1.0", "end")
        self.ranking_template_text.insert("1.0", self.default_templates["ranking_prediction"])
        
        self.response_template_text.delete("1.0", "end")
        self.response_template_text.insert("1.0", self.default_templates["response_simulation"])
        
        messagebox.showinfo("Templates Reset", "All prompt templates have been reset to default.")
    
    def bulk_import(self):
        """Import question and participant statements from a text file"""
        file_path = tk.filedialog.askopenfilename(
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
    
    def get_participant_statements(self):
        """Extract participant statements from the textbox"""
        text = self.participants_text.get("1.0", "end-1c")
        statements = [line.strip() for line in text.split('\n') if line.strip()]
        return statements
    
    def save_output(self, output_type):
        """Save the output to a file"""
        # Default file types and initial filename
        if output_type == "friendly":
            filetypes = [("Text files", "*.txt"), ("Markdown files", "*.md"), ("All files", "*.*")]
            initial_filename = f"habermas_results_{self.session_id}.md"
            content = self.friendly_output.get("1.0", "end-1c")
        elif output_type == "detailed":
            filetypes = [("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
            initial_filename = f"habermas_detailed_{self.session_id}.md"
            content = self.detailed_output.get("1.0", "end-1c")
        elif output_type == "chorus_summary":
            filetypes = [("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
            initial_filename = f"habermas_chorus_{self.session_id}.md"
            content = self.summary_text.get("1.0", "end-1c")
        elif output_type == "chorus_suggestions":
            filetypes = [("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
            initial_filename = f"habermas_suggestions_{self.session_id}.md"
            content = self.suggestions_text.get("1.0", "end-1c")
        else:
            return
        
        # Ask user where to save
        file_path = tk.filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=filetypes,
            initialfile=initial_filename
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
            self.log_to_detailed(f"**Model:** {self.model_var.get()}  \n")
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
                self.log_to_friendly("**Error:** Failed to generate candidate statements.\n\n")
                self.log_to_detailed("**Error:** Failed to generate candidate statements.\n\n")
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
                    # Save friendly output
                    friendly_path = f"habermas_results_{self.session_id}.md"
                    with open(friendly_path, 'w', encoding='utf-8') as file:
                        file.write(self.friendly_output.get("1.0", "end-1c"))
                    
                    # Save detailed output
                    detailed_path = f"habermas_detailed_{self.session_id}.md"
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
                error_msg = f"API Error: Status code {self.current_response.status_code}"
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
                    except json.JSONDecodeError:
                        self.log_to_detailed("**Error:** Failed to decode response from Ollama API\n\n")
                
            # Log the response
            self.log_to_detailed(f"**Raw Response for Candidate {candidate_num}:**\n\n```\n{full_response}\n```\n\n")
            
            # Remove the <think>...</think> tag that DeepSeek-R1 may add
            clean_response = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL).strip()
            
            return clean_response
            
        except Exception as e:
            error_msg = f"Error generating candidate {candidate_num}: {str(e)}"
            self.log_to_detailed(f"**Error:** {error_msg}\n\n")
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
                self.log_to_detailed(f"**Exception:** {str(e)}\n\n")
            finally:
                self.current_response = None
        
        # If we get here, all attempts failed
        attempts_log.append("All attempts failed. Falling back to random ranking.")
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
