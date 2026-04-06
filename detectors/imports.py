import re
from pathlib import Path

from .base import BaseDetector, Detection

SOURCE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs", ".rb", ".go", ".rs"}

SKIP_DIRS = {"node_modules", ".venv", "venv", "__pycache__", ".git", "dist", "build", ".next", ".nuxt"}

# Language-specific import patterns
IMPORT_PATTERNS = [
    # Python: import foo, from foo import bar, from foo.bar import baz
    re.compile(r"^\s*(?:import|from)\s+([\w./-]+)", re.MULTILINE),
    # JS/TS: import ... from 'foo', require('foo'), import('foo')
    re.compile(r"""(?:import|require|from)\s+['"](@?[\w./-]+)['"]"""),
    # Ruby: require 'foo'
    re.compile(r"""require\s+['"]([^'"]+)['"]"""),
    # Go: "github.com/foo/bar"
    re.compile(r'"([\w./:-]+)"'),
]


class ImportDetector(BaseDetector):
    name = "import"

    def detect(self) -> list[Detection]:
        results = []
        seen = set()

        for path in self.root.rglob("*"):
            if path.suffix not in SOURCE_EXTENSIONS:
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if not path.is_file():
                continue

            try:
                text = path.read_text(errors="ignore")
            except OSError:
                continue

            for pattern in IMPORT_PATTERNS:
                for m in pattern.finditer(text):
                    imported = m.group(1).strip()
                    # Get approximate line number
                    line_no = text[: m.start()].count("\n") + 1

                    for tool_id, matched in self._match_tool(imported, "import"):
                        key = (tool_id, self._rel(path))
                        if key in seen:
                            continue
                        seen.add(key)
                        results.append(Detection(
                            tool_id=tool_id,
                            label=self.catalog[tool_id]["label"],
                            category=self.catalog[tool_id]["category"],
                            signal=f"import: {imported}",
                            signal_type="import",
                            file=self._rel(path),
                            line=line_no,
                        ))
        return results
