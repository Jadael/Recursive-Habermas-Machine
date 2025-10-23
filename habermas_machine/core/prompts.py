"""
Prompt templates for Habermas Machine and Chorus.

This module consolidates all prompt templates, including:
1. DeepMind's production-tested Chain-of-Thought (CoT) prompts
2. Original recursive consensus prompts
3. Chorus stakeholder feedback prompts
4. Arrow notation ranking prompts

Copyright 2025 - Incorporates templates from Google DeepMind's Habermas Machine
Licensed under Apache License 2.0
"""

from typing import Sequence


# ============================================================================
# DEEPMIND CHAIN-OF-THOUGHT CONSENSUS GENERATION PROMPTS
# ============================================================================

def generate_opinion_only_cot_prompt(
    question: str,
    opinions: Sequence[str],
) -> str:
    """
    DeepMind's production-tested prompt for initial consensus generation.

    Uses structured <answer><sep></answer> format with step-by-step reasoning.
    Explicitly requires non-conflict with individual opinions.

    Args:
        question: The deliberation question
        opinions: List of participant opinion statements

    Returns:
        Formatted prompt string
    """
    prompt = f"""You are assisting a citizens' jury in forming an initial consensus opinion on an important question. The jury members have provided their individual opinions. Your role is to generate a draft consensus statement that captures the main points of agreement and represents the collective view of the jury.  The draft statement must not conflict with any of the individual opinions.

Please think through this task step-by-step:

1. Carefully analyze the individual opinions, noting key themes, points of agreement, and areas of disagreement.
2. Based on the analysis, synthesize a concise and clear consensus statement that represents the shared perspective of the jury members.  Address the core issue posed in the question, and ensure the statement *does not conflict* with any of the individual opinions.  Refer to specific opinion numbers to demonstrate how the draft reflects the collective view.

Provide your answer in the following format:
<answer>
[Your step-by-step reasoning and explanation for the statement]
<sep>
[Draft consensus statement]
</answer>

Example:
<answer>
1. Most opinions emphasize the importance of public transportation (Opinions 1, 3, 4) and reducing car dependency (Opinions 2, 4). Some also mention cycling and walking as important additions (Opinions 2, 3).
2. The draft statement prioritizes investment in public transport and encourages cycling and walking, reflecting the shared views expressed in the majority of opinions.
<sep>
We believe that investing in public transport, along with promoting cycling and walking, are crucial steps towards creating a more sustainable and livable city.
</answer>


Below you will find the question and the individual opinions of the jury members.

Question: {question}

Individual Opinions:
"""

    for i, opinion in enumerate(opinions):
        prompt += f'Opinion Person {i+1}: {opinion}\n'

    return prompt.strip()


def generate_opinion_critique_cot_prompt(
    question: str,
    opinions: Sequence[str],
    previous_winner: str,
    critiques: Sequence[str],
) -> str:
    """
    DeepMind's production-tested prompt for revised consensus generation.

    Incorporates previous draft and critiques for iterative refinement.
    Requires explicit reference to opinion and critique numbers.

    Args:
        question: The deliberation question
        opinions: List of participant opinion statements
        previous_winner: The consensus statement from the previous round
        critiques: List of participant critiques of the previous winner

    Returns:
        Formatted prompt string
    """
    prompt = f"""You are assisting a citizens' jury in forming a consensus opinion on an important question. The jury members have provided their individual opinions, a first draft of a consensus statement was created, and critiques of that draft were gathered. Your role is to generate a revised consensus statement that incorporates the feedback and aims to better represent the collective view of the jury.  Ensure the revised statement does not conflict with the individual opinions.

Please think through this task step-by-step:

1. Carefully analyze the individual opinions, noting key themes, points of agreement, and areas of disagreement.
2. Review the previous draft consensus statement and identify its strengths and weaknesses.
3. Analyze the critiques of the previous draft, paying attention to specific suggestions and concerns raised by the jury members.
4. Based on the opinions, the previous draft, and the critiques, synthesize a revised consensus statement that addresses the concerns raised and better reflects the collective view of the jury. Ensure the statement is clear, concise, addresses the core issue posed in the question, and *does not conflict* with any of the individual opinions.  Refer to specific opinion and critique numbers when making your revisions.

Provide your answer in the following format:
<answer>
[Your step-by-step reasoning and explanation for the revised statement]
<sep>
[Revised consensus statement]
</answer>

Example:
<answer>
1. Opinions generally agree on the need for more green spaces (Opinions 1, 2, 3), but disagree on the specific location (Opinions 2 and 3 prefer the riverfront) and funding (Opinion 1 suggests a tax levy, Opinion 3 suggests private donations).
2. The previous draft suggested converting the old factory site into a park, but didn't address funding, which was a key concern in Critique 1.
3. Critiques highlighted the lack of funding details (Critique 1) and some preferred a different location (Critique 2 suggested the riverfront, echoing Opinion 2).
4. The revised statement proposes converting the old factory site into a park, funded by a combination of city funds and private donations (addressing Opinion 3 and Critique 1), and includes a plan for community input on park design and amenities. The factory site is chosen as a compromise location, as it avoids the higher costs associated with the riverfront development suggested in Opinion 2 and Critique 2.
<sep>
We propose converting the old factory site into a park, funded by a combination of city funds and private donations. We will actively seek community input on the park's design and amenities to ensure it meets the needs of our residents.
</answer>


Below you will find the question, the individual opinions, the previous draft consensus statement, and the critiques provided by the jury members.


Question: {question}

Individual Opinions:
"""
    for i, opinion in enumerate(opinions):
        prompt += f'Opinion Person {i+1}: {opinion}\n'

    prompt += f"""
Previous Draft Consensus Statement: {previous_winner}

Critiques of the Previous Draft:
"""

    for i, critique in enumerate(critiques):
        prompt += f'Critique Person {i+1}: {critique}\n'

    return prompt.strip()


# ============================================================================
# DEEPMIND ARROW NOTATION RANKING PROMPTS
# ============================================================================

def generate_opinion_only_ranking_prompt(
    question: str,
    opinion: str,
    statements: Sequence[str],
) -> str:
    """
    DeepMind's prompt for ranking candidate statements using arrow notation.

    Produces rankings in format: A > B > C > D (no ties in final answer)
    More robust than JSON formatting, with extensive validation.

    Args:
        question: The deliberation question
        opinion: Single participant's opinion
        statements: List of candidate consensus statements to rank

    Returns:
        Formatted prompt string
    """
    prompt = f"""
Task: As an AI assistant, your job is to rank these statements in the order that the participant would most likely agree with them, based on their opinion. Use Arrow notation for the ranking, where ">" means "preferred to". Ties are NOT allowed and items should be in descending order of preference so you can ONLY use ">" and the letters of the statements in the final ranking. Examples of valid final rankings: B > A, D > A > C > B, B > C > A > E > D.

Please think through this task step-by-step:

1. Analyze the participant's opinion, noting key points and sentiments.
2. Compare each statement to the participant's opinion, considering how well it aligns with or supports their view.
3. Consider any nuances or implications in the statements that might appeal to or repel the participant based on their expressed opinion.
4. Rank the statements accordingly using only ">" and the letters of the statements.

Provide your answer in the following format:
<answer>
[Your step-by-step reasoning and explanation for the ranking]
<sep>
[Final ranking using arrow notation]
</answer>

For example for five statements A, B, C, D and E a valid response could be:
<answer>
1. The participant's opinion emphasizes the importance of environmental protection and the need for immediate action to address climate change.

2. - Statement A directly addresses the urgency of climate action and proposes concrete steps, aligning with the participant's opinion.
   - Statements B and D acknowledge the seriousness of climate change but offer less concrete solutions. B focuses on global cooperation, while D emphasizes economic considerations.
   - Statement C downplays the urgency of climate change, contradicting the participant's stance.
   - Statement E completely opposes the participant's view by denying the existence of climate change.

3.  The participant's emphasis on immediate action suggests a preference for proactive solutions and a dislike for approaches that downplay the issue or offer only abstract ideas.

4. Based on this analysis, the ranking is: A > D > B > C > E

<sep>
A > D > B > C > E
</answer>

It is important to follow the template EXACTLY. So ALWAYS start with <answer>, then the explanation, then <sep> then only the final ranking and then </answer>.


Below you will find the question and the participant's opinion. You will also find a list of statements to rank.

Question: {question}

Participant's Opinion: {opinion}

Statements to rank:
"""
    for i, statement in enumerate(statements):
        letter = chr(ord('A') + i)  # A, B, C, D, etc.
        statement = statement.strip().strip('"').strip('\n').strip()
        prompt += f'{letter}. {statement}\n'

    return prompt.strip()


def generate_opinion_critique_ranking_prompt(
    question: str,
    opinion: str,
    statements: Sequence[str],
    previous_winner: str,
    critique: str,
) -> str:
    """
    DeepMind's prompt for ranking with both opinion and critique context.

    Args:
        question: The deliberation question
        opinion: Single participant's opinion
        statements: List of candidate consensus statements to rank
        previous_winner: The consensus from the previous round
        critique: Participant's critique of the previous winner

    Returns:
        Formatted prompt string
    """
    prompt = f"""As an AI assistant, your job is to rank these statements in the order that the participant would most likely agree with them, based on their opinion and critique to a summary statement from a previous discussion round. Use Arrow notation for the ranking, where ">" means "preferred to". Ties are NOT allowed and items should be in descending order of preference so you can ONLY use ">" and the letters of the statements in the ranking. Examples of valid rankings: B > A, D > A > C > B, B > C > A > E > D.

Please think through this task step-by-step:

1. Analyze the participant's opinion and critique, noting key points and sentiments.
2. Analyze the critique to the summary statement from the previous discussion round.
3. Compare each statement to the participant's opinion and critique, considering how well it aligns with or supports their view.
4. Consider any nuances or implications in the statements that might appeal to or repel the participant based on their expressed opinion.
5. Rank the statements accordingly using only ">" and the letters of the statements.

Provide your answer in the following format:
<answer>
[Your step-by-step reasoning and explanation for the ranking]
<sep>
[Final ranking using arrow notation]
</answer>

For example for five statements A, B, C, D and E a valid response could be:
<answer>
1. The participant's opinion emphasizes the importance of environmental protection and the need for immediate action to address climate change. The critique of the previous winner highlights that it failed to offer specific solutions.

2. The critique emphasizes the need for concrete solutions to address climate change, indicating that the participant values action-oriented approaches.

3. - Statement A directly addresses the urgency of climate action and proposes concrete steps, aligning with both the participant's opinion and critique.
  - Statements B and D acknowledge the seriousness of climate change but offer less concrete solutions. B focuses on global cooperation, while D emphasizes economic considerations.
  - Statement C downplays the urgency of climate change, contradicting the participant's stance.
  - Statement E completely opposes the participant's view by denying the existence of climate change.

4.  The participant's emphasis on immediate action suggests a preference for proactive solutions and a dislike for approaches that downplay the issue or offer only abstract ideas.

5. Based on this analysis, the ranking is: A > D > B > C > E

<sep>
A > D > B > C > E
</answer>

It is important to follow the template EXACTLY. So ALWAYS start with <answer>, then the explanation, then <sep> then only the final ranking and then </answer>.


Below you will find the question, the participant's opinion, the statement from the previous round, and a critique of that statement. You will also find a list of statements to rank.

Question: {question}

Participant's Opinion: {opinion}

Statement from previous round: {previous_winner}

Critique: {critique}

Statements to rank:
"""
    for i, statement in enumerate(statements):
        letter = chr(ord('A') + i)  # A, B, C, D, etc.
        statement = statement.strip().strip('"').strip('\n').strip()
        prompt += f'{letter}. {statement}\n'

    return prompt.strip()


# ============================================================================
# ORIGINAL SIMPLE PROMPTS (for JSON-based ranking)
# ============================================================================

def generate_simple_consensus_prompt(
    question: str,
    participant_statements: str,
) -> str:
    """
    Original simple prompt template for basic consensus generation.

    Args:
        question: The deliberation question
        participant_statements: Formatted string of all participant statements

    Returns:
        Formatted prompt string
    """
    return f"""Based on the following question and participant statements, generate a concise consensus statement that captures the common ground and shared perspectives.

Question: {question}

Participant Statements:
{participant_statements}

Generate a single consensus statement that represents the group's collective view while respecting individual perspectives."""


def generate_simple_ranking_prompt(
    question: str,
    participant_statement: str,
    candidates: str,
    num_candidates: int,
) -> str:
    """
    Original simple JSON-based ranking prompt.

    Note: DeepMind's arrow notation prompts are more reliable.
    Consider migrating to arrow notation format.

    Args:
        question: The deliberation question
        participant_statement: Single participant's statement
        candidates: Formatted string of candidate statements
        num_candidates: Number of candidates to rank

    Returns:
        Formatted prompt string requesting JSON output
    """
    return f"""You are helping determine how a participant would rank different consensus statements based on their individual perspective.

Question: {question}

Participant's Statement: {participant_statement}

Candidate Consensus Statements:
{candidates}

Rank these {num_candidates} statements from best (1) to worst ({num_candidates}) based on how well they align with this participant's perspective.

Respond ONLY with a JSON object in this exact format:
{{"ranking": [1, 2, 3, ...]}}

The ranking array must contain integers 1 through {num_candidates} in the order corresponding to the candidates listed above."""


# ============================================================================
# CHORUS STAKEHOLDER FEEDBACK PROMPTS
# ============================================================================

def generate_chorus_feedback_prompt(
    value_statement: str,
    proposal_title: str,
    proposal_text: str,
) -> str:
    """
    Prompt for simulating individual stakeholder feedback on proposals.

    Used by Habermas Chorus to generate JSON-structured responses based on
    persistent value statements without re-surveying.

    Args:
        value_statement: The stakeholder's persistent value statement
        proposal_title: Title of the proposal being evaluated
        proposal_text: Full text of the proposal

    Returns:
        Formatted prompt requesting structured JSON feedback
    """
    return f"""You are simulating how an associate would respond to a proposal based on their stated values and perspectives.

Associate's Value Statement:
{value_statement}

Proposal Title: {proposal_title}

Proposal Details:
{proposal_text}

Based on this associate's values, generate their likely response to this proposal.

Respond with a JSON object in this exact format:
{{
  "sentiment": "favorable|neutral|unfavorable",
  "concerns": ["concern1", "concern2", ...],
  "suggestions": ["suggestion1", "suggestion2", ...],
  "importance_score": <1-10>
}}

Guidelines:
- sentiment: Overall reaction (favorable/neutral/unfavorable)
- concerns: Specific worries or issues they might raise (2-4 items)
- suggestions: Constructive improvements they might propose (2-4 items)
- importance_score: How important this proposal is to them (1=low, 10=critical)

Be authentic to their stated values. Generate realistic, specific feedback."""


def generate_chorus_summary_prompt(
    proposal_title: str,
    aggregated_data: str,
) -> str:
    """
    Prompt for generating natural language summary of Chorus results.

    Args:
        proposal_title: Title of the proposal
        aggregated_data: Pre-formatted summary of feedback data

    Returns:
        Formatted prompt for LLM summarization
    """
    return f"""Generate a concise executive summary of stakeholder feedback for the following proposal.

Proposal: {proposal_title}

Aggregated Feedback Data:
{aggregated_data}

Provide a 2-3 paragraph summary that includes:
1. Overall sentiment and approval levels
2. Most common concerns and themes
3. Key suggestions for improvement
4. Any notable patterns by department/role

Keep it professional and actionable."""


# ============================================================================
# RESPONSE PARSING UTILITIES
# ============================================================================

def extract_cot_response(response: str) -> tuple[str, str]:
    """
    Extract statement and explanation from DeepMind's <answer><sep></answer> format.

    Args:
        response: Raw LLM response

    Returns:
        Tuple of (statement, explanation) or ("", "INCORRECT_TEMPLATE") on failure
    """
    import re

    match = re.search(
        r'<answer>\s*(.*?)\s*<sep>\s*(.*?)\s*</answer>',
        response,
        re.DOTALL
    )
    if match:
        explanation = match.group(1).strip()
        statement = match.group(2).strip()
        return statement, explanation
    else:
        return '', 'INCORRECT_TEMPLATE'


def extract_arrow_ranking(text: str) -> str | None:
    """
    Extract arrow notation ranking from response text.

    Looks for patterns like: A > B > C or D > A = B > C

    Args:
        text: Response text to search

    Returns:
        Extracted ranking string or None if not found
    """
    import re

    # Match full arrow ranking pattern
    match = re.search(r'\b([A-Z](?:\s*(?:>|=)\s*[A-Z])*)\b', text)

    if match:
        return match.group(1).replace(' ', '')  # Remove extra spaces
    else:
        return None


def validate_arrow_ranking(arrow_ranking: str) -> bool:
    """
    Validate arrow notation format.

    Rules:
    - Only letters A-Z, > and = allowed
    - No >> or == (consecutive operators)
    - No = at start or end
    - No => pattern
    - Each letter appears exactly once

    Args:
        arrow_ranking: String like "A > B > C"

    Returns:
        True if valid, False otherwise
    """
    import re

    if len(arrow_ranking) < 3:
        return False

    # Remove and normalize whitespace
    arrow_ranking = re.sub(r'\s+', ' ', arrow_ranking.strip())
    arrow_ranking = re.sub(r'\s*(>|=)\s*', r'\1', arrow_ranking)

    # Check allowed characters only
    if not re.match(r'^[A-Z>=]+$', arrow_ranking):
        return False

    # Check for invalid patterns
    if (
        '>>' in arrow_ranking
        or arrow_ranking.startswith('=')
        or arrow_ranking.endswith('=')
        or '=>' in arrow_ranking
    ):
        return False

    # Split by > and check each group
    groups = arrow_ranking.split('>')

    if len(groups) < 1:
        return False

    seen_letters = set()
    for group in groups:
        if not group:  # Empty group
            return False

        # Check letters in this group (tied with =)
        letters = group.split('=')
        if len(letters) != len(set(letters)):  # Duplicate in same group
            return False

        # Check if any letter seen before
        if any(letter in seen_letters for letter in letters):
            return False

        seen_letters.update(letters)

    return True
