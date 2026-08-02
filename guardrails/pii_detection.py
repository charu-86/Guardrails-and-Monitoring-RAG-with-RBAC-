"""
PII (Personally Identifiable Information) detection and redaction module.
"""
import re
from typing import List, Dict, Optional
import yaml
from pathlib import Path

class PIIDetector:
    """
    Detects and optionally redact PII from text.
    """
    def __init__(self, config: Optional[dict] = None):
        """Initialize the PII detector with configuration."""
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
        self.redaction_placeholder = guardrails_cfg.get("redaction_placeholder", "[REDACTED]")
        self.enabled_pii_types = guardrails_cfg.get("pii_patterns", ["email", "phone", "ssn", "credit_card", "ip_address"])

        self.PII_PATTERNS = {
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": re.compile(r'(?:\+1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "credit_card": re.compile(r'\b(?:\d[ -]*?){13,19}\b'),
            "ip_address": re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')
        }

    def detect(self, text: str) -> List[Dict]:
        """
        Detect PII in the given text.

        Args:
            text (str): The text to check.

        Returns:
            List[Dict]: A list of detected PII entities.
        """
        results = []
        for pii_type, pattern in self.PII_PATTERNS.items():
            if pii_type not in self.enabled_pii_types:
                continue
            for match in pattern.finditer(text):
                # Basic validation for credit card since regex can match arbitrary digits
                if pii_type == "credit_card":
                    clean_cc = re.sub(r'[-\s]', '', match.group(0))
                    if len(clean_cc) < 13 or len(clean_cc) > 19:
                        continue
                results.append({
                    "type": pii_type,
                    "value": match.group(0),
                    "start": match.start(),
                    "end": match.end()
                })
        return results

    def redact(self, text: str, pii_types: Optional[List[str]] = None) -> str:
        """
        Redact detected PII from text.

        Args:
            text (str): The input text.
            pii_types (List[str], optional): specific PII types to redact. If None, redacts all enabled types.

        Returns:
            str: The redacted text.
        """
        redacted_text = text
        detections = self.detect(text)
        
        offset = 0
        sorted_detections = sorted(detections, key=lambda x: x["start"])
        for det in sorted_detections:
            if pii_types and det["type"] not in pii_types:
                continue
            start = det["start"] + offset
            end = det["end"] + offset
            redacted_text = redacted_text[:start] + self.redaction_placeholder + redacted_text[end:]
            offset += len(self.redaction_placeholder) - (end - start)
            
        return redacted_text

    def contains_pii(self, text: str) -> bool:
        """
        Quick check if text contains any PII.
        
        Args:
            text (str): Text to check.
            
        Returns:
            bool: True if PII is found, False otherwise.
        """
        return len(self.detect(text)) > 0

    def get_detection_summary(self, text: str) -> Dict:
        """
        Get a summary of PII detections.
        
        Args:
            text (str): The input text.
            
        Returns:
            Dict: Summary dictionary.
        """
        detections = self.detect(text)
        by_type = {}
        for det in detections:
            by_type[det["type"]] = by_type.get(det["type"], 0) + 1
            
        return {
            "has_pii": len(detections) > 0,
            "total_findings": len(detections),
            "by_type": by_type
        }
