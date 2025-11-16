# Alavista

**A local-first investigative analysis platform for civic research and accountability journalism.**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Overview

Alavista is a powerful, privacy-respecting platform that combines document ingestion, semantic search, knowledge graph construction, and persona-driven reasoning to support deep investigative analysis. Built on a **local-first** philosophy, it runs entirely on your machine without requiring cloud services or external APIs.

### Key Features

- **Document Ingestion**: Process FOIA dumps, court filings, reports, and diverse document formats
- **Semantic Search**: Combine BM25 keyword search with vector embeddings for comprehensive retrieval
- **Knowledge Graph**: Build typed entity-relationship graphs with full provenance tracking
- **Ontology Layer**: Minimal, explicit ontology for constrained reasoning and validation
- **Persona Framework**: Domain-expert reasoning styles (investigative journalist, financial forensics, etc.)
- **MCP Server**: Expose Alavista as a toolset for language models via Model Context Protocol
- **HTTP API**: RESTful interface for UI integration and automation

### Core Principles

1. **Local-First & Privacy-Respecting**: Runs on a single machine with no required cloud dependencies
2. **Evidence-First**: All claims backed by documents, snippets, and confidence scores
3. **Clear Layer Separation**: Modular architecture with clean boundaries
4. **Explainability**: Full provenance tracking for all analysis and reasoning
5. **Defensive Licensing**: AGPL-3.0 to prevent proprietary capture

## Hardware Requirements

### Minimum
- **RAM**: 16GB system memory
- **GPU**: 8GB VRAM (NVIDIA recommended for GPU acceleration)
- **Storage**: 50GB free disk space
- **CPU**: Modern multi-core processor

### Recommended
- **RAM**: 32GB system memory
- **GPU**: 16GB VRAM (NVIDIA RTX 3090/4090 or similar)
- **Storage**: 100GB+ SSD
- **CPU**: 8+ cores

## Quick Start with Docker Compose

The fastest way to get started is using Docker Compose, which sets up both Ollama and the Alavista application:

```bash
# Clone the repository
git clone https://github.com/ctonyperry/alavista.git
cd alavista

# Copy environment configuration
cp .env.example .env

# Start services
docker compose up -d

# Check logs
docker compose logs -f app
```

This will:
1. Start Ollama service on port 11434
2. Build and start the Alavista application
3. Run tests to verify the setup

### GPU Support

To enable GPU acceleration for Ollama, uncomment the GPU configuration in `docker-compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

Ensure you have [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) installed.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) or pip for package management
- Git

### Local Development

```bash
# Clone the repository
git clone https://github.com/ctonyperry/alavista.git
cd alavista

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment configuration
cp .env.example .env

# Run tests
pytest

# Run linter
ruff check alavista/
```

## Configuration

Alavista uses Pydantic Settings for configuration management. Settings can be configured via:

1. Environment variables
2. `.env` file in the project root
3. Default values in code

### Key Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `Alavista` | Application name |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `DATA_DIR` | `./data` | Directory for storing application data |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama service URL |
| `OLLAMA_MODEL` | `llama3.1:8b` | Default LLM model |
| `JSON_LOGS` | `false` | Enable JSON-formatted structured logging |

See `.env.example` for a complete list of configuration options.

## Project Structure

```
alavista/
├── alavista/              # Main application package
│   ├── core/             # Core utilities, config, DI container
│   ├── interfaces/       # Shared interface definitions
│   ├── mcp/             # MCP server implementation
│   ├── api/             # HTTP API (FastAPI)
│   ├── ingestion/       # Document ingestion pipeline
│   ├── search/          # Search services (BM25, vector, hybrid)
│   ├── vector/          # Vector embeddings management
│   ├── graph/           # Knowledge graph layer
│   ├── ontology/        # Ontology definitions
│   └── personas/        # Persona framework
├── tests/                # Test suite
├── docker/              # Docker configuration
├── scripts/             # Utility scripts
└── docs/                # Documentation

```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_core/test_config.py

# Run with coverage
pytest --cov=alavista --cov-report=html

# Run only unit tests
pytest -m unit

# Run in verbose mode
pytest -v
```

## License

This project is licensed under the **GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)**.

### Why AGPL?

Alavista is a **civic-oriented project** intended to remain a **public good** and to resist proprietary enclosure. The AGPL ensures that:

1. Anyone can use, study, modify, and distribute this software
2. All modifications must be shared under the same license
3. Network use counts as distribution (modifications must be shared even for SaaS)
4. Large organizations can use it but must contribute improvements back

See [LICENSE](LICENSE) for the full license text.

## Use Cases

Alavista is designed for:

- **Investigative Journalists**: Analyze FOIA documents, emails, flight logs, financial records
- **Civic Researchers**: Track corruption, procurement patterns, conflicts of interest
- **Watchdog NGOs**: Regulatory capture analysis, policy research
- **Power Users**: Combine multiple public data sources for comprehensive investigations
- **Domain Analysts**: Financial forensics, OSINT, policy analysis

## Safety & Ethics

Alavista is designed with important guardrails:

1. **No speculation in the graph**: Only relationships explicitly stated in documents
2. **Evidence-narrative distinction**: Clear separation between facts and interpretation
3. **No guilt labeling**: Maps structure, not moral judgments
4. **User responsibility**: Tool for analysis, not for harassment or harm
5. **LLM prompt discipline**: System prompts enforce evidence-based reasoning

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`pytest && ruff check`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Roadmap

Alavista is developed in phases:

- **Phase 0** (Current): Project foundation, core infrastructure ✅
- **Phase 1**: Corpus store and document ingestion
- **Phase 2**: BM25 search and core indexing
- **Phase 3**: Vector embeddings and semantic search
- **Phase 4**: Knowledge graph foundation
- **Phase 5+**: Advanced features, persona framework, MCP server

See [docs/roadmap_part_1_phases_0-2.md](docs/roadmap_part_1_phases_0-2.md) for detailed roadmap.

## Documentation

- [Product Overview](docs/01_product_overview.md) - Vision and principles
- [Architecture Overview](docs/02_architecture_overview.md) - System design
- [Data Models](docs/03_data_models.md) - Core data structures
- [Core Services](docs/04_core_services.md) - Service layer details

## Support

- **Issues**: [GitHub Issues](https://github.com/ctonyperry/alavista/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ctonyperry/alavista/discussions)

## Acknowledgments

This project stands on the shoulders of:

- The open-source community
- FOIA activists and transparency advocates
- Investigative journalists worldwide
- Privacy-first technology advocates

## Status

⚠️ **Alpha Software**: Alavista is in early development. APIs and interfaces will change. Not recommended for production use yet.

---

Built with ❤️ for investigative journalism, civic research, and accountability.
