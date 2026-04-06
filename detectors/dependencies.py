import json
import re
from pathlib import Path

from .base import BaseDetector, Detection

# Maps filename → parser function name
DEPENDENCY_FILES = {
    "requirements.txt": "parse_requirements",
    "requirements-dev.txt": "parse_requirements",
    "requirements-test.txt": "parse_requirements",
    "pyproject.toml": "parse_pyproject",
    "setup.cfg": "parse_setup_cfg",
    "Pipfile": "parse_pipfile",
    "package.json": "parse_package_json",
    "Gemfile": "parse_gemfile",
    "go.mod": "parse_go_mod",
    "Cargo.toml": "parse_cargo_toml",
}


class DependencyDetector(BaseDetector):
    name = "dependency"

    def detect(self) -> list[Detection]:
        results = []
        for filename, parser_name in DEPENDENCY_FILES.items():
            for path in self.root.rglob(filename):
                if self._skip(path):
                    continue
                parser = getattr(self, parser_name)
                packages = parser(path)
                for pkg in packages:
                    for tool_id, matched in self._match_tool(pkg, "dependency"):
                        results.append(Detection(
                            tool_id=tool_id,
                            label=self.catalog[tool_id]["label"],
                            category=self.catalog[tool_id]["category"],
                            signal=f"package: {pkg}",
                            signal_type="dependency",
                            file=self._rel(path),
                        ))
        return results

    def _skip(self, path: Path) -> bool:
        skip_dirs = {"node_modules", ".venv", "venv", "__pycache__", ".git", "dist", "build"}
        return any(part in skip_dirs for part in path.parts)

    def parse_requirements(self, path: Path) -> list[str]:
        packages = []
        for line in path.read_text(errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            # Strip version specifiers: openai>=1.0.0 → openai
            pkg = re.split(r"[>=<!;\[@ ]", line)[0].strip()
            if pkg:
                packages.append(pkg.lower())
        return packages

    def parse_pyproject(self, path: Path) -> list[str]:
        packages = []
        text = path.read_text(errors="ignore")
        # Match lines in [project.dependencies] or [tool.poetry.dependencies]
        for line in text.splitlines():
            line = line.strip().strip('"').strip("'")
            if not line or line.startswith("[") or line.startswith("#"):
                continue
            pkg = re.split(r"[>=<!;\[@ ]", line)[0].strip().strip('"').strip("'")
            if pkg and not pkg.startswith("python"):
                packages.append(pkg.lower())
        return packages

    def parse_setup_cfg(self, path: Path) -> list[str]:
        return self.parse_requirements(path)  # similar line format

    def parse_pipfile(self, path: Path) -> list[str]:
        packages = []
        text = path.read_text(errors="ignore")
        in_packages = False
        for line in text.splitlines():
            if line.strip().startswith("[packages]") or line.strip().startswith("[dev-packages]"):
                in_packages = True
                continue
            if line.strip().startswith("[") and in_packages:
                in_packages = False
            if in_packages:
                pkg = line.split("=")[0].strip().strip('"').strip("'")
                if pkg:
                    packages.append(pkg.lower())
        return packages

    def parse_package_json(self, path: Path) -> list[str]:
        try:
            data = json.loads(path.read_text(errors="ignore"))
        except json.JSONDecodeError:
            return []
        packages = []
        for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            packages.extend(data.get(section, {}).keys())
        return [p.lower() for p in packages]

    def parse_gemfile(self, path: Path) -> list[str]:
        packages = []
        for line in path.read_text(errors="ignore").splitlines():
            m = re.match(r"gem\s+['\"]([^'\"]+)['\"]", line.strip())
            if m:
                packages.append(m.group(1).lower())
        return packages

    def parse_go_mod(self, path: Path) -> list[str]:
        packages = []
        for line in path.read_text(errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("module") and not line.startswith("go ") and not line.startswith("//"):
                pkg = line.split()[0]
                packages.append(pkg.lower())
        return packages

    def parse_cargo_toml(self, path: Path) -> list[str]:
        packages = []
        text = path.read_text(errors="ignore")
        in_deps = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped in ("[dependencies]", "[dev-dependencies]", "[build-dependencies]"):
                in_deps = True
                continue
            if stripped.startswith("[") and in_deps:
                in_deps = False
            if in_deps and "=" in stripped and not stripped.startswith("#"):
                pkg = stripped.split("=")[0].strip()
                packages.append(pkg.lower())
        return packages
