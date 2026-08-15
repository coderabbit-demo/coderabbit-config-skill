# Quickstart Baselines

Used by the quickstart path (Q1 only). Start from the base, apply one overlay per archetype the user
selected, resolve collisions with the precedence rules at the bottom, then write the merged result.

Do **not** paste all four overlays. A quickstart config that turns on everything is worse than no
config — it just moves the tuning problem to the user's first ten PRs.

---

## Base — applied in every quickstart

```yaml
# yaml-language-server: $schema=https://coderabbit.ai/integrations/schema.v2.json

# Inherit org-level standards configured by CodeRabbit admins.
inheritance: true

reviews:
  auto_review:
    auto_incremental_review: true

knowledge_base:
  # Let CodeRabbit infer related repositories in this org.
  automatic_repository_linking: true
```

---

## Overlay A — Only flag the most critical issues

```yaml
reviews:
  profile: quiet
  review_details: false
  collapse_walkthrough: true
  changed_files_summary: false
  sequence_diagrams: false
  estimate_code_review_effort: false
  suggested_reviewers: false
  in_progress_fortune: false
  poem: false
  high_level_summary: true
  high_level_summary_instructions: "Give a brief description of the changes in 50 words or less."
  request_changes_workflow: false
  path_instructions:
    - path: "**/*"
      instructions: >
        - Restrict feedback to correctness bugs, security risks, and functionality-breaking problems.
        - Do not comment on style, formatting, naming, or non-critical improvements.
        - Limit review comments to 3-5 items unless additional merge blockers exist.
        - Group similar issues into a single comment instead of posting several.
        - If a pattern repeats, mention it once at summary level rather than per occurrence.
        - Avoid line-by-line commentary unless it flags a real bug or security hole.
        - If there are no critical problems, respond with a minimal approval and add nothing else.
  pre_merge_checks:
    docstrings: { mode: "off" }
    title: { mode: "off" }
    description: { mode: "off" }
    issue_assessment: { mode: "off" }
  finishing_touches:
    docstrings: { enabled: false }
    unit_tests: { enabled: false }
```

---

## Overlay B — Enforce organizational coding standards

```yaml
reviews:
  profile: chill
  pre_merge_checks:
    title:
      mode: warning
      requirements: "Follow Conventional Commits: https://www.conventionalcommits.org/en/v1.0.0/"
    description:
      mode: warning
  path_instructions:
    - path: "**/*"
      instructions: >
        - Apply the team's documented coding guidelines as review criteria.
        - Flag deviations from documented conventions, naming, and structure.
        - Cite the specific guideline when flagging a deviation.

knowledge_base:
  code_guidelines:
    enabled: true
    # Defaults already cover CLAUDE.md, AGENTS.md, .cursorrules, copilot-instructions.md, etc.
    # Run the thorough path to scope additional documents to specific directories.
```

---

## Overlay C — Maintain a high code quality bar

```yaml
reviews:
  profile: chill              # switch to `assertive` only on explicit request
  estimate_code_review_effort: true
  slop_detection:
    enabled: true
  path_instructions:
    - path: "**/*"
      instructions: >
        - Flag unintentional behavior changes.
        - Review correctness, security, reliability, performance, and functionality defects.
        - Keep comments brief and actionable.
        - Avoid style and subjective feedback unless it directly causes bugs.
  pre_merge_checks:
    title:
      mode: warning
    description:
      mode: warning
    issue_assessment:
      mode: warning
    custom_checks:
      - name: Performance and Algorithmic Complexity Review
        mode: warning
        instructions: >
          - Flag O(n^2) or worse behavior with non-trivial inputs in request handlers or loops
          - Flag N+1 query patterns requiring batching, joins, or set-based retrieval
          - Flag unbounded growth, memory leaks, retained listeners, accumulating buffers
          - Flag missing guardrails: pagination, size limits, timeouts, concurrency limits, backpressure
          - Flag expensive synchronous work that should be deferred, batched, or removed

tone_instructions: >
  - Indicate if code could cause a production outage
  - Explain the analysis chain behind each finding
```

---

## Overlay D — Agent-first

```yaml
tone_instructions: Prefer concise responses (high information density, low fluff).

reviews:
  enable_prompt_for_ai_agents: true
  collapse_walkthrough: true
  changed_files_summary: false
  sequence_diagrams: false
  in_progress_fortune: false
  poem: false
  high_level_summary: true
  high_level_summary_instructions: "Give a brief description of the changes in 50 words or less."
  finishing_touches:
    autofix: { enabled: true }
    simplify: { enabled: true }

chat:
  art: false
```

---

## Merge precedence

Apply in this order when two overlays set the same key:

1. **`profile`** — `quiet` (A) beats `chill` (B/C). If A is selected at all, the profile is `quiet`
   unless the user also picked C, in which case use `chill` and say you split the difference.
2. **`path_instructions`** — never emit two entries for the same `path`. Merge the bullet lists,
   dropping contradictions in favor of the more restrictive one (A's bullets beat C's).
3. **`pre_merge_checks` modes** — the stricter mode wins (`error` > `warning` > `off`), except that
   A alone means everything is `off`.
4. **Display keys** (`collapse_walkthrough`, `sequence_diagrams`, `changed_files_summary`, `poem`,
   `in_progress_fortune`, `chat.art`) — `false` wins over `true`.
5. **`tone_instructions`** — a single string, so pick one. D's concise instruction wins over C's if
   both are selected.

After merging, drop any key whose value equals the schema default (see `schema-reference.md`), except
where the value documents a deliberate choice the user made.

---

## What quickstart skips

Tell the user these were not configured, and that re-running the skill in **thorough** mode covers them:

- Coding-guideline documents outside the default patterns (Q2)
- Guideline documents in other repos (Q3)
- Noisy file-type exclusions (Q4)
- Explicit linked repositories (Q5)
- Walkthrough and summary detail (Q6)
- Custom policy gates (Q7)

Then give the Step 4 dashboard hand-off from `SKILL.md` — issue trackers and external context sources
are set up in the CodeRabbit UI and are not covered by either interview path.
