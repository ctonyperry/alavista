# Contributing to Alavista

Thank you for your interest in contributing to Alavista! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [License Agreement](#license-agreement)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of:
- Experience level
- Gender identity and expression
- Sexual orientation
- Disability
- Personal appearance
- Race or ethnicity
- Age
- Religion

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community and project
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, trolling, or discriminatory comments
- Personal or political attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct that could reasonably be considered inappropriate

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Familiarity with pytest and modern Python development practices
- (Optional) Docker and Docker Compose for containerized development

### Setting Up Your Development Environment

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/alavista.git
   cd alavista
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ctonyperry/alavista.git
   ```

4. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

5. **Install dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

6. **Copy environment configuration**:
   ```bash
   cp .env.example .env
   ```

7. **Verify setup**:
   ```bash
   pytest
   ruff check alavista/
   ```

## Development Workflow

### Before Starting Work

1. **Check existing issues** to avoid duplicate work
2. **Create or comment on an issue** describing what you plan to work on
3. **Wait for feedback** from maintainers before starting significant work

### Working on Your Feature

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Keep your branch updated**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

3. **Make small, focused commits**:
   ```bash
   git commit -m "Add specific feature or fix"
   ```

4. **Write or update tests** for your changes

5. **Run tests frequently**:
   ```bash
   pytest
   ```

6. **Run linting**:
   ```bash
   ruff check alavista/
   ruff format alavista/
   ```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 100 characters (configured in ruff)
- **Type hints**: Use type hints for function signatures
- **Docstrings**: Google style docstrings for all public functions and classes

### Code Organization

- **Module boundaries**: Respect the layer separation (core, interfaces, etc.)
- **No circular imports**: Structure code to avoid circular dependencies
- **Dependency injection**: Use the container pattern for service dependencies
- **Interface segregation**: Keep interfaces focused and minimal

### Example Code Style

```python
"""
Module docstring explaining the purpose.
"""

from typing import Optional
from pathlib import Path

from alavista.core.config import Settings


class MyService:
    """
    Brief description of the class.
    
    More detailed description if needed, explaining the purpose,
    responsibilities, and any important usage notes.
    """
    
    def __init__(self, settings: Settings) -> None:
        """
        Initialize the service.
        
        Args:
            settings: Application settings instance
        """
        self.settings = settings
    
    def process_data(self, input_path: Path) -> Optional[str]:
        """
        Process data from the given path.
        
        Args:
            input_path: Path to the input file
            
        Returns:
            Processed data as a string, or None if processing fails
            
        Raises:
            FileNotFoundError: If the input file doesn't exist
            ValueError: If the input data is invalid
        """
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")
        
        # Implementation here
        return None
```

### Naming Conventions

- **Classes**: `PascalCase`
- **Functions/Methods**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: Prefix with single underscore `_private_method`
- **Module names**: Short, lowercase, snake_case

## Testing Guidelines

### Test Organization

- **Location**: Tests mirror the source structure under `tests/`
- **Naming**: Test files start with `test_`, test functions start with `test_`
- **Markers**: Use pytest markers (`@pytest.mark.unit`, `@pytest.mark.integration`)

### Writing Good Tests

1. **Use descriptive names**:
   ```python
   def test_settings_load_from_environment_variables():
       # Test implementation
   ```

2. **Follow AAA pattern** (Arrange, Act, Assert):
   ```python
   def test_process_document():
       # Arrange
       document = create_test_document()
       processor = DocumentProcessor()
       
       # Act
       result = processor.process(document)
       
       # Assert
       assert result.status == "success"
   ```

3. **Use fixtures** for common setup:
   ```python
   @pytest.fixture
   def sample_document():
       return {"title": "Test", "content": "Sample content"}
   
   def test_document_processing(sample_document):
       processor = DocumentProcessor()
       result = processor.process(sample_document)
       assert result is not None
   ```

4. **Test edge cases**:
   - Empty inputs
   - Invalid data
   - Boundary conditions
   - Error cases

5. **Keep tests independent**: Each test should run in isolation

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_core/test_config.py

# Specific test
pytest tests/test_core/test_config.py::TestSettings::test_default_values

# With coverage
pytest --cov=alavista --cov-report=html

# Fast tests only
pytest -m "not slow"

# Verbose output
pytest -v
```

## Documentation

### Code Documentation

- **Docstrings**: All public modules, classes, and functions must have docstrings
- **Type hints**: Use type hints for better IDE support and documentation
- **Comments**: Use sparingly for complex logic that isn't self-explanatory

### User Documentation

When adding features that affect users:

1. Update relevant documentation in `docs/`
2. Add examples to README.md if appropriate
3. Update configuration documentation for new settings

### Architecture Documentation

For significant architectural changes:

1. Update `docs/02_architecture_overview.md`
2. Document design decisions in code comments or separate doc files
3. Add diagrams if they help explain the architecture

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass**: `pytest`
2. **Run linting**: `ruff check alavista/`
3. **Format code**: `ruff format alavista/`
4. **Update documentation** as needed
5. **Write clear commit messages**

### Submitting Your PR

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** on GitHub

3. **Fill out the PR template** with:
   - Clear description of changes
   - Related issue numbers
   - Testing performed
   - Screenshots (if UI changes)
   - Breaking changes (if any)

4. **Respond to feedback** from reviewers promptly

### PR Review Process

- Maintainers will review your PR
- Address any requested changes
- Once approved, a maintainer will merge your PR
- Your contribution will be acknowledged in release notes

## License Agreement

By contributing to Alavista, you agree that your contributions will be licensed under the **GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)**.

This ensures that:
- Your contributions remain open source
- Others can build upon your work
- The project stays free and open

## Questions?

- **General questions**: [GitHub Discussions](https://github.com/ctonyperry/alavista/discussions)
- **Bug reports**: [GitHub Issues](https://github.com/ctonyperry/alavista/issues)
- **Feature requests**: [GitHub Issues](https://github.com/ctonyperry/alavista/issues)

## Recognition

All contributors will be acknowledged in:
- Release notes
- Project README (for significant contributions)
- Git commit history

Thank you for contributing to Alavista and supporting open, civic-oriented technology!
