#!/usr/bin/env python3
"""
Habermas Machine - Main Entry Point

Launches the Habermas Machine GUI application with both:
- Consensus Builder (original Habermas Machine)
- Chorus Extension (value repository and proposal feedback)
"""

import sys
import os

def main():
    """Launch the Habermas Machine GUI application."""
    try:
        import customtkinter as ctk
        from habermas_machine_app import HabermasMachine

        # Create and run the application
        root = ctk.CTk()
        app = HabermasMachine(root)
        root.mainloop()

    except ImportError as e:
        print(f"Error: Missing required dependencies.")
        print(f"Details: {e}")
        print("\nPlease install required packages:")
        print("  pip install customtkinter requests numpy matplotlib pillow scikit-learn")
        print("\nAlso ensure Ollama is installed and running:")
        print("  https://ollama.com")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting Habermas Machine: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
