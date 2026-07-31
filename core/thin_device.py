"""
RAE-Suite Thin Device Runtime Profile
Optimizes memory usage, thread pools, and local storage footprint
for low-power, mobile, Windows laptop, and thin client devices.
"""

import os
import psutil
import logging
from typing import Dict, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DeviceResourceLimits(BaseModel):
    max_ram_mb: int = 512
    max_worker_threads: int = 2
    local_vector_backend: str = "sqlite"
    enable_gpu: bool = False


class ThinDeviceRuntime:
    """
    Lightweight Execution Profile Manager for RAE Mesh node adaptation.
    """
    def __init__(self, mode: str = "auto"):
        self.mode = mode
        self.profile = self.detect_hardware_profile()

    def detect_hardware_profile(self) -> DeviceResourceLimits:
        total_ram_mb = int(psutil.virtual_memory().total / (1024 * 1024))
        cpu_cores = psutil.cpu_count() or 1

        if total_ram_mb < 2048:
            logger.info("ThinDeviceRuntime: Low RAM detected (<2GB). Activating THIN_MOBILE profile.")
            return DeviceResourceLimits(
                max_ram_mb=256,
                max_worker_threads=1,
                local_vector_backend="sqlite_light",
                enable_gpu=False
            )
        elif total_ram_mb < 8192:
            logger.info("ThinDeviceRuntime: Standard RAM detected (<8GB). Activating THIN_LAPTOP profile.")
            return DeviceResourceLimits(
                max_ram_mb=1024,
                max_worker_threads=2,
                local_vector_backend="sqlite",
                enable_gpu=False
            )
        else:
            logger.info("ThinDeviceRuntime: High RAM detected. Activating MESH_NODE profile.")
            return DeviceResourceLimits(
                max_ram_mb=4096,
                max_worker_threads=cpu_cores,
                local_vector_backend="qdrant_postgres",
                enable_gpu=True
            )
