# CodeRabbit Config Builder

An agent skill that generates a `.coderabbit.yaml` for a repository through a guided interview.

Most CodeRabbit configs start as a copy-pasted wall of keys that nobody can justify six months later.
This skill takes the opposite approach: it asks what you actually want out of code review, analyzes
the repository for evidence, and emits only the keys those answers require. Schema defaults are
omitted, because a short config is a maintainable config.

**It is plain Markdown and portable.** `SKILL.md` is a procedure written for a coding agent, not a
plugin for one particular tool. It calls no harness-specific APIs — the only executable in the repo is
a standalone Python validator. Any agent that can read files, run `git ls-files`, and ask you a
question can follow it.

## Install

Clone it wherever you keep agent instructions:

```bash
git clone https://github.com/coderabbit-demo/coderabbit-config-skill.git
```

**If your harness auto-discovers skills**, put the directory where it looks. The format here is the
`SKILL.md`-plus-frontmatter convention (a `name` and `description` in YAML frontmatter, supporting
files alongside it), so a harness that supports skills at all can usually pick it up as-is. Claude
Code, for example, reads `~/.claude/skills/<name>/` for personal skills and `.claude/skills/<name>/`
for project-scoped ones:

```bash
git clone https://github.com/coderabbit-demo/coderabbit-config-skill.git \
  ~/.claude/skills/coderabbit-config
```

Check your own tool's docs for the equivalent location — the directory name and layout don't need to
change, only where it lives.

**If your harness has no skill system**, skip the install entirely. Clone the repo and point your
agent at it:

> Read `SKILL.md` in `./coderabbit-config-skill` and follow it to build a `.coderabbit.yaml` for this
> repository.

That works in any chat-based coding agent, and it's also the fallback if auto-discovery misfires.

## Use

Invoke it however your harness invokes skills — a slash command, an `@`-mention, or just asking in
plain language:

> Set up a CodeRabbit config for this repo.

You can name a mode up front, or let the skill ask:

| Mode | Time | What it does |
|---|---|---|
| **Quickstart** | ~1 min | One question. Applies an opinionated baseline plus one overlay per archetype you pick. |
| **Thorough** | ~8 min | Seven questions plus repo analysis. Produces a config tuned to the codebase in front of it. |

## The interview

| # | Question | Primary keys |
|---|---|---|
| Q1 | What are you looking for in a review tool? | `reviews.profile`, `reviews.path_instructions` |
| Q2 | Coding-guideline docs in this repo | `knowledge_base.code_guidelines` |
| Q3 | Guideline docs in other repos | `knowledge_base.linked_repositories` |
| Q4 | File types that add noise to reviews | `reviews.path_filters` |
| Q5 | Other repos relevant to changes here | `knowledge_base.linked_repositories` |
| Q6 | What appears on the PR | `reviews.high_level_summary*`, `reviews.collapse_walkthrough`, `chat.art` |
| Q7 | Merge gates | `reviews.pre_merge_checks` |

Questions 2, 4, and 5 run repository analysis *before* asking, so you're shown concrete findings —
"here are the 14 `AGENTS.md` files we found, here are 909 Jest snapshots" — rather than an open-ended
prompt. The analysis is `git ls-files` pipelines, nothing exotic.

Every question fits in four options, so agents with a structured multiple-choice prompt can use one;
the rest fall back to a numbered list. Both paths are specified in `references/question-flow.md`.

After writing the file, the skill validates it and reports a decision log: every key it emitted, and
the answer that produced it.

## What it deliberately does not ask

Jira, Linear, Confluence, Notion, and MCP servers are **dashboard** concerns, not config concerns.
Connecting them is an OAuth handshake that YAML cannot perform, and the shipped defaults
(`usage: auto`) already permit reviews to use whatever your org has connected. Writing
`knowledge_base.jira` or `knowledge_base.mcp` keys on the strength of an interview answer produces
config that reads as meaningful and changes nothing.

So the skill hands those off at the end with a pointer to
[the integrations docs](https://docs.coderabbit.ai/integrations/) instead. The one exception is
*disabling* — sealing reviews off from external context is a real YAML change, and the skill will
write it if you explicitly ask.

## Contents

```
SKILL.md                                  the interview procedure
references/question-flow.md               exact wording, options, analysis, and YAML mapping per question
references/schema-reference.md            key paths, enums, defaults, and the traps
references/baselines.md                   quickstart base config plus four archetype overlays
references/examples/enterprise...yaml     governance-heavy reference config
references/examples/minimal...yaml        signal-only reference config
scripts/validate_config.py                validates a config against the live schema
```

The frontmatter in `SKILL.md` carries two optional keys (`argument-hint`, `user-invocable`) that some
harnesses read and others ignore as unknown fields. `name` and `description` are the portable pair.

## Validator

The validator is a dependency-light Python script with no agent involved. Run it in CI, in a
pre-commit hook, or by hand:

```bash
python3 scripts/validate_config.py .coderabbit.yaml
python3 scripts/validate_config.py .coderabbit.yaml --refresh   # re-fetch the schema
```

It reports two classes of problem:

- **ERROR** — the config is invalid and CodeRabbit will reject it.
- **WARNING** — the key is unknown at that position, so it parses but never takes effect.

That second class matters more than it sounds. Nested objects in the CodeRabbit schema mostly don't
set `additionalProperties: false`, so a misplaced key under `reviews:` won't fail validation — it just
silently does nothing.

Requires PyYAML (`pip install pyyaml`). Exit codes: `0` clean, `1` errors, `2` could not run.

## Schema traps worth knowing

These caught us, and they're documented in full in `references/schema-reference.md`:

- **The root rejects unknown keys.** Only ten keys are valid at the top level. `profile`,
  `path_filters`, `pre_merge_checks`, and `code_guidelines` are *not* among them — they all nest.
- **`path_filters` drives sparse-checkout.** Excluded paths aren't cloned, so they can't serve as
  review *context* either. Don't exclude a schema directory just because you don't want comments on it.
- **`code_guidelines.filePatterns` extends the defaults rather than replacing them**, and object-form
  `{files, applyTo}` entries validate cleanly and are then dropped at runtime. Write plain strings and
  express scoping through `reviews.path_instructions`.
- **YAML parses bare `off` as boolean `false`.** Always quote it: `mode: "off"`.
- **Three walkthrough extras default to `true`** (`sequence_diagrams`, `changed_files_summary`,
  `estimate_code_review_effort`). Omitting them keeps them on; you have to write `false`.

Note that CodeRabbit scans a fixed set of agent-instruction files by default — `AGENTS.md`,
`CLAUDE.md`, `GEMINI.md`, `.cursorrules`, `.windsurfrules`, `.clinerules/`, and
`.github/copilot-instructions.md` among them. Those filenames appear throughout this repo because
they are CodeRabbit's defaults, not because the skill favors any particular agent.

## Links

- [CodeRabbit configuration docs](https://docs.coderabbit.ai/getting-started/configure-coderabbit)
- [Schema](https://coderabbit.ai/integrations/schema.v2.json)
