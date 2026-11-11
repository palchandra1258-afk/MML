# Dependency Registry Specification

`schemas/concept_dependency_registry_v1.schema.json` defines a versioned registry. Each relationship includes an ID, source/supporting concept, target concept, relationship type, source provenance, verification status, confidence, creation time, and schema version.

Relationship types are `PREREQUISITE`, `SUPPORTING_CONCEPT`, `RELATED_CONCEPT`, and `ADVANCED_CONCEPT`. Diversion detection only considers the first two. Status is one of:

- `verified`: the source has been reviewed and recorded as verified by a project owner; no such repository entries are currently supplied.
- `manually_configured`: an explicitly curated relationship, not an EdNet observation.
- `synthetic_test`: test-only relationship, excluded by default at runtime.

The default registry is empty because EdNet's skill tags do not encode prerequisite edges. No concept dependency is inferred from co-occurrence, question order, or learner performance. Test fixtures use clearly labeled synthetic edges. A future populated registry should include its domain source and human review protocol; merely setting `verified` does not make an entry scientifically validated.
