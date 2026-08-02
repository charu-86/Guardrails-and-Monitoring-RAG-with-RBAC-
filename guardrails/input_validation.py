"""
Input validation guardrails module.
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
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    sanitized_query: str
    warnings: List[str] = field(default_factory=list)
    blocked: bool = False
    block_reason: Optional[str] = None


class InputValidator:
    """Validates and sanitizes user input."""
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize the validator with configuration."""
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
        self.logger = Logger("InputValidator")
        
        self.max_input_token_limit = guardrails_cfg.get("max_input_token_limit", 2000)
        self.blocked_phrases = guardrails_cfg.get("blocked_phrases", [
            "ignore previous instructions",
            "forget everything",
            "system prompt",
            "you are a developer",
            "bypass safety"
        ])
        
        self.enable_prompt_injection = guardrails_cfg.get("enable_prompt_injection_detection", True)
        self.enable_pii_detection = guardrails_cfg.get("enable_pii_detection", True)
        
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            self.logger.error(f"Failed to load tokenizer: {e}")
            self.tokenizer = None

    def _check_prompt_injection(self, query: str) -> Tuple[bool, Optional[str]]:
        """Check for prompt injection phrases."""
        query_lower = query.lower()
        for phrase in self.blocked_phrases:
            if phrase.lower() in query_lower:
                return True, phrase
        return False, None

    def _check_token_limit(self, query: str) -> Tuple[bool, int]:
        """Check if query exceeds token limits."""
        if not self.tokenizer:
            # Fallback heuristic if tokenizer fails to load
            token_count = len(query.split()) * 1.3
            return token_count > self.max_input_token_limit, int(token_count)
            
        tokens = self.tokenizer.encode(query)
        return len(tokens) > self.max_input_token_limit, len(tokens)

    def _sanitize_input(self, query: str) -> str:
        """Sanitize input string by removing control characters and excessive whitespace."""
        # Strip control characters except newline and tab
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', query)
        # Collapse excessive whitespace
        sanitized = re.sub(r' {2,}', ' ', sanitized)
        return sanitized.strip()

    def _check_pii(self, query: str) -> Tuple[bool, str, Dict]:
        """Check and redact PII from query."""
        summary = self.pii_detector.get_detection_summary(query)
        if summary["has_pii"]:
            redacted = self.pii_detector.redact(query)
            return True, redacted, summary
        return False, query, summary

    def validate(self, query: str) -> ValidationResult:
        """
        Validate the user query.
        
        Args:
            query (str): The user query.
            
        Returns:
            ValidationResult: The result of the validation.
        """
        warnings = []
        
        if not query or not query.strip():
            return ValidationResult(
                is_valid=False,
                sanitized_query="",
                blocked=True,
                block_reason="Query is empty."
            )
            
        sanitized = self._sanitize_input(query)
        
        if self.enable_prompt_injection:
            is_injection, matched_phrase = self._check_prompt_injection(sanitized)
            if is_injection:
                self.logger.warning(f"Prompt injection detected: {matched_phrase}")
                return ValidationResult(
                    is_valid=False,
                    sanitized_query=sanitized,
                    blocked=True,
                    block_reason=f"Potential prompt injection detected."
                )
                
        exceeds_limit, token_count = self._check_token_limit(sanitized)
        if exceeds_limit:
            self.logger.warning(f"Query exceeds token limit: {token_count} > {self.max_input_token_limit}")
            return ValidationResult(
                is_valid=False,
                sanitized_query=sanitized,
                blocked=True,
                block_reason=f"Query exceeds maximum length of {self.max_input_token_limit} tokens."
            )
            
        if self.enable_pii_detection:
            has_pii, sanitized, pii_summary = self._check_pii(sanitized)
            if has_pii:
                warnings.append(f"PII detected and redacted: {pii_summary['by_type']}")
                self.logger.info(f"PII redacted from query: {pii_summary['by_type']}")
                
        return ValidationResult(
            is_valid=True,
            sanitized_query=sanitized,
            warnings=warnings,
            blocked=False
        )
