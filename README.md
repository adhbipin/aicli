# 🤖 aicli

**A local terminal AI assistant powered by [Ollama](https://ollama.com) — your own Claude Code / Gemini CLI that runs 100% on your machine.**

No API keys. No internet required. No usage limits. Just you, your terminal, and a local LLM.

---

## ✨ Features

- 📁 **File operations** — read, write, create, delete, move, search files
- 🖥️ **Shell commands** — run any terminal command and see the output
- 🔁 **Agentic loop** — AI chains multiple tool calls automatically to complete complex tasks
- 💬 **Conversation memory** — maintains context across turns in a session
- 📍 **Path-aware** — always works in your current directory, like Claude Code
- 🔌 **100% local** — powered by Ollama, no data leaves your machine
- ⚡ **Installable** — one `pip install` and use `aicli` from any terminal location

---

## 📦 Installation

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/aicli.git
cd aicli
```

### 2. Install

```bash
pip install -e .
```

That's it. `aicli` is now available globally in your terminal.

### 3. Pull an Ollama model

```bash
ollama pull llama3.2          # general purpose (recommended)
ollama pull codellama         # focused on coding
ollama pull qwen2.5-coder     # excellent for code tasks
ollama pull mistral           # fast and capable
```

### 4. Start Ollama (if not already running)

```bash
ollama serve
```

---

## 🚀 Usage

```bash
# From any directory
cd ~/projects/myapp
aicli

# Specify a model
aicli codellama
aicli qwen2.5-coder
```

### Example prompts

```
> list all files here
> create a Flask hello world app in app.py
> read main.py and fix any bugs you find
> run python app.py
> find all TODO comments in .py files
> create a src/ folder and move all Python files into it
> write a README for this project
> add error handling to utils.py
```

---

## ⌨️ Built-in Commands

| Command | Description |
|---|---|
| `/help` | Show help |
| `/models` | List available Ollama models |
| `/model <name>` | Switch to a different model |
| `/clear` | Clear conversation history |
| `/cd <path>` | Change working directory |
| `/pwd` | Print current directory |
| `/exit` | Quit |

---

## 🛠️ Available Tools

The AI can use these tools autonomously to complete your requests:

| Tool | What it does |
|---|---|
| `read_file` | Read a file with line numbers |
| `write_file` | Create or overwrite a file |
| `append_file` | Append text to a file |
| `delete_file` | Delete a file or directory |
| `list_dir` | List directory contents |
| `create_dir` | Create a directory |
| `move_file` | Move or rename a file |
| `run_command` | Execute any shell command |
| `search_in_files` | Search text across files (like grep) |

---

## ⚙️ Configuration

### Environment variables

```bash
# Set default model (add to ~/.bashrc or ~/.zshrc)
export AICLI_MODEL=qwen2.5-coder

# Custom Ollama host (if not running on localhost)
export OLLAMA_HOST=http://localhost:11434
```

### Recommended models by use case

| Use case | Model |
|---|---|
| General tasks | `llama3.2` |
| Coding & debugging | `qwen2.5-coder` or `codellama` |
| Fast responses | `mistral` |
| Large context | `llama3.1:70b` (needs good hardware) |

---

## 🖥️ How it works

```
You type a prompt
      ↓
aicli sends it to Ollama (local LLM)
      ↓
Model decides which tools to call
      ↓
aicli executes tools (read files, run commands, etc.)
      ↓
Results fed back to the model
      ↓
Model reasons further, calls more tools if needed
      ↓
Final answer printed in your terminal
```

The agent loop runs up to 12 tool rounds per request, enabling complex multi-step tasks like: read a file → spot a bug → fix it → run tests → report results.

---

## 📁 Project Structure

```
aicli/
├── aicli/
│   ├── __init__.py
│   └── main.py        ← all source code
├── pyproject.toml     ← package config & entry point
└── README.md
```

---

## 🔧 Development

To modify aicli, just edit `aicli/main.py`. Since it's installed with `-e` (editable mode), changes take effect immediately — no reinstall needed.

```bash
# Uninstall
pip uninstall aicli
```

---

## 🤝 Contributing

Pull requests are welcome! Some ideas for contributions:

- Support for more file types (PDF, DOCX, images via vision models)
- Web search tool integration
- Syntax highlighting in output
- Config file support (`~/.aiclirc`)
- Plugin system for custom tools

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- [Ollama](https://ollama.com) — for making local LLMs incredibly easy to run
- Inspired by [Claude Code](https://claude.ai/code) and [Gemini CLI](https://github.com/google-gemini/gemini-cli)

---

> Built by [Bipin Adhikari](https://github.com/yourusername) · BSc. CSIT, Tribhuvan University
