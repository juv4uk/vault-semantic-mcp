# ŚŪNYA-BHŪMI integration policy

Parent coordination: `juv4uk/ecosystem#12` and `#13`.

## Purpose

Integrate this vault bridge with the shared ŚŪNYA-BHŪMI research discipline without turning semantic search or shared memory into a truth authority.

## Default client policy

Start every new agent/client in **READ/SEARCH-first** mode.

Before write access is enabled, the client must successfully:

1. read the canonical research protocol;
2. search and retrieve one concept note;
3. summarize it without modifying source text;
4. distinguish `GIVEN / OBSERVED / INFERRED / HYPOTHESIZED`;
5. produce a handoff proposal when a task belongs to another kṣetra;
6. record bridge/config/version provenance.

## Protected research surfaces

By policy, clients must not silently rewrite:

- Genesis records;
- raw observations;
- raw evidence artifacts;
- source quotations/provenance.

Interpretations, hypotheses, and derived summaries belong in separate records.

## Semantic retrieval rule

Embedding similarity, ranking, nearest-neighbor retrieval, clustering, and model-generated summaries are **retrieval aids**, not evidence-strength upgrades.

A retrieved hypothesis remains a hypothesis.
A retrieved observation remains an observation.
Repeated agent agreement does not promote either.

## Write promotion

Write access should be promoted explicitly and incrementally:

`READ/SEARCH → CREATE-DERIVED-NOTES → APPEND-COORDINATION → CONTROLLED-EDIT`

Deletion, bulk rewriting, or mutation of protected surfaces requires explicit user authorization.

## Failure behavior

If an operation cannot be performed in the current kṣetra, report:

`BLOCKED: <reason> — needed kṣetra: <environment/tool>`

Do not simulate a successful write or verification.

## Provenance minimum

For each agent-produced derived note, preserve where practical:

- agent/source;
- timestamp;
- query/task;
- source refs;
- relevant repository commit/build;
- epistemic status;
- evidence level if applicable.

## Non-goals

This integration does not claim that shared memory produces intelligence, self-awareness, understanding, motivation, or emergence.

> Research memory must increase traceability, not confidence theater.
