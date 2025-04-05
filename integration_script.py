"""
This script demonstrates how to integrate the enhanced Habermas Chorus extensions
into the main Habermas Machine application.
"""

from habermas_machine import HabermasMachine
from habermas_chorus_extension import HabermasChorusExtension

# Import our new components
from vector_embedding_helper import OllamaEmbeddingHelper
from habermas_llm_summarizer import HabermasLLMSummarizer
from chorus_improvements import VerbalSamplingManager

class EnhancedHabermasChorusExtension(HabermasChorusExtension):
    """
    Enhanced version of the Habermas Chorus Extension with improved
    verbatim sampling and result presentation
    """
    
    def __init__(self, habermas_machine):
        """Initialize the extension with reference to the main app"""
        super().__init__(habermas_machine)
        
        # Initialize the verbal sampling manager
        self.verbal_sampling_manager = VerbalSamplingManager()
        
        # Initialize Ollama embedding helper if available
        self.embedding_helper = OllamaEmbeddingHelper()
        
        # Initialize LLM summarizer if available
        self.llm_summarizer = HabermasLLMSummarizer(model=self.app.model_var.get())
        
        # Set up enhanced methods
        self._enhance_methods()
    
    def _enhance_methods(self):
        """Replace methods with enhanced versions"""
        # Save original methods as fallbacks
        self._original_update_concerns = self.update_concerns_chart_with_data
        self._original_update_suggestions = self.update_suggestions_list_with_data
        self._original_update_results = self.update_chorus_results
        
        # Replace with enhanced methods
        from chorus_improvements import enhance_habermas_chorus_extension
        enhanced_class = enhance_habermas_chorus_extension(HabermasChorusExtension)
        
        from types import MethodType
        self.update_concerns_chart_with_data = MethodType(
            enhanced_class.update_concerns_chart_with_data, self
        )
        
        self.update_suggestions_list_with_data = MethodType(
            enhanced_class.update_suggestions_list_with_data, self
        )
        
        self.update_chorus_results = MethodType(
            enhanced_class.update_chorus_results, self
        )
    
    def get_embedding_for_text(self, text):
        """Get embedding vector for text using available methods"""
        if self.embedding_helper and self.embedding_helper.available:
            return self.embedding_helper.get_embedding(text)
        else:
            # Fallback to the verbal sampling manager's method
            return self.verbal_sampling_manager.get_embedding(text)
    
    def generate_llm_summary(self, results, proposal_title, proposal_text, 
                            representative_statements=None, top_concerns=None, 
                            department_insights=None):
        """Generate an LLM-powered summary"""
        if self.llm_summarizer and self.llm_summarizer.available:
            return self.llm_summarizer.generate_summary(
                results, 
                proposal_title, 
                proposal_text,
                representative_statements,
                top_concerns,
                department_insights
            )
        else:
            # Fallback to the original summary method
            return None
    
    def generate_llm_suggestions(self, results, suggestion_counts, 
                                suggestion_statements, categories):
        """Generate an LLM-powered suggestions summary"""
        if self.llm_summarizer and self.llm_summarizer.available:
            return self.llm_summarizer.generate_suggestions_summary(
                results,
                suggestion_counts,
                suggestion_statements,
                categories
            )
        else:
            # Fallback to the original suggestions method
            return None


def main():
    """Run the enhanced Habermas Machine with Chorus Extension"""
    import tkinter as tk
    import customtkinter as ctk
    
    try:
        # Initialize the main application
        root = ctk.CTk()
        root.protocol("WM_DELETE_WINDOW", lambda: (root.quit(), root.destroy()))
        
        # Set window title and size
        root.title("Enhanced Habermas Machine with Chorus Extension")
        root.geometry("1800x900")
        
        # Set up the main Habermas Machine
        app = HabermasMachine(root)
        
        # Add the Enhanced Chorus extension
        chorus_extension = EnhancedHabermasChorusExtension(app)
        
        # Set window title (no startup message needed)
        root.title("Enhanced Habermas Machine with Chorus Extension")
        
        # Start the main loop
        root.mainloop()
        
    except Exception as e:
        # Create error window if initialization fails
        error_root = tk.Tk()
        error_root.title("Error")
        error_root.geometry("600x400")
        error_root.configure(bg="#2b2b2b")
        
        import traceback
        
        tk.Label(
            error_root, 
            text="Error Starting Enhanced Habermas Machine", 
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
