"""
Retriever component for RAG pipeline.
"""
import os
import yaml
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Any

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import faiss
except ImportError:
    faiss = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    RecursiveCharacterTextSplitter = None

from monitoring.logger import Logger

class Retriever:
    """
    Handles loading, chunking, embedding, and retrieving documents.
    """
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Retriever with config.
        """
        self.logger = Logger(__name__)
        if config is None:
            config_path = Path("config/config.yaml")
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
            else:
                config = {}
        
        rag_config = config.get("rag", {})
        self.embedding_model = rag_config.get("embedding_model", "all-MiniLM-L6-v2")
        self.chunk_size = rag_config.get("chunk_size", 500)
        self.chunk_overlap = rag_config.get("chunk_overlap", 50)
        self.top_k = rag_config.get("top_k", 5)
        self.vector_store_path = rag_config.get("vector_store_path", "data/vector_store")
        self.supported_file_types = rag_config.get("supported_file_types", [".pdf", ".md", ".txt"])
        
        self._embeddings = None
        self._vector_store = None
        self.chunks = []
        self.metadata = []
        self.embeddings_array = None

    def _initialize_embeddings(self):
        if self._embeddings is None:
            if SentenceTransformer is None:
                raise ImportError("sentence_transformers is not installed.")
            self._embeddings = SentenceTransformer(self.embedding_model)

    def _load_document(self, file_path: str) -> List[str]:
        ext = Path(file_path).suffix.lower()
        if ext not in self.supported_file_types:
            self.logger.warning(f"Unsupported file type: {ext}")
            return []
            
        texts = []
        if ext == ".pdf":
            if PyPDF2 is None:
                self.logger.warning("PyPDF2 not installed. Falling back to text read.")
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        texts.append(f.read())
                except Exception as e:
                    self.logger.error(f"Failed to read PDF as text: {e}")
            else:
                try:
                    with open(file_path, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        for page in reader.pages:
                            text = page.extract_text()
                            if text:
                                texts.append(text)
                except Exception as e:
                    self.logger.error(f"Error reading PDF: {e}")
        else:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    texts.append(f.read())
            except Exception as e:
                self.logger.error(f"Error reading file {file_path}: {e}")
        return texts

    def _split_text(self, texts: List[str]) -> List[str]:
        if not texts:
            return []
        if RecursiveCharacterTextSplitter is None:
            self.logger.warning("langchain not installed, doing naive split.")
            chunks = []
            for t in texts:
                for i in range(0, len(t), self.chunk_size - self.chunk_overlap):
                    chunks.append(t[i:i + self.chunk_size])
            return chunks
            
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        return splitter.split_text("\n\n".join(texts))

    def ingest(self, file_paths: List[str], access_level: str = 'public') -> int:
        self._initialize_embeddings()
        all_chunks = []
        new_metadata = []
        
        for fp in file_paths:
            texts = self._load_document(fp)
            chunks = self._split_text(texts)
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                new_metadata.append({
                    "source": fp,
                    "access_level": access_level,
                    "chunk_index": i
                })
                
        if not all_chunks:
            return 0
            
        embs = self._embeddings.encode(all_chunks)
        
        if self._vector_store is None:
            if faiss is None or np is None:
                raise ImportError("faiss or numpy not installed.")
            d = embs.shape[1]
            self._vector_store = faiss.IndexFlatL2(d)
            self.embeddings_array = np.array(embs).astype("float32")
        else:
            self.embeddings_array = np.vstack([self.embeddings_array, embs])
            
        self._vector_store.add(np.array(embs).astype("float32"))
        self.chunks.extend(all_chunks)
        self.metadata.extend(new_metadata)
        
        os.makedirs(os.path.dirname(self.vector_store_path) or ".", exist_ok=True)
        self.save_index(self.vector_store_path)
        
        return len(all_chunks)

    def retrieve(self, query: str, user: Any = None, top_k: Optional[int] = None) -> List[Dict]:
        if self._vector_store is None:
            return []
            
        self._initialize_embeddings()
        if faiss is None or np is None:
            raise ImportError("faiss or numpy not installed.")
            
        q_emb = self._embeddings.encode([query])
        k = top_k or self.top_k
        
        search_k = min(len(self.chunks), k * 5)
        distances, indices = self._vector_store.search(np.array(q_emb).astype("float32"), search_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            meta = self.metadata[idx]
            
            if user is not None:
                user_roles = getattr(user, "roles", [])
                is_admin = "admin" in user_roles
                if not is_admin:
                    if meta.get("access_level") != "public" and meta.get("access_level") not in user_roles:
                        continue
                        
            results.append({
                "content": self.chunks[idx],
                "metadata": meta,
                "score": float(dist)
            })
            if len(results) >= k:
                break
                
        return results

    def save_index(self, path: Optional[str] = None):
        if self._vector_store is None or faiss is None:
            return
        p = path or self.vector_store_path
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
        faiss.write_index(self._vector_store, f"{p}.index")
        with open(f"{p}.pkl", "wb") as f:
            pickle.dump({
                "chunks": self.chunks,
                "metadata": self.metadata,
                "embeddings": self.embeddings_array
            }, f)

    def load_index(self, path: Optional[str] = None):
        p = path or self.vector_store_path
        if faiss is None:
            return
        try:
            if os.path.exists(f"{p}.index") and os.path.exists(f"{p}.pkl"):
                self._vector_store = faiss.read_index(f"{p}.index")
                with open(f"{p}.pkl", "rb") as f:
                    data = pickle.load(f)
                    self.chunks = data["chunks"]
                    self.metadata = data["metadata"]
                    self.embeddings_array = data["embeddings"]
        except Exception as e:
            self.logger.error(f"Failed to load index: {e}")
