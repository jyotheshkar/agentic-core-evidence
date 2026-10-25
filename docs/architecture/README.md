# Architecture evidence

| Evidence | Date | Status |
|---|---|---|
| Python and SQLite core excerpt | 26 September 2026 source revision | Implemented deterministic source; five core modules, two synthetic test modules and 35 passing exported-source tests |
| [Foundation reference v0.1](agentic-core-foundation-v0.1.json) | 10 October 2026 supplied design | Proposed design and conditional derivations; acceptance tests are defined, not reported as passing |
| [Current scoped AWS case study](../diagrams/Agentic-Core-AWS-Case-Study.md) and [target diagram](../diagrams/Agentic-Core-AWS-Target.png) | 24 October 2026 source, Workspace v81 | Authored target design; AWS deployment and cloud runtime validation pending |

## Current scoped target

Read the [case study](../diagrams/Agentic-Core-AWS-Case-Study.md) alongside the [diagram index](../diagrams/README.md). The selected target keeps exact contract approval separate from later owner acceptance of the exact verified candidate. There are two total candidate attempts: the initial attempt and at most one admitted repair. Release authority and authority to operate the generated child workflow remain separate.

The target proposes bounded Bedrock plan proposals, reviewed deterministic operators, independent verification, a conditional release intent and receipt-based delivery reconciliation. These are requirements and design decisions, not cloud execution results. The six-pillar review states the evidence still needed.

## Implemented local source

The September excerpt validates and compiles bounded workflows, applies engine-scoped controls, persists local SQLite execution state and exchanges requests/receipts with a host. It has no cloud service or model/mail adapter. The [35-test receipt](../verification/core-tests.json) covers that exact excerpt and does not prove the full October target.

## Earlier foundation and expanded reference

The October foundation describes Contract Engine, Core Controller, Workflow Builder and Verifier with a shared six-rule PIC library. Its AWS mappings and mathematical propositions remain conditional proposals.

The [enterprise reference views](../diagrams/README.md#supporting-views) have broader scale, account and isolation assumptions than the current scoped case study. Editing the enterprise drawio does not regenerate the separate scoped SVG. Do not relabel the historical Agentic Core/SOL relationship as a demonstrated QUASAR integration.

## Provenance

The [diagram manifest](../diagrams/diagram-manifest.json) records exact recovered source paths, source commit and hashes for seven assets. [SOURCE_PROVENANCE.json](../../SOURCE_PROVENANCE.json) records runtime/reference sources and the hash of that manifest and its index. No AWS deployment or measured cost claim follows from an image.
