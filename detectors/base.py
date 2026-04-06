from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Detection:
    tool_id: str
    label: str
    category: str
    signal: str        # what triggered the detection (e.g. "package: openai")
    signal_type: str   # "dependency" | "import" | "env_var" | "config_file" | "api_call"
    file: str          # relative file path where found
    line: int = 0      # line number (0 = file-level)


class BaseDetector:
    name: str = ""

    def __init__(self, root: Path, catalog: dict):
        self.root = root
        self.catalog = catalog

    def detect(self) -> list[Detection]:
        raise NotImplementedError

    def _rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    def _match_tool(self, value: str, signal_type: str) -> list[tuple[str, str]]:
        """Return [(tool_id, matched_value)] for all catalog entries matching value."""
        matches = []
        key = {
            "dependency": "packages",
            "import": "imports",
            "env_var": "env_keys",
            "api_call": "urls",
        }.get(signal_type, "")
        if not key:
            return matches
        value_lower = value.lower()
        for tool_id, tool in self.catalog.items():
            for pattern in tool.get(key, []):
                if pattern.lower() in value_lower or value_lower in pattern.lower():
                    matches.append((tool_id, pattern))
                    break
        return matches
