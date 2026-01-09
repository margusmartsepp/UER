# Contributing to UER

## Development Setup

### Prerequisites
- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Initial Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd UER
```

2. Install dependencies with uv:
```bash
# Install all dependencies including dev tools
uv sync --all-extras

# Or just production dependencies
uv sync
```

3. Install pre-commit hooks:
```bash
uv run pre-commit install
```

### Development Workflow

#### Running Code Quality Checks

**Format code with Black:**
```bash
uv run black .
```

**Lint with Ruff:**
```bash
uv run ruff check . --fix
```

**Type check with mypy:**
```bash
uv run mypy src/
```

**Run all pre-commit hooks manually:**
```bash
uv run pre-commit run --all-files
```

#### Running Tests

```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/test_example.py

# Run with verbose output
uv run pytest -v
```

#### Adding Dependencies

```bash
# Production dependency
uv add package-name

# Development dependency
uv add --dev package-name
```

### Code Quality Standards

This project follows strict code quality standards:

- **Line length:** 100 characters
- **Type hints:** Required for all functions/methods
- **Docstrings:** Required for public APIs (Google style)
- **Test coverage:** Aim for >80%

### Pre-commit Hooks

The following checks run automatically on every commit:

- ✅ **Black** - Code formatting
- ✅ **Ruff** - Linting and import sorting
- ✅ **Mypy** - Static type checking
- ✅ **Trailing whitespace** - Removed automatically
- ✅ **End of file fixer** - Ensures files end with newline
- ✅ **YAML/JSON/TOML** - Syntax validation
- ✅ **Large files** - Prevents commits >1MB

### Project Structure

```
UER/
├── src/uer/              # Main package source code
├── context/
│   ├── datasets/         # Downloaded datasets (gitignored)
│   ├── papers/           # Research papers (gitignored)
│   └── scripts/          # Test and utility scripts
├── tests/                # Test files (mirror src/ structure)
├── pyproject.toml        # Project configuration
├── .pre-commit-config.yaml  # Pre-commit hooks config
└── seed_datasets.py      # Dataset download script
```

### Dataset Setup

Download all required datasets:

```bash
python seed_datasets.py
```

This downloads:
- WMDP Benchmark (3,668 questions)
- WildChat (10k conversations)
- lm-evaluation-harness

### Testing Scripts

**Test sandbagging detection:**
```bash
cd context/scripts
python test_wmdp.py --model gemini/gemini-3-flash-preview --limit 10
```

**Test sycophancy detection:**
```bash
python test_sycophancy.py --models gemini/gemini-3-flash-preview
```

### Git Workflow

1. Create a feature branch:
```bash
git checkout -b feat/your-feature-name
```

2. Make changes and commit (pre-commit hooks run automatically):
```bash
git add .
git commit -m "feat(scope): description"
```

3. If pre-commit fails, fix issues and try again:
```bash
# Format automatically fixed files are staged
git add .
git commit -m "feat(scope): description"
```

### Commit Message Format

Follow conventional commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(llm): add GPT-5.2 support
fix(storage): handle missing file gracefully
docs(readme): update API key instructions
test(sycophancy): add edge case tests
```

### Troubleshooting

**Pre-commit hooks failing:**
```bash
# Run manually to see detailed errors
uv run pre-commit run --all-files

# Update hooks to latest versions
uv run pre-commit autoupdate
```

**Type checking errors:**
```bash
# Check specific file
uv run mypy path/to/file.py

# Ignore missing imports for external libraries
# (already configured in pyproject.toml)
```

**Dependency issues:**
```bash
# Recreate virtual environment
rm -rf .venv
uv sync --all-extras
```

### Getting Help

- Check [CLAUDE.md](CLAUDE.md) for project-specific guidelines
- Review [README.md](README.md) for project overview
- See [HACKATHON_RESOURCES.md](context/HACKATHON_RESOURCES.md) for research papers

### Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code is formatted with Black
- [ ] Ruff linting passes
- [ ] Type checking passes (mypy)
- [ ] Tests added/updated for changes
- [ ] Tests pass with coverage >80%
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventional format
- [ ] Pre-commit hooks pass

### Questions?

Contact the team or open an issue in the repository.
