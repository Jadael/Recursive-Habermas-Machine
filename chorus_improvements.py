import tkinter as tk
import customtkinter as ctk
import numpy as np
import re
from threading import Thread
import random
import json
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from sklearn.metrics.pairwise import cosine_similarity
from itertools import combinations
import traceback

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
            
            relevance_scores = []
            for i, text_emb in enumerate(text_embs):
                relevance = cosine_similarity([keyword_emb], [text_emb])[0][0]
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


def enhance_habermas_chorus_extension(HabermasChorusExtension):
    """
    Enhance the HabermasChorusExtension class with improved verbatim sampling and results
    """
    # Add verbal sampling manager to the class
    original_init = HabermasChorusExtension.__init__
    
    def enhanced_init(self, habermas_machine):
        original_init(self, habermas_machine)
        self.verbal_sampling_manager = VerbalSamplingManager()
        
    HabermasChorusExtension.__init__ = enhanced_init
    
    # Update concerns chart with improved sampling
    original_update_concerns = HabermasChorusExtension.update_concerns_chart_with_data
    
    def enhanced_update_concerns_chart_with_data(self):
        """Update the key concerns chart with actual data and improved sampling"""
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
        
        # Reset the sampling manager to ensure fresh sampling
        self.verbal_sampling_manager.reset()
            
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
                # Select 3 diverse statements relevant to this concern
                diverse_quotes = self.verbal_sampling_manager.select_diverse_statements(
                    statements, concern, n=min(3, len(statements))
                )
                
                # Add each quote in its own frame
                for quote in diverse_quotes:
                    quote_frame = ctk.CTkFrame(concern_frame)
                    quote_frame.pack(fill="x", padx=10, pady=(0, 5))
                    
                    ctk.CTkLabel(quote_frame, text=f"\"{quote}\"", wraplength=600, 
                               font=("Arial", 12, "italic"), anchor="w").pack(fill="x", padx=10, pady=5)
    
    HabermasChorusExtension.update_concerns_chart_with_data = enhanced_update_concerns_chart_with_data
    
    # Update suggestions list with improved sampling
    original_update_suggestions = HabermasChorusExtension.update_suggestions_list_with_data
    
    def enhanced_update_suggestions_list_with_data(self):
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
        
        # Reset the sampler for fresh sampling
        self.verbal_sampling_manager.reset()
        
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
    
    HabermasChorusExtension.update_suggestions_list_with_data = enhanced_update_suggestions_list_with_data
    
    # Add LLM-powered summarization of results
    original_update_chorus_results = HabermasChorusExtension.update_chorus_results
    
    def enhanced_update_chorus_results(self, proposal_title, proposal_text):
        """Update the chorus results with simulation data and LLM-powered summarization"""
        # First, call the original method to update all the visualizations
        original_update_chorus_results(self, proposal_title, proposal_text)
        
        # Now, enhance the summary with LLM-powered insights while respecting participants' wording
        if not self.simulation_results:
            return
        
        # Prepare key statistics for the summary
        total = len(self.simulation_results)
        favorable = sum(1 for r in self.simulation_results if r.get("sentiment") == "favorable")
        neutral = sum(1 for r in self.simulation_results if r.get("sentiment") == "neutral")
        unfavorable = sum(1 for r in self.simulation_results if r.get("sentiment") == "unfavorable")
        
        favorable_pct = round((favorable / total) * 100) if total > 0 else 0
        neutral_pct = round((neutral / total) * 100) if total > 0 else 0
        unfavorable_pct = round((unfavorable / total) * 100) if total > 0 else 0
        
        # Extract actual statements for sentiment categories
        favorable_statements = [r.get("statement", "") for r in self.simulation_results if r.get("sentiment") == "favorable"]
        neutral_statements = [r.get("statement", "") for r in self.simulation_results if r.get("sentiment") == "neutral"]
        unfavorable_statements = [r.get("statement", "") for r in self.simulation_results if r.get("sentiment") == "unfavorable"]
        
        # Reset the sampling manager for fresh sampling
        self.verbal_sampling_manager.reset()
        
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
        
        # Calculate department statistics
        dept_counts = {}
        for result in self.simulation_results:
            dept = result.get("department", "Unknown")
            sentiment = result.get("sentiment", "neutral")
            
            if dept not in dept_counts:
                dept_counts[dept] = {"favorable": 0, "neutral": 0, "unfavorable": 0, "total": 0}
                
            dept_counts[dept][sentiment] += 1
            dept_counts[dept]["total"] += 1
        
        # Find departments with notable sentiment divergence
        dept_insights = []
        for dept, counts in dept_counts.items():
            if counts["total"] > 0:
                dept_favorable_pct = round((counts["favorable"] / counts["total"]) * 100)
                dept_unfavorable_pct = round((counts["unfavorable"] / counts["total"]) * 100)
                
                # If department sentiment differs significantly from overall
                if abs(dept_favorable_pct - favorable_pct) > 20 or abs(dept_unfavorable_pct - unfavorable_pct) > 20:
                    if dept_favorable_pct > favorable_pct + 20:
                        dept_insights.append(f"{dept} department responded notably more favorably ({dept_favorable_pct}% favorable)")
                    elif dept_unfavorable_pct > unfavorable_pct + 20:
                        dept_insights.append(f"{dept} department responded notably more unfavorably ({dept_unfavorable_pct}% unfavorable)")
        
        # Count all concerns from the results
        all_concerns = []
        for result in self.simulation_results:
            if "concerns" in result and result["concerns"]:
                all_concerns.extend(result["concerns"])
                
        # Count frequencies of concerns
        concern_counts = {}
        for concern in all_concerns:
            concern = concern.strip()
            if concern in concern_counts:
                concern_counts[concern] += 1
            else:
                concern_counts[concern] = 1
        
        # Get top concerns
        top_concerns = sorted(concern_counts.items(), key=lambda x: x[1], reverse=True)[:4]
        
        # Generate the LLM-powered summary
        # For now, we'll create a structured summary that respects original wording
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
        
        # Add key insights if available
        if dept_insights or top_concerns:
            summary_text += "\n## Key Insights:\n"
            
            # Add department-based insights
            for insight in dept_insights:
                summary_text += f"- {insight}\n"
            
            # Add top concern insight if available
            if top_concerns:
                summary_text += f"- The most significant concern was '{top_concerns[0][0]}', mentioned by {top_concerns[0][1]} associates.\n"
        
        # Add representative verbatim quotes
        if representative_statements:
            summary_text += "\n## Sample Feedback:\n"
            for stmt in representative_statements:
                summary_text += f"\"{stmt}\"\n\n"
        
        # Update the summary text
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", summary_text)
        
        # Switch to Summary tab to show results
        self.results_tabview.set("Summary")
    
    HabermasChorusExtension.update_chorus_results = enhanced_update_chorus_results
    
    return HabermasChorusExtension

# Function to apply the enhancement to an existing HabermasChorusExtension class
def enhance_existing_chorus_extension(extension_instance):
    """Apply enhancements to an existing HabermasChorusExtension instance"""
    extension_instance.verbal_sampling_manager = VerbalSamplingManager()
    
    # Replace the methods with enhanced versions
    extension_instance.update_concerns_chart_with_data = MethodType(
        enhance_habermas_chorus_extension(type(extension_instance)).update_concerns_chart_with_data,
        extension_instance
    )
    
    extension_instance.update_suggestions_list_with_data = MethodType(
        enhance_habermas_chorus_extension(type(extension_instance)).update_suggestions_list_with_data,
        extension_instance
    )
    
    extension_instance.update_chorus_results = MethodType(
        enhance_habermas_chorus_extension(type(extension_instance)).update_chorus_results,
        extension_instance
    )
    
    return extension_instance
