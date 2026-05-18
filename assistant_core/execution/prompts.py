"""Prompt templates used by the execution runner.

Kept here so prompts can be reviewed and tuned independently of the call sites.
All prompts are written to be model-agnostic and stable across qwen3,
deepseek-r1, and llama 3.3 families.
"""


EXECUTION_SYSTEM_PROMPT = (
    "You execute only READY local-first work packets. "
    "Do not modify original user files. Do not perform external writes. "
    "Use cloud only after explicit policy authorization. "
    "When unsure, label the assumption rather than guess. "
    "Always respect the work packet's stated audience, sources, and stop conditions."
)


EVALUATOR_SYSTEM_PROMPT = (
    "You are a strict evaluator. Return ONLY valid JSON matching the requested schema. "
    "Do not include any prose, code fences, or commentary outside the JSON."
)


EVALUATOR_PROMPT = (
    "Return strict JSON only with these keys: pass (bool), quality_score (0..1), "
    "grounding_score (0..1), completeness_score (0..1), actionability_score (0..1), "
    "contradiction_score (0..1), hallucination_risk ('low'|'medium'|'high'), "
    "missing_information (list of strings), needs_retry (bool), "
    "recommended_next_step ('pass'|'retry_local_secondary'|'reasoning_check'|"
    "'cloud_review'|'human_review'), reason (string)."
)


# ---------- Extraction (per source file) ---------------------------------

EXTRACT_PROMPT_TEMPLATE = """You are extracting structured signals from one source document for a private work brief.

WORK PACKET CONTEXT
- Title: {title}
- Objective: {objective}
- Audience: {audience}
- Quality bar: {quality_threshold}
- Assumption policy: {assumption_policy}
- Stop conditions: {escalation_policy}

SOURCE FILE
- Path: {source_path}
- Kind: {kind}

SOURCE CONTENT (verbatim; do not summarize away the source itself):
---
{content}
---

INSTRUCTIONS
1. Read the source carefully.
2. Extract structured signals as Markdown sections, in the exact order below.
3. Be specific. Cite quotes or line ranges from the source where helpful.
4. If a section has no content, write "(none)" - do not fabricate.
5. Label every inference clearly with "Assumption:" prefix.

REQUIRED SECTIONS

## Priorities
- One bullet per priority. Each: <statement>. Source: <quote or ref>. Rationale: <one line>.

## Decisions needed
- One bullet per decision. Each: <decision>. Owner if stated: <name or "unclear">. Source: <quote or ref>.

## Risks / Blockers
- One bullet per item. Each: <risk>. Severity (low/medium/high): <level>. Source: <quote or ref>.

## Action items (with owners where stated)
- One bullet per action. Each: <action>. Owner: <name or "unclear">. Source: <quote or ref>.

## Draft messages (DO NOT SEND; for human review)
- (none) unless the source explicitly contains an unsent reply or message stub.

## Open questions
- Things the source raises but does not resolve.

## Assumptions made
- One bullet per inference you made while extracting. Each prefixed "Assumption:".

Return only the Markdown above. No preamble, no postscript."""


# ---------- Synthesis (all extractions -> morning brief) -----------------

SYNTHESIZE_PROMPT_TEMPLATE = """You are synthesizing a private morning brief from multiple structured per-file extractions.

WORK PACKET CONTEXT
- Title: {title}
- Objective: {objective}
- Audience: {audience}
- Quality bar: {quality_threshold}
- Assumption policy: {assumption_policy}
- Escalation policy: {escalation_policy}
- Success criteria: {success_criteria}

PER-FILE EXTRACTIONS (one per source file processed):
{extractions}

INSTRUCTIONS
Produce a single concise Markdown morning brief, structured as below.
- Be specific. Carry source attribution from the extractions.
- Cap the top section at three items. Other sections may be longer.
- Preserve "Assumption:" labels from the source extractions.
- Where two extractions disagree, surface the conflict explicitly under "Conflicts".
- Do not invent items not present in the extractions.

OUTPUT FORMAT

# Morning Brief - {today}

## Today's three things
1. <item> (Source: <file>)
2. <item> (Source: <file>)
3. <item> (Source: <file>)

## Decisions needed
<bullets, each with owner and source file>

## Risks surfaced
<bullets, severity-ordered, with source file>

## Action items by owner
<grouped sublists by owner name, "unclear" group last>

## Open questions
<bullets with source file>

## Conflicts between sources
<bullets when two extractions disagree, otherwise "(none)">

## Sources used
<bulleted list of source file paths>

## Assumptions list
<flattened from per-file extractions>

## Confidence
<one-line self-assessment: low / medium / high, with one sentence why>

Return only the Markdown above. No preamble."""


# ---------- Helpers ------------------------------------------------------

def format_extract_prompt(*, packet, source_path, kind, content):
    return EXTRACT_PROMPT_TEMPLATE.format(
        title=packet.title or "",
        objective=(packet.objective or "").strip() or "(unspecified)",
        audience=packet.audience or "(unspecified)",
        quality_threshold=packet.quality_threshold or "(unspecified)",
        assumption_policy=packet.assumption_policy or "(unspecified)",
        escalation_policy=packet.escalation_policy or "(unspecified)",
        source_path=source_path,
        kind=kind,
        content=content,
    )


def format_synthesize_prompt(*, packet, extractions, today):
    return SYNTHESIZE_PROMPT_TEMPLATE.format(
        title=packet.title or "",
        objective=(packet.objective or "").strip() or "(unspecified)",
        audience=packet.audience or "(unspecified)",
        quality_threshold=packet.quality_threshold or "(unspecified)",
        assumption_policy=packet.assumption_policy or "(unspecified)",
        escalation_policy=packet.escalation_policy or "(unspecified)",
        success_criteria=", ".join(packet.success_criteria) if packet.success_criteria else "(unspecified)",
        extractions=extractions,
        today=today,
    )


__all__ = [
    "EXECUTION_SYSTEM_PROMPT",
    "EVALUATOR_SYSTEM_PROMPT",
    "EVALUATOR_PROMPT",
    "EXTRACT_PROMPT_TEMPLATE",
    "SYNTHESIZE_PROMPT_TEMPLATE",
    "format_extract_prompt",
    "format_synthesize_prompt",
]
