#!/usr/bin/env python3
"""
Habermas Machine 2.0 - Main Entry Point

Simple launcher that starts the existing GUI application.
Future versions will support CLI options for different modes.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main():
    """Launch the Habermas Machine GUI application."""
    try:
        # Import the existing GUI application from the standalone file
        # Note: The HabermasMachine class is in habermas_machine.py (not the package)
        import sys
        import importlib.util

        # Load the standalone habermas_machine.py file
        spec = importlib.util.spec_from_file_location(
            "habermas_machine_gui",
            os.path.join(project_root, "habermas_machine.py")
        )
        habermas_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(habermas_module)

        import customtkinter as ctk

        # Create and run the application
        root = ctk.CTk()
        app = habermas_module.HabermasMachine(root)
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
