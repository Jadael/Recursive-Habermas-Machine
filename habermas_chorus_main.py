"""
Habermas Machine with Chorus Extension
Integration file - run this to launch the extended application
"""

import sys
import tkinter as tk
import tkinter.messagebox as messagebox
import traceback

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

# Try to import matplotlib for visualizations
try:
    import matplotlib
    matplotlib.use('TkAgg')  # Use TkAgg backend for embedding in Tkinter
    import matplotlib.pyplot as plt
except ImportError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Missing Dependency", 
        "The matplotlib package is required for visualizations but not installed.\n\n"
        "Please install it using pip:\n"
        "pip install matplotlib"
    )
    sys.exit(1)

# Import main Habermas Machine application
try:
    from habermas_machine import HabermasMachine
except ImportError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Missing File", 
        "The habermas_machine.py file is missing.\n\n"
        "Please ensure it is in the same directory as this script."
    )
    sys.exit(1)

# Import the Chorus extension
try:
    from habermas_chorus_extension import HabermasChorusExtension
except ImportError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Missing File", 
        "The habermas_chorus_extension.py file is missing.\n\n"
        "Please ensure it is in the same directory as this script."
    )
    sys.exit(1)

def main():
    try:
        # Initialize the main application
        root = ctk.CTk()
        root.protocol("WM_DELETE_WINDOW", lambda: (root.quit(), root.destroy()))
        
        # Set window title and size
        root.title("Habermas Machine with Chorus Extension")
        root.geometry("1800x900")
        
        # Set up the main Habermas Machine
        app = HabermasMachine(root)
        
        # Add the Chorus extension
        chorus_extension = HabermasChorusExtension(app)
        
        # Display startup message
        messagebox.showinfo(
            "Habermas Machine with Chorus Extension",
            "Welcome to the Habermas Machine with Chorus Extension.\n\n"
            "This tool combines consensus-building with stakeholder feedback analysis.\n\n"
            "Make sure Ollama is running with a suitable LLM (e.g., DeepSeek-R1) before proceeding."
        )
        
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
