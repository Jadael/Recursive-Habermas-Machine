"""
File utilities for the Habermas Machine.

This module handles file I/O operations including:
- Saving consensus results
- Bulk importing participant statements
- Loading/saving configurations

Copyright (C) 2025  Habermas Machine Project

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_session_id() -> str:
    """
    Generate a unique session ID based on current timestamp.

    Returns:
        Session ID in format: YYYYMMDD_HHMMSS

    Example:
        >>> session_id = generate_session_id()
        >>> len(session_id)
        15
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_friendly_output(
    content: str,
    session_id: str,
    output_dir: str = "."
) -> Optional[Path]:
    """
    Save user-friendly consensus results to a markdown file.

    Args:
        content: The markdown content to save
        session_id: Unique session identifier
        output_dir: Directory to save file in (default: current directory)

    Returns:
        Path to saved file, or None if save failed

    Example:
        >>> content = "# Consensus Results\\n\\nWinner: Statement 1"
        >>> path = save_friendly_output(content, "20250129_120000")
        >>> path.name
        'habermas_results_20250129_120000.md'
    """
    try:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filepath = output_dir / f"habermas_results_{session_id}.md"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Saved friendly output to {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Failed to save friendly output: {e}", exc_info=True)
        return None


def save_detailed_output(
    content: str,
    session_id: str,
    output_dir: str = "."
) -> Optional[Path]:
    """
    Save detailed process records to a markdown file.

    This includes matrices, voting details, and full prompts/responses.

    Args:
        content: The markdown content to save
        session_id: Unique session identifier
        output_dir: Directory to save file in (default: current directory)

    Returns:
        Path to saved file, or None if save failed

    Example:
        >>> content = "# Detailed Process Log\\n\\n## Pairwise Matrix\\n..."
        >>> path = save_detailed_output(content, "20250129_120000")
        >>> path.name
        'habermas_detailed_20250129_120000.md'
    """
    try:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filepath = output_dir / f"habermas_detailed_{session_id}.md"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Saved detailed output to {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Failed to save detailed output: {e}", exc_info=True)
        return None


def save_recursive_results(
    content: str,
    session_id: str,
    output_dir: str = "."
) -> Optional[Path]:
    """
    Save recursive consensus results to a markdown file.

    Args:
        content: The markdown content to save
        session_id: Unique session identifier
        output_dir: Directory to save file in (default: current directory)

    Returns:
        Path to saved file, or None if save failed
    """
    try:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filepath = output_dir / f"habermas_recursive_results_{session_id}.md"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Saved recursive results to {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Failed to save recursive results: {e}", exc_info=True)
        return None


def save_recursive_detailed(
    content: str,
    session_id: str,
    output_dir: str = "."
) -> Optional[Path]:
    """
    Save detailed recursive consensus process to a markdown file.

    Args:
        content: The markdown content to save
        session_id: Unique session identifier
        output_dir: Directory to save file in (default: current directory)

    Returns:
        Path to saved file, or None if save failed
    """
    try:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filepath = output_dir / f"habermas_recursive_detailed_{session_id}.md"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Saved detailed recursive log to {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Failed to save recursive detailed log: {e}", exc_info=True)
        return None


def load_participant_statements_from_file(filepath: str) -> List[str]:
    """
    Load participant statements from a text file.

    The file should have one statement per line. Empty lines and lines
    starting with # are ignored.

    Args:
        filepath: Path to the file containing statements

    Returns:
        List of participant statements

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is empty or contains no valid statements

    Example:
        >>> # Assuming file contains:
        >>> # I support option A
        >>> # I prefer option B
        >>> statements = load_participant_statements_from_file("input.txt")
        >>> len(statements)
        2
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    statements = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            # Strip whitespace
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            statements.append(line)

    if not statements:
        raise ValueError(f"No valid statements found in {filepath}")

    logger.info(f"Loaded {len(statements)} statements from {filepath}")
    return statements


def export_statements_to_file(
    statements: List[str],
    filepath: str,
    include_header: bool = True
) -> Optional[Path]:
    """
    Export participant statements to a text file.

    Args:
        statements: List of statements to export
        filepath: Path to save the file
        include_header: Whether to include a descriptive header

    Returns:
        Path to saved file, or None if save failed

    Example:
        >>> statements = ["I support X", "I oppose Y"]
        >>> path = export_statements_to_file(statements, "export.txt")
        >>> path.name
        'export.txt'
    """
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            if include_header:
                f.write("# Participant Statements\n")
                f.write("# One statement per line\n")
                f.write("# Lines starting with # are ignored\n\n")

            for statement in statements:
                f.write(f"{statement}\n")

        logger.info(f"Exported {len(statements)} statements to {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Failed to export statements: {e}", exc_info=True)
        return None


def parse_bulk_import_text(text: str) -> List[str]:
    """
    Parse participant statements from bulk-imported text.

    Handles various formats:
    - One statement per line
    - Numbered lists (1., 2., etc.)
    - Bullet points (-, *, •)
    - Empty lines between statements

    Args:
        text: Raw text containing statements

    Returns:
        List of parsed statements

    Example:
        >>> text = '''
        ... 1. First statement
        ... 2. Second statement
        ... - Third statement
        ... '''
        >>> parse_bulk_import_text(text)
        ['First statement', 'Second statement', 'Third statement']
    """
    statements = []

    for line in text.split('\n'):
        # Strip whitespace
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue

        # Remove common list prefixes
        # Match patterns like: "1.", "1)", "-", "*", "•"
        import re
        line = re.sub(r'^(\d+[\.\)]|\-|\*|\•)\s+', '', line)

        # Only add if there's still content
        if line:
            statements.append(line)

    return statements


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing/replacing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for all platforms

    Example:
        >>> sanitize_filename("My File: Test?")
        'My_File_Test'
    """
    import re
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    # Collapse multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized
