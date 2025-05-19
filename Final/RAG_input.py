from Rag import ChatbotWithRAG
import time

class RAGQueryProcessor:
    """A class to manage RAG chatbot initialization and query processing."""
    
    def __init__(self, auto_load_files=None):
        """Initialize the RAG Query Processor.
        
        Args:
            auto_load_files (list, optional): List of files to load at initialization.
        """
        self.chatbot = None
        self.auto_load_files = auto_load_files if auto_load_files else ["1.pdf"]
        
    def initialize_chatbot(self):
        """Initialize and load the RAG chatbot with necessary files."""
        self.chatbot = ChatbotWithRAG(
            auto_load_files=self.auto_load_files
        )
        self.chatbot.add_file("2.pdf")
        return self.chatbot
    
    def process_query(self, text):
        """Process a user query using the initialized chatbot.
        
        Args:
            text: The query text to process
            
        Returns:
            The context_query result from processing
        """
        if self.chatbot is None:
            self.initialize_chatbot()
            
        result = self.chatbot.process_query(text)
        return result['context_query']
    
    def user_input_with_rag(self, text):
        """Complete workflow that ensures the chatbot is initialized and processes the query."""
        if self.chatbot is None:
            self.initialize_chatbot()
        
        return self.process_query(text)