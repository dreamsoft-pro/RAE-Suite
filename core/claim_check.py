"""
RAE-Suite Claim Check & ArtifactRef Manager
Offloads large message payloads (prompts, logs, patches, diffs > 16 KiB) to Artifact Store
and transmits lightweight ArtifactRef references with SHA-256 integrity hashes.
"""

import os
import hashlib
import threading
from enum import Enum
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class RedactionStatus(str, Enum):
    NOT_SCANNED = "NOT_SCANNED"
    SCANNED_SAFE = "SCANNED_SAFE"
    REDACTED = "REDACTED"


class ArtifactRef(BaseModel):
    kind: str = "artifact-ref"
    artifact_id: str = Field(..., description="Unique artifact UUID")
    uri: str = Field(..., description="URI location of stored artifact payload")
    content_hash: str = Field(..., description="SHA-256 hash of payload content")
    size_bytes: int = Field(..., ge=0, description="Size in bytes")
    media_type: str = Field("text/plain", description="MIME content type")
    redaction_status: RedactionStatus = Field(RedactionStatus.SCANNED_SAFE)
    retention_policy: str = Field("90_DAYS", description="Artifact retention policy label")


class ClaimCheckManager:
    """
    Manages payload offloading for large messages (> 16 KiB or complex blobs).
    Guarantees thread-safe atomic artifact storage.
    """
    def __init__(self, artifact_dir: Optional[str] = None):
        self.artifact_dir = artifact_dir or "/tmp/rae_artifacts"
        self._lock = threading.Lock()
        os.makedirs(self.artifact_dir, exist_ok=True)

    def offload_if_needed(self, payload: str, artifact_id: str, media_type: str = "text/plain", threshold_bytes: int = 16384) -> tuple[bool, Union[str, ArtifactRef]]:
        """
        If payload size exceeds threshold_bytes (default 16 KiB), offloads to artifact store
        and returns (True, ArtifactRef). Otherwise returns (False, raw_payload).
        """
        payload_bytes = payload.encode("utf-8")
        content_hash = hashlib.sha256(payload_bytes).hexdigest()
        size = len(payload_bytes)

        if size > threshold_bytes:
            file_path = os.path.join(self.artifact_dir, f"{artifact_id}.bin")
            with self._lock:
                if not os.path.exists(file_path):
                    temp_path = f"{file_path}.tmp"
                    with open(temp_path, "wb") as f:
                        f.write(payload_bytes)
                    os.replace(temp_path, file_path)

            ref = ArtifactRef(
                artifact_id=artifact_id,
                uri=f"file://{file_path}",
                content_hash=content_hash,
                size_bytes=size,
                media_type=media_type,
                redaction_status=RedactionStatus.SCANNED_SAFE,
            )
            return True, ref

        return False, payload

    def retrieve(self, ref: ArtifactRef) -> str:
        """Retrieves and verifies artifact content against stored SHA-256 content_hash."""
        file_path = ref.uri.replace("file://", "")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Artifact file not found at {file_path}")

        with open(file_path, "rb") as f:
            data = f.read()

        computed_hash = hashlib.sha256(data).hexdigest()
        if computed_hash != ref.content_hash:
            raise ValueError(f"Artifact integrity failure: computed {computed_hash} != stored {ref.content_hash}")

        return data.decode("utf-8")
