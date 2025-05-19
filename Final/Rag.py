import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
import threading
import time
from dataclasses import dataclass
import hashlib

# For text splitting and embedding
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize
import nltk

# For file parsing
import PyPDF2
import docx
import csv
import json

class RAGSystem:
    """
    A Retrieval-Augmented Generation system for chatbots that preloads files
    and provides context-aware responses.
    """
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2", 
                 max_chunk_size: int = 512,
                 cache_dir: str = "./rag_cache",
                 preload_nltk: bool = True):
        """
        Initialize the RAG system.
        
        Args:
            model_name: Name of the sentence transformer model to use
            max_chunk_size: Maximum chunk size for text splitting
            cache_dir: Directory to store cached embeddings
            preload_nltk: Whether to preload NLTK data
        """
        self.model_name = model_name
        self.max_chunk_size = max_chunk_size
        self.cache_dir = cache_dir
        self.documents = {}
        self.document_chunks = {}
        self.document_embeddings = {}
        self.embedding_model = None
        self._load_lock = threading.Lock()
        self._loaded = False
        self._loading_thread = None

        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        # Preload NLTK data if requested
        if preload_nltk:
            try:
                nltk.download('punkt', quiet=True)
            except:
                print("Warning: NLTK punkt download failed. Sentence splitting may be affected.")
                
        # Start loading the embedding model in the background
        self._start_loading()
        
    def _start_loading(self):
        """Start loading the embedding model in a background thread"""
        self._loading_thread = threading.Thread(target=self._load_model)
        self._loading_thread.daemon = True
        self._loading_thread.start()
        
    def _load_model(self):
        """Load the embedding model"""
        with self._load_lock:
            if not self._loaded:
                print(f"Loading embedding model {self.model_name}...")
                self.embedding_model = SentenceTransformer(self.model_name)
                self._loaded = True
                print("Embedding model loaded successfully")
    
    def wait_until_loaded(self, timeout: Optional[float] = None) -> bool:
        """
        Wait until the embedding model is loaded.
        
        Args:
            timeout: Maximum time to wait in seconds. None means wait indefinitely.
            
        Returns:
            True if loaded successfully, False if timed out
        """
        start_time = time.time()
        while not self._loaded:
            if timeout is not None and time.time() - start_time > timeout:
                return False
            time.sleep(0.1)
        return True
    
    def is_ready(self) -> bool:
        """Check if the RAG system is fully loaded and ready"""
        return self._loaded
        
    def _get_file_hash(self, file_path: str) -> str:
        """Get a hash of the file for caching purposes"""
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return file_hash
    
    def _get_cache_path(self, file_path: str) -> str:
        """Get the cache path for a file"""
        file_hash = self._get_file_hash(file_path)
        base_name = os.path.basename(file_path)
        cache_name = f"{base_name}_{file_hash}.pkl"
        return os.path.join(self.cache_dir, cache_name)
    
    def _load_from_cache(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Try to load document embeddings from cache"""
        cache_path = self._get_cache_path(file_path)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except:
                return None
        return None
    
    def _save_to_cache(self, file_path: str, data: Dict[str, Any]) -> None:
        """Save document embeddings to cache"""
        cache_path = self._get_cache_path(file_path)
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
    
    def _read_text_file(self, file_path: str) -> str:
        """Read a plain text file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _read_pdf_file(self, file_path: str) -> str:
        """Read a PDF file"""
        text = ""
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _read_docx_file(self, file_path: str) -> str:
        """Read a DOCX file"""
        doc = docx.Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    
    def _read_csv_file(self, file_path: str) -> str:
        """Read a CSV file"""
        text = ""
        with open(file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            for row in csv_reader:
                text += " | ".join(row) + "\n"
        return text
    
    def _read_json_file(self, file_path: str) -> str:
        """Read a JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
    
    def _read_file(self, file_path: str) -> str:
        """Read a file based on its extension"""
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == '.txt':
            return self._read_text_file(file_path)
        elif ext == '.pdf':
            return self._read_pdf_file(file_path)
        elif ext == '.docx':
            return self._read_docx_file(file_path)
        elif ext == '.csv':
            return self._read_csv_file(file_path)
        elif ext == '.json':
            return self._read_json_file(file_path)
        else:
            # Try reading as plain text
            return self._read_text_file(file_path)
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks for embedding"""
        # First split by sentences
        sentences = sent_tokenize(text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed the chunk size,
            # store the current chunk and start a new one
            if len(current_chunk) + len(sentence) > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
    
    def _compute_embeddings(self, chunks: List[str]) -> np.ndarray:
        """Compute embeddings for a list of text chunks"""
        self.wait_until_loaded()  # Ensure model is loaded
        return self.embedding_model.encode(chunks)
    
    def add_file(self, file_path: str, doc_id: Optional[str] = None) -> str:
        """
        Add a file to the RAG system.
        
        Args:
            file_path: Path to the file
            doc_id: Optional document ID, defaults to the file name
            
        Returns:
            The document ID
        """
        if not doc_id:
            doc_id = os.path.basename(file_path)
        
        # Check if we have a cached version
        cached_data = self._load_from_cache(file_path)
        
        if cached_data:
            print(f"Loading {file_path} from cache")
            self.documents[doc_id] = cached_data['text']
            self.document_chunks[doc_id] = cached_data['chunks']
            self.document_embeddings[doc_id] = cached_data['embeddings']
        else:
            print(f"Processing {file_path}")
            # Read the file
            text = self._read_file(file_path)
            
            # Split into chunks
            chunks = self._split_text(text)
            
            # Compute embeddings
            embeddings = self._compute_embeddings(chunks)
            
            # Store the results
            self.documents[doc_id] = text
            self.document_chunks[doc_id] = chunks
            self.document_embeddings[doc_id] = embeddings
            
            # Cache the results
            cache_data = {
                'text': text,
                'chunks': chunks,
                'embeddings': embeddings
            }
            self._save_to_cache(file_path, cache_data)
        
        return doc_id
    
    def add_text(self, text: str, doc_id: str) -> str:
        """
        Add text directly to the RAG system.
        
        Args:
            text: The text to add
            doc_id: Document ID
            
        Returns:
            The document ID
        """
        # Split into chunks
        chunks = self._split_text(text)
        
        # Compute embeddings
        embeddings = self._compute_embeddings(chunks)
        
        # Store the results
        self.documents[doc_id] = text
        self.document_chunks[doc_id] = chunks
        self.document_embeddings[doc_id] = embeddings
        
        return doc_id
    
    def remove_document(self, doc_id: str) -> bool:
        """
        Remove a document from the RAG system.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if the document was removed, False otherwise
        """
        if doc_id in self.documents:
            del self.documents[doc_id]
            del self.document_chunks[doc_id]
            del self.document_embeddings[doc_id]
            return True
        return False
    
    def list_documents(self) -> List[str]:
        """
        List all document IDs in the RAG system.
        
        Returns:
            List of document IDs
        """
        return list(self.documents.keys())
    
    def _get_document_info(self, doc_id: str) -> Dict[str, Any]:
        """Get information about a document"""
        if doc_id not in self.documents:
            return {}
        
        return {
            'doc_id': doc_id,
            'length': len(self.documents[doc_id]),
            'chunks': len(self.document_chunks[doc_id]),
        }
    
    def get_all_document_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all documents.
        
        Returns:
            Dictionary mapping document IDs to document information
        """
        return {doc_id: self._get_document_info(doc_id) for doc_id in self.documents}
    
    def _compute_query_embedding(self, query: str) -> np.ndarray:
        """Compute embedding for a query"""
        self.wait_until_loaded()  # Ensure model is loaded
        return self.embedding_model.encode([query])[0]
    
    def _compute_similarity(self, query_embedding: np.ndarray, doc_embeddings: np.ndarray) -> np.ndarray:
        """Compute cosine similarity between query and document embeddings"""
        # Normalize embeddings
        query_embedding_norm = query_embedding / np.linalg.norm(query_embedding)
        doc_embeddings_norm = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
        
        # Compute cosine similarity
        return np.dot(doc_embeddings_norm, query_embedding_norm)
    
    @dataclass
    class RetrievalResult:
        """Class for storing retrieval results"""
        doc_id: str
        chunk_index: int
        chunk_text: str
        similarity: float
        
    def retrieve(self, 
                query: str, 
                top_k: int = 3, 
                min_similarity: float = 0.3, 
                doc_ids: Optional[List[str]] = None) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: The query to retrieve chunks for
            top_k: Maximum number of chunks to retrieve
            min_similarity: Minimum similarity score for retrieved chunks
            doc_ids: Optional list of document IDs to restrict retrieval to
            
        Returns:
            List of RetrievalResult objects
        """
        if not self.documents:
            return []
        
        # If doc_ids is not provided, use all documents
        if doc_ids is None:
            doc_ids = list(self.documents.keys())
        else:
            # Filter out non-existent doc_ids
            doc_ids = [doc_id for doc_id in doc_ids if doc_id in self.documents]
            
        if not doc_ids:
            return []
        
        # Compute query embedding
        query_embedding = self._compute_query_embedding(query)
        
        results = []
        
        # Process each document
        for doc_id in doc_ids:
            doc_embeddings = self.document_embeddings[doc_id]
            chunks = self.document_chunks[doc_id]
            
            # Compute similarities
            similarities = self._compute_similarity(query_embedding, doc_embeddings)
            
            # Get indices of chunks with similarity above threshold
            indices = np.where(similarities >= min_similarity)[0]
            
            # Sort by similarity (descending)
            indices = indices[np.argsort(-similarities[indices])]
            
            # Add results
            for i in indices:
                results.append(self.RetrievalResult(
                    doc_id=doc_id,
                    chunk_index=i,
                    chunk_text=chunks[i],
                    similarity=float(similarities[i])
                ))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x.similarity, reverse=True)
        
        # Return top_k results
        return results[:top_k]
    
    def get_context(self, query: str, top_k: int = 3, min_similarity: float = 0.3) -> str:
        """
        Get context for a query as a formatted string.
        
        Args:
            query: The query to retrieve context for
            top_k: Maximum number of chunks to retrieve
            min_similarity: Minimum similarity score for retrieved chunks
            
        Returns:
            Formatted string with context information
        """
        results = self.retrieve(query, top_k, min_similarity)
        
        if not results:
            return "No relevant context found."
        
        context_str = "Relevant context:\n\n"
        
        for i, result in enumerate(results):
            context_str += f"[{i+1}] From {result.doc_id} (similarity: {result.similarity:.4f}):\n"
            context_str += f"{result.chunk_text}\n\n"
        
        return context_str
    
    def query_with_context(self, query: str, top_k: int = 3, min_similarity: float = 0.3) -> Tuple[str, List[RetrievalResult]]:
        """
        Get a query with context for an LLM.
        
        Args:
            query: The query to retrieve context for
            top_k: Maximum number of chunks to retrieve
            min_similarity: Minimum similarity score for retrieved chunks
            
        Returns:
            Tuple of (formatted query with context, list of retrieved results)
        """
        results = self.retrieve(query, top_k, min_similarity)
        
        if not results:
            return query, []
        
        context_str = "Here is some relevant context to help answer the question:\n\n"
        
        for i, result in enumerate(results):
            context_str += f"[Context {i+1}] From {result.doc_id}:\n"
            context_str += f"{result.chunk_text}\n\n"
        
        context_str += f"Question: {query}\n\n"
        context_str += "Please answer the question based on the provided context. If the context doesn't contain relevant information, say so."
        
        return context_str, results


class ChatbotWithRAG:
    """
    A chatbot that uses RAG to enhance responses.
    """
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 cache_dir: str = "./rag_cache",
                 auto_load_files: Optional[List[str]] = None):
        """
        Initialize the chatbot with RAG.
        
        Args:
            model_name: Name of the sentence transformer model to use
            cache_dir: Directory to store cached embeddings
            auto_load_files: Optional list of files to load automatically
        """
        # Initialize the RAG system
        self.rag = RAGSystem(model_name=model_name, cache_dir=cache_dir)
        
        # Load files if provided
        if auto_load_files:
            for file_path in auto_load_files:
                self.rag.add_file(file_path)
                
        # Wait for the RAG system to be ready
        self.rag.wait_until_loaded()
        print("ChatbotWithRAG is ready!")
    
    def add_file(self, file_path: str, doc_id: Optional[str] = None) -> str:
        """
        Add a file to the RAG system.
        
        Args:
            file_path: Path to the file
            doc_id: Optional document ID
            
        Returns:
            The document ID
        """
        return self.rag.add_file(file_path, doc_id)
    
    def add_text(self, text: str, doc_id: str) -> str:
        """
        Add text directly to the RAG system.
        
        Args:
            text: The text to add
            doc_id: Document ID
            
        Returns:
            The document ID
        """
        return self.rag.add_text(text, doc_id)
    
    def remove_document(self, doc_id: str) -> bool:
        """
        Remove a document from the RAG system.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if the document was removed, False otherwise
        """
        return self.rag.remove_document(doc_id)
    
    def list_documents(self) -> List[str]:
        """
        List all document IDs in the RAG system.
        
        Returns:
            List of document IDs
        """
        return self.rag.list_documents()
    
    def get_document_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all documents.
        
        Returns:
            Dictionary mapping document IDs to document information
        """
        return self.rag.get_all_document_info()
    
    def process_query(self, query: str, top_k: int = 3, min_similarity: float = 0.3) -> Dict[str, Any]:
        """
        Process a user query using RAG.
        
        Args:
            query: The user query
            top_k: Maximum number of chunks to retrieve
            min_similarity: Minimum similarity score for retrieved chunks
            
        Returns:
            Dictionary with query context and retrieval results
        """
        context_query, results = self.rag.query_with_context(query, top_k, min_similarity)
        
        # In a real chatbot, you would send context_query to an LLM here
        # For demonstration, we'll just return the context
        
        return {
            'original_query': query,
            'context_query': context_query,
            'retrieved_chunks': [
                {
                    'doc_id': r.doc_id,
                    'chunk_index': r.chunk_index,
                    'similarity': r.similarity,
                    'text': r.chunk_text
                }
                for r in results
            ]
        }
    
    def is_ready(self) -> bool:
        """Check if the chatbot is ready to process queries"""
        return self.rag.is_ready()

if __name__ == "__main__":

    # Create a chatbot with RAG
    chatbot = ChatbotWithRAG(
        auto_load_files=["1.pdf"]  # Optional: load files at startup
    )
    
    # Check if the chatbot is ready
    if chatbot.is_ready():
        print("Chatbot is ready to process queries!")
    else:
        print("Waiting for chatbot to be ready...")
        while not chatbot.is_ready():
            time.sleep(0.1)
        print("Chatbot is now ready!")
    
    # Add more files
    chatbot.add_file("2.pdf")
    
    # Process a query
    result = chatbot.process_query("Bhopal?")
    print(result['context_query'])

