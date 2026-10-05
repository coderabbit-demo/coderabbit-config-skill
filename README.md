# CodeRabbit Config Builder

An agent skill that builds a `.coderabbit.yaml` by interviewing you about what you want out of code
review — then emitting only the keys your answers justify, instead of a wall of copy-pasted defaults.

## Quickstart

```bash
# 1. Install the skill
git clone https://github.com/coderabbit-demo/coderabbit-config-skill.git \
  ~/.claude/skills/coderabbit-config

# 2. Go to the repo you want to configure
cd ~/code/my-repo

# 3. Start your coding agent there, then invoke the skill
/coderabbit-config
```

Answer the questions; the skill writes and validates `.coderabbit.yaml` in that repo, then shows you
which answer produced each key.

Pass a mode to skip the first prompt:

```
/coderabbit-config quickstart    # one question, ~1 min
/coderabbit-config thorough      # seven questions + repo analysis, ~8 min
```

### Other harnesses

`SKILL.md` is plain Markdown and calls no vendor APIs. Step 1 above is the path for Claude Code — for
any other tool, clone into whatever directory it scans for skills; the layout doesn't change. If it
has no skill system, clone anywhere and ask your agent in plain language:

> Read `SKILL.md` in `./coderabbit-config-skill` and follow it to build a `.coderabbit.yaml` for this
> repository.

## What it asks

| # | Question | Primary keys |
|---|---|---|
| Q1 | What are you looking for in a review tool? | `reviews.profile`, `reviews.path_instructions` |
| Q2 | Coding-guideline docs in this repo | `knowledge_base.code_guidelines.filePatterns` (`applyTo` for scoping) |
| Q3 | Guideline docs in other repos | `knowledge_base.code_guidelines.filePatterns` (`repo:path`) |
| Q4 | File types that add noise to reviews | `reviews.path_filters` |
| Q5 | Other repos relevant to changes here | `knowledge_base.linked_repositories` |
| Q6 | What appears on the PR | `reviews.high_level_summary*`, `reviews.collapse_walkthrough`, `chat.art` |
| Q7 | Merge gates | `reviews.pre_merge_checks` |

Questions 2, 4, and 5 scan the repo *before* asking, so you're shown concrete findings — "here are the
14 `AGENTS.md` files we found, here are 909 Jest snapshots" — rather than an open-ended prompt.

It won't ask about Jira, Linear, Notion, or MCP. Those connect via OAuth in the CodeRabbit dashboard,
and the YAML defaults already permit reviews to use them — config keys there look meaningful and
change nothing.

## Validator

Runs standalone, no agent involved. Useful in CI or a pre-commit hook:

```bash
python3 scripts/validate_config.py .coderabbit.yaml
```

Reports **ERROR** (invalid — CodeRabbit rejects it) and **WARNING** (unknown key at that position, so
it parses but never takes effect). The warnings matter: most nested objects in the schema don't set
`additionalProperties: false`, so a misplaced key under `reviews:` fails silently rather than loudly.

Requires PyYAML. Exit codes: `0` clean, `1` errors, `2` could not run.

## Contents

```
SKILL.md                       the interview procedure
references/question-flow.md    wording, options, analysis, and YAML mapping per question
references/schema-reference.md key paths, enums, defaults, and the traps
references/baselines.md        quickstart base config plus four archetype overlays
references/examples/           enterprise and minimal reference configs
scripts/validate_config.py     schema validator
```

`references/schema-reference.md` is worth reading on its own — it documents the traps, including that
`path_filters` drives sparse-checkout (excluded files aren't cloned, so they can't serve as review
context) and that bare `off` parses as boolean `false`, so it must be quoted.

The `CLAUDE.md` / `.cursorrules` / `copilot-instructions.md` filenames throughout the references are
CodeRabbit's own default scan patterns, not a preference of this skill.

## Links

- [CodeRabbit configuration docs](https://docs.coderabbit.ai/getting-started/configure-coderabbit)
- [Schema](https://coderabbit.ai/integrations/schema.v2.json)
