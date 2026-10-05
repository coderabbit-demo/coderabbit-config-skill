---
name: coderabbit-config
description: Interactively generate a .coderabbit.yaml for this repository. Walks the user through a guided interview (quickstart or thorough), analyzes the repo for coding-guideline docs and noisy file types, and writes a schema-valid config. Use when a user asks to set up, create, tune, or review their CodeRabbit configuration.
# Optional keys below are read by some harnesses and ignored by the rest.
argument-hint: "[quickstart|thorough]"
user-invocable: true
---

# CodeRabbit Config Builder

Generate a `.coderabbit.yaml` for the current repository through a guided interview.

Your job is to **ask, analyze, then write** — never to dump a giant default config and call it done.
Every key you emit must be justified by an answer the user gave or by evidence you found in the repo.

## Ground rules

1. **Schema is authoritative.** Read `references/schema-reference.md` before emitting YAML. Root-level
   `additionalProperties` is `false` — a misplaced key fails the whole config. Most review settings live
   under `reviews:`, most context settings under `knowledge_base:`.
2. **One question at a time.** If your harness has a structured multiple-choice prompt, use it — every
   question below fits within four options. Otherwise present a numbered list and wait for a reply.
   Never batch the whole interview into one message.
3. **Analyze before asking.** Questions 2, 4, and 5 depend on repo analysis. Do that work *first* so you
   can show the user concrete findings instead of an open-ended prompt.
4. **Omit defaults.** If an answer matches the schema default, don't write the key. A short config is a
   maintainable config. Exception: keys the user explicitly discussed are worth stating for clarity.
5. **Never overwrite silently.** If `.coderabbit.yaml` already exists, read it, show the diff you intend
   to make, and get confirmation.
6. **Explain the output.** After writing, give a short table of each setting and the answer that produced it.

## Step 0 — Pick a mode

If the user supplied a mode — as an invocation argument (`$ARGUMENTS`, where your harness substitutes
it) or anywhere in their message — use it. Otherwise ask:

> **How much setup do you want to do right now?**
> - **Quickstart** — one question, ~1 minute. Produces a solid, opinionated config you can grow into.
> - **Thorough** — seven questions plus repo analysis, ~8 minutes. Produces a config tuned to this codebase.

## Step 1 — Quickstart path

Ask **Q1** only (see `references/question-flow.md`), then build the config from
`references/baselines.md`: start from the base, apply one overlay per selected archetype, resolve
conflicts with the documented precedence rules.

Then jump to **Step 3 — Write and verify**. Tell the user which questions they skipped and that
re-running with `thorough` will cover them.

## Step 2 — Thorough path

Run the full interview in `references/question-flow.md`. It defines, for each question: the exact
wording, the options, the repo analysis to run first, and the YAML each answer maps to.

| # | Question | Primary keys |
|---|---|---|
| Q1 | What are you looking for in a review tool? | `reviews.profile`, `reviews.path_instructions` |
| Q2 | Existing coding-guideline docs in this repo | `knowledge_base.code_guidelines.filePatterns` (`applyTo` for scoping) |
| Q3 | Guideline docs living in other repos | `knowledge_base.code_guidelines.filePatterns` (`repo:path`) |
| Q4 | File types that add noise to reviews | `reviews.path_filters` |
| Q5 | Other repos relevant to changes here | `knowledge_base.linked_repositories` |
| Q6 | What appears on the PR (summary / walkthrough / fun) | `reviews.high_level_summary*`, `reviews.collapse_walkthrough`, `chat.art` |
| Q7 | Merge gates | `reviews.pre_merge_checks` |

Q2 and Q3 both write to `knowledge_base.code_guidelines.filePatterns` — merge them into one list.
Use the object form `{files, applyTo}` whenever a document should govern only part of the repo, and
`repo:path` / `owner/repo:path` for documents that live in another repository. Q3 does **not** write
`linked_repositories`; that key (Q5) is for cross-repo code context, capped at 20 entries.

**Do not ask about issue trackers or external data sources.** Jira, Linear, Confluence, Notion, and
MCP servers are dashboard concerns, not config concerns — connecting them is an authentication step
the YAML cannot perform, and the YAML defaults (`usage: auto`) already let reviews use whatever is
connected. Asking produces keys that look meaningful but change nothing. Instead, close the interview
with the dashboard hand-off in Step 4.

Carry a running decision log as you go: `answer → key → value`. You will need it for Step 3.

## Step 3 — Write and verify

1. Write `.coderabbit.yaml` at the repo root. First line must be:
   `# yaml-language-server: $schema=https://coderabbit.ai/integrations/schema.v2.json`
2. Group keys with section comments in this order: top-level (`tone_instructions`, `inheritance`),
   `reviews:`, `chat:`, `knowledge_base:`, `code_generation:`.
3. Validate: `python3 <skill-dir>/scripts/validate_config.py .coderabbit.yaml`. Fix every ERROR, and
   treat every WARNING as a misplaced key until proven otherwise.
   If the script can't run (no PyYAML), self-check every key you emitted against
   `references/schema-reference.md` and say that you did the check manually.
4. Make sure `reviews.review_details: true` is in the file — every config this skill writes enables it
   (the schema default is `false`). If you are tuning an existing `.coderabbit.yaml` and it already
   has `review_details: true`, leave it; if the key is missing or `false`, set it to `true` and list
   that change in the decision log. Only write `false` if the user explicitly asks to turn it off.
5. Present the decision log as a table, then offer: *"Want to change any of these?"*

## Step 4 — Dashboard hand-off

Close every run — quickstart and thorough — by telling the user what the YAML *cannot* do. Keep it to
the items that apply to their repo; don't recite the whole list.

> **Set these up in the CodeRabbit dashboard, not in this file:**
>
> - **Issue trackers** — Jira and Linear need OAuth. Integrations → Jira / Linear. Once connected,
>   reviews use them automatically; the YAML default (`usage: auto`) already permits it.
> - **Docs and knowledge sources** — Notion, Confluence, and internal MCP servers connect at
>   Integrations → MCP. The YAML has no way to register a server or hold a credential.
> - **Org-level base config** — set once by a CodeRabbit admin and inherited by every repo. This
>   config sets `inheritance: true` if you asked for organizational standards.
> - **Repository access** — linked repositories only work if the CodeRabbit app is installed on them.
>   An uninstalled repo links silently and does nothing.
>
> Docs: https://docs.coderabbit.ai/integrations/

If the user asks to disable one of these sources rather than connect it, that *is* a YAML change —
`knowledge_base.mcp.usage: disabled` or `knowledge_base.web_search.enabled: false`. Write it only when
they explicitly ask to seal reviews off from external context.

## Bundled files

- `references/question-flow.md` — the full interview: wording, options, analysis, YAML mapping
- `references/schema-reference.md` — key paths, enums, defaults, and the traps
- `references/baselines.md` — quickstart base config plus the four archetype overlays
- `references/examples/enterprise.coderabbit.yaml` — governance-heavy reference config
- `references/examples/minimal.coderabbit.yaml` — signal-only reference config
- `scripts/validate_config.py` — validates a config against the live schema
