"""Shared model lifecycle management utilities."""

from __future__ import annotations

from typing import Any

import torch


class ModelManager:
    """Track loaded model objects and expose GPU/cache health helpers.

    Args:
        None: Manager starts with an empty registry.

    Returns:
        None: Instance stores mutable model registry state.
    """

    def __init__(self) -> None:
        """Initialise model registry.

        Args:
            None: No constructor parameters.

        Returns:
            None: Creates an empty dictionary for loaded models.
        """
        self._models: dict[str, Any] = {}

    def register_model(self, name: str, model: Any) -> None:
        """Register a loaded model object under a unique name.

        Args:
            name (str): Registry key for the model.
            model (Any): Loaded model or pipeline object.

        Returns:
            None: Updates internal model registry.
        """
        self._models[name] = model

    def get_model(self, name: str) -> Any | None:
        """Return a model object by name when present.

        Args:
            name (str): Registry key for the model.

        Returns:
            Any | None: Registered model object or None.
        """
        return self._models.get(name)

    def clear_cache(self) -> None:
        """Clear torch CUDA cache when GPU is available.

        Args:
            None: No parameters.

        Returns:
            None: Invokes CUDA cache clear side effects.
        """
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def check_gpu(self) -> dict[str, str | int]:
        """Return GPU name and VRAM usage metrics.

        Args:
            None: No parameters.

        Returns:
            dict[str, str | int]: gpu_name, vram_used_bytes, vram_total_bytes.
        """
        if not torch.cuda.is_available():
            return {
                "gpu_name": "cpu-mock",
                "vram_used_bytes": 0,
                "vram_total_bytes": 0,
            }

        device_index = torch.cuda.current_device()
        props = torch.cuda.get_device_properties(device_index)
        return {
            "gpu_name": props.name,
            "vram_used_bytes": int(torch.cuda.memory_allocated(device_index)),
            "vram_total_bytes": int(props.total_memory),
        }
