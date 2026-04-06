import re
from pathlib import Path

from .base import BaseDetector, Detection

SKIP_DIRS = {"node_modules", ".venv", "venv", "__pycache__", ".git", "dist", "build"}

# Files that declare env vars
ENV_FILE_PATTERNS = [".env", ".env.local", ".env.example", ".env.sample",
                     ".env.development", ".env.production", ".env.test"]

# Source code patterns that reference env vars
ENV_USAGE_PATTERNS = [
    re.compile(r"""os\.(?:environ\.get|getenv|environ)\s*\[\s*['"]([\w_]+)['"]"""),
    re.compile(r"""os\.(?:environ\.get|getenv)\s*\(\s*['"]([\w_]+)['"]"""),
    re.compile(r"""process\.env\.([\w_]+)"""),
    re.compile(r"""ENV\[['"]([\w_]+)['"]\]"""),        # Ruby
    re.compile(r"""(?:std::)?env::var\s*\(\s*"([\w_]+)"\s*\)"""),  # Rust
]

SOURCE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".rb", ".go", ".rs", ".yml", ".yaml"}


class EnvVarDetector(BaseDetector):
    name = "env_var"

    def detect(self) -> list[Detection]:
        results = []
        seen = set()

        # 1. Scan .env* files for key declarations
        for path in self.root.rglob("*"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.name in ENV_FILE_PATTERNS or path.name.startswith(".env"):
                results += self._scan_env_file(path, seen)

        # 2. Scan source files for env var usage
        for path in self.root.rglob("*"):
            if path.suffix not in SOURCE_EXTENSIONS:
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if not path.is_file():
                continue
            results += self._scan_source_file(path, seen)

        return results

    def _scan_env_file(self, path: Path, seen: set) -> list[Detection]:
        results = []
        try:
            for i, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key = line.split("=")[0].strip()
                for tool_id, matched in self._match_tool(key, "env_var"):
                    k = (tool_id, self._rel(path))
                    if k not in seen:
                        seen.add(k)
                        results.append(Detection(
                            tool_id=tool_id,
                            label=self.catalog[tool_id]["label"],
                            category=self.catalog[tool_id]["category"],
                            signal=f"env var: {key}",
                            signal_type="env_var",
                            file=self._rel(path),
                            line=i,
                        ))
        except OSError:
            pass
        return results

    def _scan_source_file(self, path: Path, seen: set) -> list[Detection]:
        results = []
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            return results

        for pattern in ENV_USAGE_PATTERNS:
            for m in pattern.finditer(text):
                key = m.group(1)
                line_no = text[: m.start()].count("\n") + 1
                for tool_id, matched in self._match_tool(key, "env_var"):
                    k = (tool_id, self._rel(path))
                    if k not in seen:
                        seen.add(k)
                        results.append(Detection(
                            tool_id=tool_id,
                            label=self.catalog[tool_id]["label"],
                            category=self.catalog[tool_id]["category"],
                            signal=f"env var: {key}",
                            signal_type="env_var",
                            file=self._rel(path),
                            line=line_no,
                        ))
        return results
