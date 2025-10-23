"""
LLM-powered summarization utilities for Habermas Chorus results.

Generates natural language summaries that prioritize participant wording
while making content accessible for stakeholders and leadership.
"""

import requests
import json
import re
import traceback
from collections import defaultdict


class HabermasLLMSummarizer:
    """
    LLM-powered summarizer that respects Habermas Machine principles.

    Generates summaries that:
    1. Prioritize direct quotations from participants
    2. Present balanced views representing all perspectives
    3. Focus on finding common ground and shared concerns
    4. Avoid imposing external judgments
    5. Make content accessible for various audiences
    """

    def __init__(self, ollama_base_url="http://localhost:11434", model="deepseek-r1:14b"):
        """
        Initialize the summarizer.

        Args:
            ollama_base_url: Ollama API base URL
            model: LLM model name to use for summarization
        """
        self.base_url = ollama_base_url
        self.model = model
        self.available = self._check_availability()

    def _check_availability(self):
        """Check if Ollama is available and has the specified model."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code != 200:
                return False

            # Check if specified model is available
            models = response.json().get("models", [])
            model_names = [m.get("name") for m in models]

            return self.model in model_names
        except:
            return False

    def generate_summary(self, results, proposal_title, proposal_text,
                        representative_statements=None, top_concerns=None,
                        department_insights=None):
        """
        Generate an LLM-powered summary that respects participant wording.

        Args:
            results: List of simulation results
            proposal_title: Title of the proposal
            proposal_text: Text of the proposal
            representative_statements: List of representative statements (optional)
            top_concerns: List of top concerns with counts (optional)
            department_insights: List of department insights (optional)

        Returns:
            Generated summary text (Markdown formatted)
        """
        if not self.available or not results:
            return self._generate_fallback_summary(
                results, proposal_title, top_concerns, representative_statements
            )

        try:
            # Calculate statistics
            total = len(results)
            favorable = sum(1 for r in results if r.get("sentiment") == "favorable")
            neutral = sum(1 for r in results if r.get("sentiment") == "neutral")
            unfavorable = sum(1 for r in results if r.get("sentiment") == "unfavorable")

            favorable_pct = round((favorable / total) * 100) if total > 0 else 0
            neutral_pct = round((neutral / total) * 100) if total > 0 else 0
            unfavorable_pct = round((unfavorable / total) * 100) if total > 0 else 0

            # Prepare prompt for LLM
            prompt = self._prepare_summary_prompt(
                results,
                proposal_title,
                proposal_text,
                representative_statements,
                top_concerns,
                department_insights,
                favorable_pct,
                neutral_pct,
                unfavorable_pct
            )

            # Make API call to Ollama
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # Low temperature for consistency
                        "top_p": 0.9,
                        "top_k": 40
                    }
                },
                timeout=20  # Longer timeout for summary generation
            )

            if response.status_code != 200:
                return self._generate_fallback_summary(
                    results, proposal_title, top_concerns, representative_statements
                )

            summary_text = response.json().get("response", "").strip()

            # Clean response if needed (remove any system prompt residue)
            summary_text = re.sub(r'<.*?>', '', summary_text)

            # Ensure the summary has a title
            if not summary_text.startswith('#'):
                summary_text = f"# Feedback Summary for: {proposal_title}\n\n{summary_text}"

            return summary_text

        except Exception as e:
            print(f"Error generating LLM summary: {str(e)}")
            print(traceback.format_exc())
            return self._generate_fallback_summary(
                results, proposal_title, top_concerns, representative_statements
            )

    def _prepare_summary_prompt(self, results, proposal_title, proposal_text,
                                representative_statements, top_concerns,
                                department_insights, favorable_pct, neutral_pct,
                                unfavorable_pct):
        """Prepare a prompt for the LLM summarizer."""
        prompt = f"""You are an AI assistant helping to analyze and summarize feedback about a proposal. Your task is to create a concise, balanced, and informative summary that emphasizes participant wording while making the content more readable.

The summary should follow these principles:
1. Prioritize using direct quotations from participants when possible
2. Present a balanced view that represents all perspectives
3. Focus on finding common ground and shared concerns
4. Identify key themes without imposing your own judgments
5. Make content accessible and clearly organized for various audiences

Here's the information about the proposal:

Title: {proposal_title}
Description: {proposal_text}

Feedback statistics:
- Total responses: {len(results)}
- Favorable: {favorable_pct}%
- Neutral: {neutral_pct}%
- Unfavorable: {unfavorable_pct}%

"""

        # Add top concerns if available
        if top_concerns:
            prompt += "Top concerns identified:\n"
            for concern, count in top_concerns:
                concern_pct = round((count / len(results)) * 100)
                prompt += f"- {concern}: {concern_pct}% of responses\n"
            prompt += "\n"

        # Add department insights if available
        if department_insights and department_insights:
            prompt += "Department-specific insights:\n"
            for insight in department_insights:
                prompt += f"- {insight}\n"
            prompt += "\n"

        # Add representative statements if available
        if representative_statements and representative_statements:
            prompt += "Representative statements from participants:\n"
            for stmt in representative_statements:
                prompt += f'"{stmt}"\n'
            prompt += "\n"

        # Sample of all statements for context
        sample_size = min(5, len(results))
        sample_statements = [r.get("statement", "") for r in results if "statement" in r][:sample_size]

        if sample_statements:
            prompt += "Sample of all feedback statements for context:\n"
            for stmt in sample_statements:
                prompt += f'"{stmt}"\n'
            prompt += "\n"

        # Instructions for output format
        prompt += """
Please create a comprehensive summary with the following sections:
1. Top level summary of overall reception (positive, negative, or mixed) with most important points
2. Quick statistics on the feedback breakdown
3. Key themes and concerns identified
4. Important insights from the data
5. Representative quotes that illustrate the key points (use actual quotes from participants)

Format the summary with Markdown, including appropriate headers. Remember to be balanced and focus on finding consensus while accurately representing diverse perspectives.
"""

        return prompt

    def _generate_fallback_summary(self, results, proposal_title,
                                  top_concerns=None, representative_statements=None):
        """Generate a fallback summary when LLM is not available."""
        if not results:
            return f"# No Feedback Available for: {proposal_title}\n\nNo simulation results were available to generate a summary."

        # Calculate statistics
        total = len(results)
        favorable = sum(1 for r in results if r.get("sentiment") == "favorable")
        neutral = sum(1 for r in results if r.get("sentiment") == "neutral")
        unfavorable = sum(1 for r in results if r.get("sentiment") == "unfavorable")

        favorable_pct = round((favorable / total) * 100) if total > 0 else 0
        neutral_pct = round((neutral / total) * 100) if total > 0 else 0
        unfavorable_pct = round((unfavorable / total) * 100) if total > 0 else 0

        # Determine overall sentiment
        sentiment_description = (
            "positive" if favorable_pct > unfavorable_pct + 10
            else "mixed" if abs(favorable_pct - unfavorable_pct) <= 10
            else "negative"
        )
        concern_note = (
            " with some significant concerns."
            if unfavorable_pct > 20 or neutral_pct > 30
            else "."
        )

        # Create basic summary
        summary_text = f"# Feedback Summary for: {proposal_title}\n\n"
        summary_text += f"Based on simulated responses from {total} associates, the proposal received **{sentiment_description} reception**{concern_note}\n\n"

        # Add quick statistics
        summary_text += "## Quick Statistics:\n"
        summary_text += f"- 🟢 Favorable: {favorable_pct}%\n"
        summary_text += f"- 🟡 Neutral: {neutral_pct}%\n"
        summary_text += f"- 🔴 Unfavorable: {unfavorable_pct}%\n\n"

        # Add top concerns if available
        if top_concerns:
            summary_text += "## Top Themes:\n"
            for i, (concern, count) in enumerate(top_concerns, 1):
                concern_pct = round((count / total) * 100)
                summary_text += f"{i}. {concern} ({concern_pct}%)\n"
            summary_text += "\n"

        # Add representative statements if available
        if representative_statements:
            summary_text += "## Sample Feedback:\n"
            for stmt in representative_statements:
                summary_text += f'"{stmt}"\n\n'

        return summary_text

    def generate_suggestions_summary(self, results, suggestion_counts,
                                    suggestion_statements, categories):
        """
        Generate an enhanced summary of suggestions with the LLM.

        Args:
            results: List of simulation results
            suggestion_counts: Dictionary of suggestion → count
            suggestion_statements: Dictionary of suggestion → list of statements
            categories: Dictionary of category → list of (suggestion, count) tuples

        Returns:
            Generated suggestions summary (Markdown formatted)
        """
        if not self.available or not results or not suggestion_counts:
            return self._generate_fallback_suggestions(
                suggestion_counts, suggestion_statements, categories
            )

        try:
            # Prepare prompt for LLM
            prompt = self._prepare_suggestions_prompt(
                results, suggestion_counts, suggestion_statements, categories
            )

            # Make API call to Ollama
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # Low temperature for consistency
                        "top_p": 0.9,
                        "top_k": 40
                    }
                },
                timeout=20  # Longer timeout for summary generation
            )

            if response.status_code != 200:
                return self._generate_fallback_suggestions(
                    suggestion_counts, suggestion_statements, categories
                )

            suggestions_text = response.json().get("response", "").strip()

            # Clean response if needed
            suggestions_text = re.sub(r'<.*?>', '', suggestions_text)

            # Ensure the summary has a title
            if not suggestions_text.startswith('#'):
                suggestions_text = f"# Improvement Suggestions\n\n{suggestions_text}"

            return suggestions_text

        except Exception as e:
            print(f"Error generating LLM suggestions summary: {str(e)}")
            print(traceback.format_exc())
            return self._generate_fallback_suggestions(
                suggestion_counts, suggestion_statements, categories
            )

    def _prepare_suggestions_prompt(self, results, suggestion_counts,
                                   suggestion_statements, categories):
        """Prepare a prompt for suggestions summarization."""
        prompt = """You are an AI assistant helping to summarize improvement suggestions based on feedback about a proposal. Your task is to organize the suggestions into a cohesive, actionable format that emphasizes participant wording.

Follow these principles:
1. Prioritize using direct language from the original suggestions
2. Group related suggestions into meaningful categories
3. Present concrete, actionable recommendations
4. Use supporting quotes from participants to add context and credibility
5. Make the content organized and accessible for leadership decision-making

Here's the feedback information:
"""

        # Add suggestion counts
        prompt += f"Total responses: {len(results)}\n"
        prompt += f"Number of distinct suggestions: {len(suggestion_counts)}\n\n"

        # Add categorized suggestions
        prompt += "Suggestions by category:\n"
        for category, suggestions in categories.items():
            if suggestions:
                prompt += f"\n{category}:\n"
                for suggestion, count in suggestions:
                    percentage = round((count / len(results)) * 100)
                    prompt += f"- {suggestion} ({percentage}% of respondents)\n"

                    # Add supporting statements if available
                    if suggestion in suggestion_statements and suggestion_statements[suggestion]:
                        # Get a sample of statements (up to 2)
                        sample_statements = suggestion_statements[suggestion][:min(2, len(suggestion_statements[suggestion]))]
                        for stmt in sample_statements:
                            prompt += f'  - "{stmt}"\n'

        # Instructions for output format
        prompt += """
Please create a well-organized summary of improvement suggestions with the following sections:
1. Brief introduction summarizing the overall feedback on improvement areas
2. Categorized recommendations, organized by theme
3. Specific actionable items highlighted within each category
4. Supporting quotes from participants to illustrate key suggestions
5. A section highlighting the most critical recommendations based on frequency and importance

Format the summary with Markdown including appropriate headers, and emphasize the most critical recommendations. Make the suggestions concrete and actionable.
"""

        return prompt

    def _generate_fallback_suggestions(self, suggestion_counts,
                                     suggestion_statements, categories):
        """Generate a fallback suggestions summary when LLM is not available."""
        if not suggestion_counts:
            return "# No Suggestions\n\nNo specific suggestions were provided in the feedback."

        # Find top suggestion
        top_suggestion = max(
            suggestion_counts.items(), key=lambda x: x[1], default=("", 0)
        )

        # Create basic summary
        suggestions_text = "# Improvement Suggestions\n\n"
        suggestions_text += "Based on the simulated feedback, here are key suggestions to improve reception:\n\n"

        # Add categorized suggestions
        section_count = 1
        for category, suggestions in categories.items():
            if suggestions:
                suggestions = sorted(suggestions, key=lambda x: x[1], reverse=True)
                suggestions_text += f"## {section_count}. {category} Recommendations\n"

                # Take top 3 per category
                top_category_suggestions = suggestions[:min(3, len(suggestions))]

                for suggestion, count in top_category_suggestions:
                    # Add the suggestion with a supporting quote if available
                    suggestions_text += f"- **{suggestion}**\n"

                    if suggestion in suggestion_statements and suggestion_statements[suggestion]:
                        stmt = suggestion_statements[suggestion][0]
                        suggestions_text += f'  - *"{stmt}"*\n'

                suggestions_text += "\n"
                section_count += 1

        # Add key recommendation if available
        if top_suggestion[0]:
            suggestions_text += "## Key Recommendation\n"
            suggestions_text += f'The most frequent suggestion was: "{top_suggestion[0]}"\n'

            # Add supporting quote if available
            if top_suggestion[0] in suggestion_statements and suggestion_statements[top_suggestion[0]]:
                stmt = suggestion_statements[top_suggestion[0]][0]
                suggestions_text += f'\nSupporting feedback: "{stmt}"\n'

        return suggestions_text
