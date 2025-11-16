# Alavista – Data Models

This document defines the core data models used across the system. All models should be implemented using **Pydantic** (v1 or v2 depending on the project setup).


## 1. Corpus, Document, and Related Models

### 1.1 `Corpus`

Represents a logical collection of documents.

```python
from pydantic import BaseModel
from typing import Any, Literal


class Corpus(BaseModel):
    id: str
    type: Literal["persona_manual", "research", "global"]  # "persona_manual" to be renamed "profile_manual"
    persona_id: str | None = None    # for persona_manual type (field to be renamed to analysis_profile_id)
    topic_id: str | None = None      # for research corpora (e.g. "epstein_core")
    name: str
    description: str | None = None
    metadata: dict[str, Any] = {}
```
