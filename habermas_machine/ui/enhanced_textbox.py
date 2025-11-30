"""
Enhanced textbox with visual line demarcation for better readability.

Copyright (C) 2025  Habermas Machine Project

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

import customtkinter as ctk
import tkinter as tk


class EnhancedTextbox(ctk.CTkTextbox):
    """
    A textbox with visual line demarcation:
    - Zebra striping (alternating background colors)
    - Spacing between true lines (not wrapped lines)
    - Maintains seamless copy/paste experience
    """

    def __init__(self, master, line_spacing=8, line_padding=6, horizontal_padding=12, zebra_colors=None, **kwargs):
        """
        Args:
            master: Parent widget
            line_spacing: Vertical spacing in pixels between lines (default: 8)
            line_padding: Vertical padding in pixels above/below each line (default: 6)
            horizontal_padding: Horizontal padding (left/right margins) in pixels (default: 12)
            zebra_colors: Tuple of (even_color, odd_color) for alternating rows
                         If None, uses subtle default colors based on theme
            **kwargs: All other CTkTextbox arguments
        """
        super().__init__(master, **kwargs)

        self.line_spacing = line_spacing
        self.line_padding = line_padding
        self.horizontal_padding = horizontal_padding

        # Set default zebra colors based on appearance mode if not provided
        if zebra_colors is None:
            # Use subtle colors that work in dark mode
            appearance = ctk.get_appearance_mode()
            if appearance == "Dark":
                self.zebra_colors = ("#2b2b2b", "#242424")  # Subtle dark grays
            else:
                self.zebra_colors = ("#f5f5f5", "#ffffff")  # Subtle light grays
        else:
            self.zebra_colors = zebra_colors

        # Configure text tags for zebra striping and spacing
        self._configure_tags()

        # Bind events to update styling dynamically
        self.bind("<<Modified>>", self._on_text_modified)
        self.bind("<KeyRelease>", lambda e: self._schedule_update())
        self.bind("<ButtonRelease-1>", lambda e: self._schedule_update())

        # Track if we need to update styling
        self._update_pending = False

    def _configure_tags(self):
        """Configure text tags for visual styling."""
        # Configure tags for alternating line backgrounds
        self._textbox.tag_configure(
            "even_line",
            background=self.zebra_colors[0],
            spacing1=self.line_padding,  # Space before line (top padding)
            spacing3=self.line_padding + self.line_spacing,  # Space after line (bottom padding + gap)
            lmargin1=self.horizontal_padding,  # Left margin for first line of entry
            lmargin2=self.horizontal_padding,  # Left margin for wrapped lines
            rmargin=self.horizontal_padding    # Right margin
        )
        self._textbox.tag_configure(
            "odd_line",
            background=self.zebra_colors[1],
            spacing1=self.line_padding,  # Space before line (top padding)
            spacing3=self.line_padding + self.line_spacing,  # Space after line (bottom padding + gap)
            lmargin1=self.horizontal_padding,  # Left margin for first line of entry
            lmargin2=self.horizontal_padding,  # Left margin for wrapped lines
            rmargin=self.horizontal_padding    # Right margin
        )

        # Configure tags for empty lines (to maintain spacing)
        self._textbox.tag_configure(
            "empty_line",
            spacing1=self.line_padding,
            spacing3=self.line_padding + self.line_spacing,
            lmargin1=self.horizontal_padding,
            lmargin2=self.horizontal_padding,
            rmargin=self.horizontal_padding
        )

    def _schedule_update(self):
        """Schedule a styling update (debounced)."""
        if not self._update_pending:
            self._update_pending = True
            self.after(50, self._apply_line_styling)

    def _on_text_modified(self, event):
        """Handle text modification events."""
        # Reset the modified flag
        try:
            self._textbox.edit_modified(False)
        except tk.TclError:
            pass

        self._schedule_update()

    def _apply_line_styling(self):
        """Apply zebra striping and spacing to all lines."""
        self._update_pending = False

        # Remove all existing tags
        self._textbox.tag_remove("even_line", "1.0", "end")
        self._textbox.tag_remove("odd_line", "1.0", "end")
        self._textbox.tag_remove("empty_line", "1.0", "end")

        # Get total number of lines
        end_line = int(self._textbox.index("end-1c").split(".")[0])

        # Apply tags to each line
        for line_num in range(1, end_line + 1):
            line_start = f"{line_num}.0"
            line_end = f"{line_num}.end"

            # Check if line is empty
            line_content = self._textbox.get(line_start, line_end)

            if line_content.strip():  # Non-empty line
                # Apply zebra striping
                tag = "even_line" if line_num % 2 == 0 else "odd_line"
                self._textbox.tag_add(tag, line_start, line_end)
            else:  # Empty line
                self._textbox.tag_add("empty_line", line_start, line_end)

    def insert(self, index, text, tags=None):
        """Override insert to apply styling after insertion."""
        super().insert(index, text, tags)
        self._schedule_update()

    def delete(self, start, end=None):
        """Override delete to apply styling after deletion."""
        super().delete(start, end)
        self._schedule_update()

    def update_colors(self, zebra_colors):
        """Update zebra stripe colors and refresh display."""
        self.zebra_colors = zebra_colors
        self._configure_tags()
        self._apply_line_styling()
