# Refactor: From "Persona" to "Analysis Profile"

## Motivation

The original design used the term "persona" to describe domain-constrained expert reasoning engines. While this term conveyed the idea of different analytical perspectives, it has significant drawbacks:

1. **Anthropomorphic implications**: "Persona" suggests a simulated person or character, which misrepresents what these components actually do.
2. **Misleading semantics**: The system does not create artificial personalities or simulate human behavior; it applies domain-specific analytical frameworks.
3. **Clarity**: A function-oriented term better reflects the actual purpose—these are **analytical configuration profiles** that define:
   - Ontology constraints (which entities and relations are relevant)
   - Tool whitelists (which MCP tools and services can be used)
   - Reasoning strategies (how to approach investigation questions)
   - Safety rules (what speculation to forbid)
   - Domain-specific corpora (manuals, techniques, examples)

By renaming to **"Analysis Profile"**, we emphasize that these are:
- **Configuration-driven**: YAML/JSON policy files
- **Function-oriented**: Domain expert reasoning engines, not characters
- **Evidence-based**: Analytical frameworks constrained by ontology and provenance
- **Professional**: Appropriate for investigative, forensic, and analytical contexts

## Current Usage of Personas

Based on the existing architecture and documentation:

### Conceptual Role
Personas (now Analysis Profiles) serve as:
- **Domain-expert reasoning engines** that interpret investigative questions through specialized lenses
- **Policy configurations** that constrain the system's behavior to domain-appropriate operations
- **Ontology-aware filters** that whitelist relevant entity and relation types
- **Safety scaffolding** that enforces evidence-based reasoning and forbids speculation
- **Corpus-attached frameworks** with their own training materials, techniques, and examples

### Technical Implementation
Personas are implemented as:
- **YAML configuration files** in `core/personas/persona_profiles/` containing:
  - Entity and relation type whitelists
  - Tool access permissions
  - Reasoning approach guidelines
  - Evidence strength rules
  - Corpus paths for domain-specific knowledge
  - Safety disclaimers and constraints

- **Runtime components**:
  - `PersonaBase`: Abstract class defining persona interface
  - `PersonaRegistry`: Loads and validates YAML definitions
  - `PersonaRuntime`: Orchestrates multi-step reasoning using personas
  - `PersonaPlanner`: LLM tool for generating investigation plans

- **API and MCP surfaces**:
  - HTTP routes: `/personas` for listing and querying personas
  - MCP tools: `persona_list`, `persona_query`, `persona_ingest_resource`, `persona_inspect`, `persona_explain`

### Integration Points
Personas integrate with:
- **SearchService**: For semantic/hybrid queries on research and manual corpora
- **GraphService**: For structural queries constrained by persona's ontology whitelist
- **OntologyService**: For validating entity/relation types
- **LLMClient**: For controlled reasoning and answer generation
- **CorpusStore**: For accessing persona-specific and research corpora

## Selected New Term

After evaluating several options, we have selected **"Analysis Profile"** as the replacement term:

### Primary Choice: Analysis Profile
**Rationale**:
- Emphasizes the **analytical function** of these configurations
- "Profile" clearly indicates this is a configuration/policy, not a person
- Aligns with common usage in professional contexts (e.g., "risk analysis profile", "threat analysis profile")
- Natural fit for phrases like "using the Financial Forensics analysis profile"
- Abbreviates naturally to "profile" in code and conversation

### Alternative Terms Considered
- **Investigation Profile**: Also appropriate, but slightly narrower in scope
- **Reasoning Profile**: More abstract; less clear about the analytical domain focus
- **Domain Profile**: Too generic; doesn't emphasize the analytical nature

## Rename Mapping

### Conceptual Terminology
| Old Term | New Term |
|----------|----------|
| Persona | Analysis Profile |
| Persona-driven reasoning | Analysis profile-driven reasoning |
| Persona framework | Analysis profile framework |
| Persona definition | Analysis profile definition |
| Persona manual | Analysis profile manual |

### Code-Level Components (Future Implementation)
The following code-level renames should be performed in a subsequent implementation PR:

| Current Name | Proposed New Name |
|--------------|-------------------|
| `PersonaBase` | `AnalysisProfileBase` |
| `PersonaRegistry` | `AnalysisProfileRegistry` |
| `PersonaRuntime` | `AnalysisProfileRuntime` |
| `PersonaPlanner` | `AnalysisProfilePlanner` |
| `persona_id` (field/parameter) | `analysis_profile_id` or `profile_id` |
| `core/personas/` | `core/analysis_profiles/` |
| `persona_profiles/` | `profile_definitions/` |

### Data Model Fields
| Current Field | Proposed New Field |
|---------------|-------------------|
| `type: "persona_manual"` | `type: "profile_manual"` or `type: "analysis_profile_manual"` |
| `persona_id` in Corpus model | `analysis_profile_id` or `profile_id` |

### API Endpoints (Future Implementation)
| Current Endpoint | Proposed New Endpoint |
|------------------|----------------------|
| `/personas` | `/analysis-profiles` or `/profiles` |
| `/personas/{persona_id}` | `/analysis-profiles/{profile_id}` |
| `/personas/{persona_id}/answer` | `/analysis-profiles/{profile_id}/answer` |

### MCP Tools (Future Implementation)
| Current Tool | Proposed New Tool |
|--------------|-------------------|
| `persona_list` | `analysis_profile_list` or `profile_list` |
| `persona_query` | `analysis_profile_query` or `profile_query` |
| `persona_select` | `analysis_profile_select` or `profile_select` |
| `persona_ingest_resource` | `analysis_profile_ingest_resource` or `profile_ingest_resource` |
| `persona_inspect` | `analysis_profile_inspect` or `profile_inspect` |
| `persona_explain` | `analysis_profile_explain` or `profile_explain` |

### File Names (Future Implementation)
| Current File | Proposed New File |
|--------------|-------------------|
| `persona_base.py` | `analysis_profile_base.py` |
| `persona_registry.py` | `analysis_profile_registry.py` |
| `persona_runtime.py` | `analysis_profile_runtime.py` |
| `07_persona_framework.md` | `07_analysis_profile_framework.md` |
| `persona_profiles/*.yaml` | `profile_definitions/*.yaml` |

## Implementation Strategy

### Phase 1: Documentation (This PR)
- Update all narrative documentation to use "Analysis Profile" terminology
- Create this refactors document to guide future implementation
- Where code/file names are mentioned, add clarifying notes like:
  - "Analysis profiles (implemented in `core/personas/`, to be renamed in a future refactor)"
  - "`PersonaRuntime` (conceptually now `AnalysisProfileRuntime`)"
- Keep actual file paths and code references accurate to current implementation

### Phase 2: Code Implementation (Future PR)
Perform the actual code-level renames:
1. Rename core classes and modules
2. Update imports across the codebase
3. Rename directories and files
4. Update configuration files and YAML schemas
5. Maintain backward compatibility aliases for one version if needed
6. Update all code comments and docstrings
7. Update test names and test data

### Phase 3: API Transition (Future PR)
Update public-facing APIs:
1. Create new endpoints/tools with profile-based names
2. Maintain old endpoints as deprecated aliases for one version
3. Add deprecation warnings to old endpoints
4. Update MCP tool registration
5. Update HTTP route definitions
6. Document migration path for API consumers

## Backward Compatibility Notes

When implementing the code-level changes:
- **Consider deprecation period**: Keep old names as aliases for 1-2 versions
- **Add deprecation warnings**: Log warnings when old names are used
- **Update migration guide**: Provide clear instructions for users updating integrations
- **Version API changes**: Use semantic versioning to signal breaking changes
- **Test both old and new names**: Ensure aliases work correctly during transition

## Success Criteria

This refactor is complete when:
- [x] All documentation uses "Analysis Profile" terminology consistently
- [x] This refactors document provides complete rename mapping
- [ ] (Future) All code uses new class/module names
- [ ] (Future) All API endpoints use new paths
- [ ] (Future) All MCP tools use new names
- [ ] (Future) All tests updated and passing
- [ ] (Future) Migration guide available for API consumers
- [ ] (Future) Deprecated names removed after transition period

## Related Documents

This refactor affects the following documentation:
- `docs/01_product_overview.md`
- `docs/02_architecture_overview.md`
- `docs/03_data_models.md`
- `docs/04_core_services.md`
- `docs/07_persona_framework.md` (to be renamed `07_analysis_profile_framework.md`)
- `docs/08_interfaces_and_tools.md`
- `README.md`
- `alavista/__init__.py`
- All roadmap and phase completion documents

## Questions and Decisions

### Q: Why not just "Profile"?
**A**: While "profile" is shorter, "analysis profile" provides necessary context. In isolation, "profile" could refer to user profiles, performance profiles, etc. The full term "analysis profile" is unambiguous and can be shortened to "profile" in contexts where it's clear.

### Q: Should we use "analysis_profile" or "profile" in code?
**A**: Prefer full term in class names and file names for clarity (`AnalysisProfileRuntime`), but shorter form is acceptable for common variables and parameters where context is clear (e.g., `profile_id` instead of `analysis_profile_id`).

### Q: What about existing YAML files and user data?
**A**: Field names in YAML should be updated, but loaders should accept both old and new field names during transition period. User data migration scripts should be provided.

### Q: How does this affect ontology terminology?
**A**: The ontology itself doesn't reference personas, so no changes needed there. However, documentation about how profiles use ontology constraints will be updated.
