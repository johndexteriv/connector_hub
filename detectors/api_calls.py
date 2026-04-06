import re
from pathlib import Path

from .base import BaseDetector, Detection

SKIP_DIRS = {"node_modules", ".venv", "venv", "__pycache__", ".git", "dist", "build"}
SOURCE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".go", ".rb", ".rs",
                     ".yml", ".yaml", ".json", ".toml", ".env", ".env.example"}

URL_PATTERN = re.compile(r"""['"\s](https?://[\w./:-]+)['"\s]""")


class ApiCallDetector(BaseDetector):
    """Detects hardcoded AI API endpoints in source code and config files."""

    name = "api_call"

    def detect(self) -> list[Detection]:
        results = []
        seen = set()

        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in SOURCE_EXTENSIONS and path.name not in {".env", ".env.example"}:
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue

            try:
                text = path.read_text(errors="ignore")
            except OSError:
                continue

            for m in URL_PATTERN.finditer(text):
                url = m.group(1)
                line_no = text[: m.start()].count("\n") + 1
                for tool_id, matched in self._match_tool(url, "api_call"):
                    k = (tool_id, self._rel(path))
                    if k not in seen:
                        seen.add(k)
                        results.append(Detection(
                            tool_id=tool_id,
                            label=self.catalog[tool_id]["label"],
                            category=self.catalog[tool_id]["category"],
                            signal=f"api url: {url}",
                            signal_type="api_call",
                            file=self._rel(path),
                            line=line_no,
                        ))
        return results
