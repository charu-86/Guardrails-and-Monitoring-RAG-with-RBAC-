"""
Generator component for RAG pipeline.
"""
import os
import yaml
from pathlib import Path
from typing import List, Dict, Optional

try:
    import openai
except ImportError:
    openai = None

try:
    import tiktoken
except ImportError:
    tiktoken = None

from monitoring.logger import Logger

class Generator:
    """
    LLM Generation component for the RAG pipeline.
    """
    def __init__(self, config: Optional[Dict] = None):
        self.logger = Logger(__name__)
        if config is None:
            config_path = Path("config/config.yaml")
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
            else:
                config = {}
                
        rag_config = config.get("rag", {})
        self.model = rag_config.get("model", "gpt-3.5-turbo")
        self.temperature = rag_config.get("temperature", 0.7)
        self.max_tokens = rag_config.get("max_tokens", 1024)
        self.prompt_template = rag_config.get("prompt_template", "Context:\n{context}\n\nQuestion:\n{question}\n\nAnswer:")

    def generate(self, query: str, context: Optional[List[Dict]] = None) -> Dict:
        """
        Generate a response based on the query and retrieved context.
        """
        prompt = self._build_prompt(query, context)
        response_data = self._call_llm(prompt)
        response_data["model"] = self.model
        return response_data

    def _build_prompt(self, query: str, context: Optional[List[Dict]] = None) -> str:
        ctx_str = ""
        if context:
            ctx_str = "\n".join([c.get("content", "") for c in context])
        return self.prompt_template.format(context=ctx_str, question=query)

    def _call_llm(self, prompt: str) -> Dict:
        if openai is not None and os.getenv("OPENAI_API_KEY"):
            try:
                client = openai.OpenAI()
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                content = response.choices[0].message.content
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                return {
                    "response": content,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens
                }
            except Exception as e:
                self.logger.error(f"OpenAI call failed: {e}")
                
        # Mock fallback
        mock_response = f"Based on the provided context: [mock response for {prompt[:30]}...]"
        prompt_tokens = self._count_tokens(prompt)
        completion_tokens = self._count_tokens(mock_response)
        
        return {
            "response": mock_response,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens
        }

    def _count_tokens(self, text: str) -> int:
        if tiktoken is not None:
            try:
                enc = tiktoken.get_encoding("cl100k_base")
                return len(enc.encode(text))
            except Exception:
                pass
        return len(text.split())

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        # Cost estimate based on generic gpt-3.5-turbo rates
        return (prompt_tokens * 0.0015 / 1000) + (completion_tokens * 0.002 / 1000)
