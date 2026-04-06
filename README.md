# AI Connector Hub

Detect every AI tool, model, and connector your team is using — automatically.

## How it works

The scanner inspects five signal types across your codebase:

| Signal | What it scans | Example |
|--------|--------------|---------|
| 📦 **dependency** | `package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, `Gemfile`, `Cargo.toml` | `openai` in requirements.txt |
| 📥 **import** | Python, JS/TS, Go, Ruby, Rust source files | `from anthropic import Anthropic` |
| 🔑 **env_var** | `.env*` files + `os.environ` / `process.env` usage | `OPENAI_API_KEY=...` |
| ⚙️ **config_file** | Tool-specific config/instruction files | `.cursorrules`, `CLAUDE.md` |
| 🌐 **api_call** | Hardcoded API endpoint URLs in source and config | `api.openai.com` |

## Detected tools (50+)

- **LLM APIs**: OpenAI, Anthropic/Claude, Google Gemini/Vertex, Azure OpenAI, AWS Bedrock, Cohere, Mistral, Groq, Together AI, Replicate, Hugging Face, Perplexity, Ollama
- **Frameworks**: LangChain, LlamaIndex, DSPy, CrewAI, AutoGen, Semantic Kernel, Haystack, Pydantic AI, Instructor
- **Vector DBs**: Pinecone, Weaviate, Chroma, Qdrant, Milvus/Zilliz
- **Dev Tools**: GitHub Copilot, Cursor, Continue.dev, Codeium/Windsurf, Tabnine
- **Observability**: LangSmith, Helicone, Braintrust, Arize/Phoenix, Weights & Biases
- **No-code**: Flowise, n8n

## Usage

### Local (on-demand)

```bash
# Scan current directory — terminal output
python scanner.py

# Scan a specific repo
python scanner.py /path/to/your/repo

# Generate a Markdown report
python scanner.py /path/to/repo --format markdown --output report.md

# Generate JSON (for dashboards or further processing)
python scanner.py /path/to/repo --format json --output scan.json
```

### Git / CI (automatic)

The included GitHub Actions workflow (`.github/workflows/ai-scan.yml`) runs on every push and PR:

- Posts the full report as a **PR comment**
- **Warns when new AI tools appear** vs the committed baseline
- **Auto-updates the baseline** on merge to main
- Uploads the report as a downloadable **artifact** (retained 30 days)

To add it to your own repo, copy the workflow file and point the `python scanner.py` path at where you've placed this tool.

## Why Git + CI is the right home

| Option | Verdict |
|--------|---------|
| **Git / CI** (primary) | Code is the ground truth. Every dep, import, and config file lives here. CI keeps the inventory current on every PR — no manual scans needed. |
| **Local CLI** | Great for dev-time checks before pushing. Zero setup beyond Python 3.11+. |
| **Hosted dashboard** | Useful for multi-repo orgs that want a unified view. Build one by aggregating the JSON output from each repo's CI run into a central store. |

## Adding new tools

Edit `catalog.py`. Each entry follows this shape:

```python
"tool_id": {
    "category": "LLM API",          # LLM API | Framework | Vector DB | Dev Tool | Observability | No-code
    "label": "My Tool",
    "packages": ["my-tool-pkg"],     # pip/npm/gem/cargo package names
    "imports": ["my_tool"],          # import statement fragments
    "env_keys": ["MY_TOOL_API_KEY"], # env var names
    "urls": ["api.mytool.com"],      # API endpoint hostnames/fragments
    "config_files": [".mytool/"],    # config file names or dirs (trailing / = dir)
},
```

## Requirements

Python 3.11+ — no third-party dependencies. The scanner uses only the standard library.
