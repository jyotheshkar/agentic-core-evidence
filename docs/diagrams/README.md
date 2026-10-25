# Agentic Core Architecture Views

These are authored architecture designs recovered from System Architecture Workspace Site v81, source commit `4f583cb90bff726eada9a180a0eeba4118981a73` (24 October 2026, 13:40 UTC). The copied assets retain their exact source bytes; [the manifest](diagram-manifest.json) records file hashes and source paths.

## Current Scoped AWS Case Study

![Agentic Core AWS target](Agentic-Core-AWS-Target.png)

Read the [case study](Agentic-Core-AWS-Case-Study.md), or open the [editable SVG](Agentic-Core-AWS-Target.svg).

The selected design uses contract approval and a separate exact-candidate owner acceptance, two total candidate attempts, a bounded Bedrock plan proposal, reviewed operators, independent verification and guarded release. Its AWS runtime and cloud validation remain pending. The local code and tests elsewhere in this repository cover their stated subset; they do not implement or prove this whole AWS target.

## Supporting Views

- [User-to-MOA foundation](Agentic-Core-User-To-MOA-Foundation.png): the proposed lifecycle and six release conditions.
- [Enterprise reference PNG](reference/Agentic-Core-Enterprise-Reference.png) and [editable eight-page drawio](reference/Agentic-Core-Enterprise-Reference.drawio): an expanded 35-capability, 68-interface study.
- [Enterprise communication paths](reference/Agentic-Core-Enterprise-Communication.png): representative transport and trust paths for that expanded study.

The enterprise study has different scale, account and isolation assumptions from the small managed-service case study. It is supplementary, not the scoped MVP's deployment diagram. Editing its drawio does not regenerate the separate case-study SVG.

The source pack credits official [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/). Retain the applicable icon attribution and terms when reusing those assets. No AWS deployment, current cost or benchmark is established by these images.
