# Alavista – Ontology Layer Specification (v0.1 → forward-compatible)

The ontology is the backbone that keeps Alavista disciplined.  
It defines *what kinds of things exist*, *what kinds of relationships are legitimate*, and *how analysis profiles reason safely and consistently across the system*.

This layer is intentionally minimal now, but engineered for long-term expansion (v0.2+).

---

# 1. Purpose

### What the ontology provides:

1. **A shared vocabulary**  
   All subsystems — extraction, graph, analysis profiles, LLM agents, RAG — speak the same domain language.

2. **Typed constraints**  
   Nodes and edges have valid combinations, preventing speculative graph edges.

3. **Analysis profile grounding**  
   Each analysis profile is restricted to a curated subset of entity types and relations.

4. **Safer LLM behavior**  
   The ontology limits hallucination by explicitly defining what *can* and *cannot* exist.

5. **Long-term extensibility**  
   Every new feature (graph ops, analysis profile workflows, ingestion rules) attaches cleanly to the ontology.

---

# 2. Storage & Structure

Stored at:

```
/ontology/ontology_v0.1.json
```

Format:

```json
{
  "version": "0.1",

  "entities": {
    "Person": {
      "description": "A human individual appearing in documents.",
      "aliases": ["Individual", "Witness", "Victim", "Subject"]
    },

    "Organization": {
      "description": "Legal or informal groups: corporations, agencies, foundations.",
      "aliases": ["Org", "Company", "Agency"]
    },

    "Document": {
      "description": "A source file or chunk within the corpus.",
      "aliases": ["Doc", "Record", "Transcript"]
    },

    "Flight": {
      "description": "A distinct aircraft movement or manifest occurring in records.",
      "aliases": ["Manifest"]
    },

    "Property": {
      "description": "Real estate or physical assets owned or sold by entities.",
      "aliases": ["Asset", "Location"]
    },

    "Account": {
      "description": "A financial account (bank, brokerage, trust).",
      "aliases": []
    },

    "Transaction": {
      "description": "A fund transfer or monetary event.",
      "aliases": []
    }
  },

  "relations": {
    "APPEARS_IN": {
      "description": "Entity explicitly appears in a document.",
      "domain": ["Person", "Organization"],
      "range": ["Document"]
    },

    "MENTIONED_WITH": {
      "description": "Two entities co-mentioned in text.",
      "domain": ["Person", "Organization"],
      "range": ["Person", "Organization"]
    },

    "ON_FLIGHT": {
      "description": "Person is present on a flight manifest.",
      "domain": ["Person"],
      "range": ["Flight"]
    },

    "OWNS": {
      "description": "Property or account ownership expressed in text.",
      "domain": ["Person", "Organization"],
      "range": ["Property", "Account"]
    },

    "HOLDS": {
      "description": "Entity holds or controls an account.",
      "domain": ["Person", "Organization"],
      "range": ["Account"]
    },

    "TRANSFERRED_FUNDS": {
      "description": "Direct fund transfer event.",
      "domain": ["Account"],
      "range": ["Account"]
    }
  }
}
```

The initial ontology is deliberately sparse but expressive enough for structured reasoning.

---

# 3. Ontology Constraints & Validation Rules

### **3.1 Entity Type Validation**

`validate_entity_type(type: str)` ensures:

- type exists in ontology  
- type is spelled correctly  
- aliases resolve to canonical names

### **3.2 Relation Validation**

`validate_relation(entityA, relation_type, entityB)` enforces:

- relation_type exists  
- entityA.type ⟶ domain is valid  
- entityB.type ⟶ range is valid

If invalid: extraction drops the relation silently (never hallucinates).

---

# 4. Integrations With the System

## 4.1 Extraction Pipeline

During entity/relation extraction:

- entity types must match ontology  
- relationship must match domain/range  
- “weak” entity types (ambiguous NER) are discarded  
- relations without valid evidence snippets are dropped  

This reduces noise significantly.

---

## 4.2 Graph Layer

Graph nodes and edges carry ontology tags:

```python
GraphNode(type="Person")
GraphEdge(type="MENTIONED_WITH")
```

GraphStore uses these types to:

- reject invalid node combinations  
- prevent illegal edges  
- ensure pathfinding only navigates structurally valid relationships  
- enable ontology-aware subgraph queries

---

## 4.3 Analysis Profiles

Each analysis profile has:

1. **Entity type whitelist**  
2. **Relation type whitelist**  
3. **Interpretation rules** (“strength model”)  

Example (Financial Forensics):

```json
{
  "entity_whitelist": ["Person", "Organization", "Account", "Transaction"],
  "relation_whitelist": ["OWNS", "HOLDS", "TRANSFERRED_FUNDS"],
  "strength_rules": {
    "OWNS": "strong",
    "HOLDS": "strong",
    "TRANSFERRED_FUNDS": "strong",
    "MENTIONED_WITH": "weak"
  }
}
```

---

## 4.4 Local LLM Agents

The agent prompt uses ontology constraints to:

- choose which MCP graph tools to invoke  
- avoid asking the graph for illegal relationships  
- restrict the language model from inventing unsupported entity categories

---

# 5. OntologyService

Located at:

```
core/ontology/service.py
```

API:

```python
class OntologyService:

    def list_entity_types(self) -> list[str]: ...

    def list_relation_types(self) -> list[str]: ...

    def get_entity_info(self, entity_type: str) -> dict: ...

    def get_relation_info(self, relation_type: str) -> dict: ...

    def resolve_alias(self, name: str) -> str: ...

    def validate_entity(self, entity: Entity) -> bool: ...

    def validate_relation(self, edge: Edge) -> bool: ...
```

---

# 6. MCP Tools for Ontology

1. `ontology_describe_type(type)`  
   Returns canonical definition + aliases + analysis profile relevance.

2. `ontology_list_relations(entity_id)`  
   Returns valid edges that can originate from an entity of this type.

3. `ontology_help()`  
   Prints friendly documentation for reasoning agents.

---

# 7. Tests

Unit Tests:
- entity type validation  
- alias resolution  
- domain/range enforcement  
- relation rejection  
- schema load  

Integration Tests:
- extraction uses ontology  
- graph rejects invalid edges  
- analysis profiles select correct relations  
- ontology tools callable through MCP  

---

# 8. Evolution Path (v0.2+)

Future expansions:

- Time-bound relationships  
- Chain-of-custody for documents  
- Expanded asset classes  
- Narrative graph inference  
- Multi-persona overlays  
- Confidence-based relation classes  

---

# 9. Definition of Done (Ontology v0.1)

- `/ontology/ontology_v0.1.json` loads cleanly  
- OntologyService implements validation  
- Extraction enforces ontology  
- Graph enforces domain/range  
- Personas reference ontology  
- MCP ontology tools operational  
- >80% test coverage  

