from pathlib import Path

from .base import BaseDetector, Detection


class ConfigDetector(BaseDetector):
    """Detects AI tools by the presence of their config/instruction files."""

    name = "config_file"

    def detect(self) -> list[Detection]:
        results = []
        seen = set()

        for tool_id, tool in self.catalog.items():
            for config_pattern in tool.get("config_files", []):
                # Patterns ending with "/" are directories
                if config_pattern.endswith("/"):
                    dir_name = config_pattern.rstrip("/")
                    for path in self.root.rglob(dir_name):
                        if path.is_dir() and tool_id not in seen:
                            seen.add(tool_id)
                            results.append(Detection(
                                tool_id=tool_id,
                                label=tool["label"],
                                category=tool["category"],
                                signal=f"config dir: {config_pattern}",
                                signal_type="config_file",
                                file=self._rel(path),
                            ))
                else:
                    for path in self.root.rglob(config_pattern):
                        if path.is_file() and tool_id not in seen:
                            seen.add(tool_id)
                            results.append(Detection(
                                tool_id=tool_id,
                                label=tool["label"],
                                category=tool["category"],
                                signal=f"config file: {config_pattern}",
                                signal_type="config_file",
                                file=self._rel(path),
                            ))
        return results
