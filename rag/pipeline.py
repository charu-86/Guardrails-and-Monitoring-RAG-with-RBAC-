"""
RAG Pipeline integrating Retriever, Generator, and Guardrails.
"""
import time
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Any

from .retriever import Retriever
from .generator import Generator
from guardrails.input_validation import InputValidator
from guardrails.output_filtering import OutputFilter
from monitoring.metrics import MetricsCollector
from monitoring.logger import Logger
from monitoring.analytics import Analytics

class RAGPipeline:
    """
    Main RAG pipeline coordinating retrieval, generation, monitoring, and guardrails.
    """
    def __init__(self, config: Optional[Dict] = None, enable_guardrails: bool = True, enable_monitoring: bool = True):
        self.logger = Logger(__name__)
        if config is None:
            config_path = Path("config/config.yaml")
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
            else:
                config = {}
                
        self.retriever = Retriever(config)
        self.generator = Generator(config)
        self.input_validator = InputValidator()
        self.output_filter = OutputFilter()
        self.metrics_collector = MetricsCollector()
        self.analytics = Analytics()
        self.enable_guardrails = enable_guardrails
        self.enable_monitoring = enable_monitoring

    def query(self, user_query: str, user: Any = None) -> Dict:
        """
        Process a user query end-to-end through the RAG pipeline.
        """
        start_time = time.time()
        guardrails_info = {}
        status = "success"
        
        # 1. Input Validation
        sanitized_query = user_query
        if self.enable_guardrails:
            val_result = self.input_validator.validate(user_query)
            guardrails_info["input_warnings"] = getattr(val_result, "warnings", [])
            if not getattr(val_result, "is_valid", True):
                status = "blocked_input"
                return {
                    "response": "Query blocked by input validation.",
                    "query": user_query,
                    "sources": [],
                    "latency": time.time() - start_time,
                    "tokens": {},
                    "guardrails": guardrails_info,
                    "status": status
                }
            sanitized_query = getattr(val_result, "sanitized_query", user_query)
            
        # 2. Retrieval
        retrieved_context = self.retriever.retrieve(sanitized_query, user=user)
        sources = [c["metadata"].get("source", "unknown") for c in retrieved_context]
        
        # 3. Generation
        gen_result = self.generator.generate(sanitized_query, retrieved_context)
        response_text = gen_result["response"]
        
        # 4. Output Filtering
        if self.enable_guardrails:
            filter_result = self.output_filter.filter(response_text)
            guardrails_info["output_warnings"] = getattr(filter_result, "warnings", [])
            if not getattr(filter_result, "is_safe", True):
                status = "blocked_output"
                response_text = "Response blocked by output filter."
            else:
                response_text = getattr(filter_result, "filtered_response", response_text)
                
        latency = time.time() - start_time
        tokens = {
            "prompt_tokens": gen_result.get("prompt_tokens", 0),
            "completion_tokens": gen_result.get("completion_tokens", 0)
        }
        
        # 5. Monitoring
        if self.enable_monitoring:
            self.metrics_collector.record_latency(latency)
            p_toks = tokens["prompt_tokens"]
            c_toks = tokens["completion_tokens"]
            self.metrics_collector.record_tokens(p_toks, c_toks)
            
            user_str = user.username if hasattr(user, "username") else (str(user) if user else "anonymous")
            triggered = []
            if guardrails_info.get("input_warnings"):
                triggered.extend(guardrails_info["input_warnings"])
            if guardrails_info.get("output_warnings"):
                triggered.extend(guardrails_info["output_warnings"])
                
            self.analytics.record_query(
                query=user_query,
                response=response_text,
                user=user_str,
                latency=latency,
                tokens_used={"prompt": p_toks, "completion": c_toks},
                guardrails_triggered=triggered
            )
            
        return {
            "response": response_text,
            "query": user_query,
            "sources": sources,
            "latency": latency,
            "tokens": tokens,
            "guardrails": guardrails_info,
            "status": status
        }

    def ingest(self, file_paths: List[str], user: Any = None, access_level: str = 'public') -> Dict:
        """
        Ingest new documents into the knowledge base, with basic permission checks.
        """
        if user is not None:
            user_roles = getattr(user, "roles", [])
            if "admin" not in user_roles:
                return {"status": "permission_denied", "chunks_ingested": 0, "files_processed": 0}
                
        chunks = self.retriever.ingest(file_paths, access_level=access_level)
        self.logger.info(f"Ingested {len(file_paths)} files, {chunks} chunks total.")
        return {
            "status": "success",
            "chunks_ingested": chunks,
            "files_processed": len(file_paths)
        }
        
    def get_analytics(self) -> Dict:
        """
        Retrieve monitoring and analytics data.
        """
        return self.analytics.get_summary()
