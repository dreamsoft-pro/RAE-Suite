"""
RAE-Suite Ingestion Stage PII Scrubber
Scrubs sensitive information (passwords, JWTs, API keys, emails, credit cards)
BEFORE vectorization and storage in Qdrant/pgvector to comply with ISO 27001 & ISO 42001.
"""

import re
import logging
from typing import Dict, Any, Union

logger = logging.getLogger(__name__)


class IngestionPIIScrubber:
    """
    Scrubs sensitive PII and secrets prior to memory persistence and vector embeddings.
    """
    # Regex patterns for common secrets and PII
    PATTERNS = [
        (re.compile(r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*'), '[REDACTED_JWT_TOKEN]'),
        (re.compile(r'(?i)(api[_-]?key|secret|password|passwd|auth[_-]?token)\s*[:=]\s*["\']?[A-Za-z0-9-_+/=]{8,}["\']?'), r'\1: [REDACTED_SECRET]'),
        (re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'), '[REDACTED_EMAIL]'),
        (re.compile(r'\b(?:\d[ -]*?){13,16}\b'), '[REDACTED_CREDIT_CARD]'),
        (re.compile(r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC )?PRIVATE KEY-----'), '[REDACTED_PRIVATE_KEY]')
    ]

    @classmethod
    def scrub_text(cls, text: str) -> str:
        if not isinstance(text, str):
            return text

        scrubbed = text
        for pattern, replacement in cls.PATTERNS:
            scrubbed = pattern.sub(replacement, scrubbed)

        return scrubbed

    @classmethod
    def scrub_payload(cls, payload: Union[Dict[str, Any], list, str]) -> Union[Dict[str, Any], list, str]:
        if isinstance(payload, str):
            return cls.scrub_text(payload)
        elif isinstance(payload, dict):
            return {k: cls.scrub_payload(v) for k, v in payload.items()}
        elif isinstance(payload, list):
            return [cls.scrub_payload(item) for item in payload]
        return payload
