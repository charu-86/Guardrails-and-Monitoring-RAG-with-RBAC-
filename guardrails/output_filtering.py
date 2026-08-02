"""
Output filtering guardrails module.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import yaml
from pathlib import Path
import tiktoken
import re

from guardrails.pii_detection import PIIDetector
from monitoring.logger import Logger


@dataclass
class FilterResult:
    """Result of output filtering."""
    is_safe: bool
    filtered_response: str
    warnings: List[str] = field(default_factory=list)
    blocked: bool = False
    block_reason: Optional[str] = None
    modifications: List[str] = field(default_factory=list)


TOXIC_KEYWORDS = [
    "hate", "kill", "stupid", "idiot", "dumb", "ugly", "loser",
    "moron", "trash", "scum", "bastard", "bitch", "crap",
    "die", "murder", "terror", "bomb", "attack", "violence"
]


class OutputFilter:
    """Filters and validates LLM outputs."""
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize the output filter with configuration."""
        if config is None:
            config_path = Path(__file__).resolve().parent.parent / "config" / "config.yaml"
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config = yaml.safe_load(f) or {}
            else:
                self.config = {}
        else:
            self.config = config
            
        guardrails_cfg = self.config.get("guardrails", {})
        
        self.pii_detector = PIIDetector(config=self.config)
        self.logger = Logger("OutputFilter")
        
        self.max_output_token_limit = guardrails_cfg.get("max_output_token_limit", 4000)
        self.toxicity_threshold = guardrails_cfg.get("toxicity_threshold", 0.7)
        self.enable_output_filtering = guardrails_cfg.get("enable_output_filtering", True)
        self.enable_pii_detection = guardrails_cfg.get("enable_pii_detection", True)
        
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            self.logger.error(f"Failed to load tokenizer: {e}")
            self.tokenizer = None

    def _check_toxicity(self, response: str) -> Tuple[bool, float, List[str]]:
        """Check for toxic keywords in response."""
        words = re.findall(r'\b\w+\b', response.lower())
        if not words:
            return False, 0.0, []
            
        matched_words = []
        for word in words:
            if word in TOXIC_KEYWORDS:
                matched_words.append(word)
                
        score = len(matched_words) / max(len(words), 1)
        is_toxic = score > self.toxicity_threshold
        
        return is_toxic, score, matched_words

    def _check_response_length(self, response: str) -> Tuple[bool, int]:
        """Check if response exceeds token limits."""
        if not self.tokenizer:
            token_count = len(response.split()) * 1.3
            return token_count > self.max_output_token_limit, int(token_count)
            
        tokens = self.tokenizer.encode(response)
        return len(tokens) > self.max_output_token_limit, len(tokens)

    def _check_factual_grounding(self, response: str, context: str) -> Tuple[bool, float]:
        """Check if response is factually grounded in the provided context."""
        if not context or not context.strip():
            return True, 1.0  # Cannot verify without context
            
        context_words = set(re.findall(r'\b\w{4,}\b', context.lower()))
        if not context_words:
            return True, 1.0
            
        # Split response into simple sentences
        sentences = re.split(r'(?<=[.!?]) +', response)
        sentences = [s for s in sentences if s.strip()]
        if not sentences:
            return True, 1.0
            
        grounded_sentences = 0
        for sentence in sentences:
            sentence_words = set(re.findall(r'\b\w{4,}\b', sentence.lower()))
            if not sentence_words:
                grounded_sentences += 1
                continue
                
            # If at least one significant word from the context appears in the sentence
            if sentence_words.intersection(context_words):
                grounded_sentences += 1
                
        grounding_score = grounded_sentences / len(sentences)
        is_grounded = grounding_score > 0.3
        
        return is_grounded, grounding_score

    def _generate_safe_fallback(self) -> str:
        """Generate a standard safe response fallback."""
        return "I apologize, but I cannot provide a response to that request."

    def filter(self, response: str, context: Optional[str] = None) -> FilterResult:
        """
        Filter and validate the model response.
        
        Args:
            response (str): The generated response.
            context (str, optional): The context used to generate the response.
            
        Returns:
            FilterResult: The filtering result.
        """
        if not self.enable_output_filtering:
            return FilterResult(is_safe=True, filtered_response=response)
            
        warnings = []
        modifications = []
        filtered = response
        
        if not filtered or not filtered.strip():
            return FilterResult(
                is_safe=False,
                filtered_response=self._generate_safe_fallback(),
                blocked=True,
                block_reason="Response is empty."
            )
            
        is_toxic, score, toxic_words = self._check_toxicity(filtered)
        if is_toxic:
            self.logger.warning(f"Toxic response detected. Score: {score}")
            return FilterResult(
                is_safe=False,
                filtered_response=self._generate_safe_fallback(),
                blocked=True,
                block_reason="Response violates safety guidelines."
            )
            
        exceeds_limit, token_count = self._check_response_length(filtered)
        if exceeds_limit:
            self.logger.warning(f"Response exceeds token limit: {token_count} > {self.max_output_token_limit}")
            return FilterResult(
                is_safe=False,
                filtered_response=self._generate_safe_fallback(),
                blocked=True,
                block_reason="Response exceeds length limits."
            )
            
        if context:
            is_grounded, grounding_score = self._check_factual_grounding(filtered, context)
            if not is_grounded:
                self.logger.warning(f"Response may hallucinate. Grounding score: {grounding_score}")
                warnings.append(f"Low factual grounding score: {grounding_score:.2f}")
                
        if self.enable_pii_detection:
            summary = self.pii_detector.get_detection_summary(filtered)
            if summary["has_pii"]:
                filtered = self.pii_detector.redact(filtered)
                modifications.append("Redacted PII from response")
                warnings.append(f"PII detected and redacted: {summary['by_type']}")
                
        return FilterResult(
            is_safe=True,
            filtered_response=filtered,
            warnings=warnings,
            blocked=False,
            modifications=modifications
        )
