# The Interview

Seven questions. Each section gives you: analysis to run first, the exact question to ask, the options,
and the YAML each answer maps to. Ask in order — later questions assume earlier answers.

Quickstart asks **Q1 only**. Thorough asks all seven.

**Out of scope: issue trackers and external data sources.** Do not ask about Jira, Linear, GitHub
Issues, Notion, Confluence, or MCP. Those are connected in the CodeRabbit dashboard — the YAML cannot
authenticate a tracker or register an MCP server, and the shipped defaults (`usage: auto`,
`web_search.enabled: true`) already let reviews use anything that is connected. Writing
`knowledge_base.jira`/`linear`/`issues`/`mcp` keys produces config that reads as meaningful and
changes nothing. Hand these off via **Step 4 — Dashboard hand-off** in `SKILL.md` instead.

The analysis commands below are `git ls-files` pipelines, so they only see tracked files — which is
what you want. A `grep` exit code of 1 means "no matches", not failure; report it as "nothing found"
and move on.

---

## Q1 — Review philosophy

**Ask (multi-select, up to 4):**

> **How would you define what you're looking for in a code review tool?** Select all that apply.
>
> - **Only flag the most critical issues** — silence on style and nits; comment only when something is unsafe to merge.
> - **Enforce organizational coding standards** — apply our written guidelines as review criteria.
> - **Maintain a high code quality bar** — thorough review including performance, security, and design.
> - **Agent-first** — an AI agent will apply the fixes, so optimize output for machine consumption.

**Mapping:**

<a id="critical-only"></a>
### Selected: Only flag the most critical issues
```yaml
reviews:
  profile: quiet
  collapse_walkthrough: true
  path_instructions:
    - path: "**/*"
      instructions: >
        - Restrict feedback to correctness bugs, security risks, and functionality-breaking problems.
        - Do not comment on style, formatting, naming, or non-critical improvements.
        - Limit review comments to 3-5 items unless additional merge blockers exist.
        - Group similar issues into one comment; if a pattern repeats, mention it once at summary level.
        - If there are no critical problems, respond with minimal approval and add nothing else.
```

<a id="standards"></a>
### Selected: Enforce organizational coding standards
```yaml
inheritance: true          # pick up org-level standards set by CodeRabbit admins
knowledge_base:
  code_guidelines:
    enabled: true          # filePatterns filled in by Q2 (this repo) and Q3 (other repos)
reviews:
  pre_merge_checks:
    title:
      mode: warning
    description:
      mode: warning
```

<a id="quality-bar"></a>
### Selected: Maintain a high code quality bar
```yaml
reviews:
  profile: chill           # use `assertive` only if the user explicitly wants nitpicks
  estimate_code_review_effort: true
  pre_merge_checks:
    custom_checks: []      # populated in Q7 from the catalog
  path_instructions:
    - path: "**/*"
      instructions: >
        - Flag unintentional behavior changes.
        - Review correctness, security, reliability, performance, and functionality defects.
        - Keep comments brief and actionable; avoid subjective style feedback unless it causes bugs.
```

<a id="agent-first"></a>
### Selected: Agent-first
```yaml
tone_instructions: Prefer concise responses (high information density, low fluff).
reviews:
  enable_prompt_for_ai_agents: true
  collapse_walkthrough: true
  poem: false
  in_progress_fortune: false
  finishing_touches:
    autofix:
      enabled: true
chat:
  art: false
```

**Conflicts.** If *critical-only* and *quality bar* are both selected, `profile: chill` wins and you
keep the critical-only `path_instructions`; tell the user you split the difference and how to shift it.
If *critical-only* and *agent-first* are both selected, they reinforce — take the union.

---

## Q2 — Coding-guideline documents in this repo

**Analyze first.** Find candidate guideline docs:

```bash
git ls-files | grep -Ei '(^|/)(CLAUDE|AGENTS?|GEMINI|REVIEW|CONTRIBUTING|STYLEGUIDE|STYLE_GUIDE|CODING_STANDARDS|CONVENTIONS|ARCHITECTURE)\.(md|mdc)$|\.cursorrules$|\.windsurfrules$|(^|/)\.(cursor|clinerules|rules)/'
git ls-files '*.md' | grep -Ei '(docs|guidelines|standards|engineering)/' | head -40
```

Sort the hits into two buckets using the default-pattern list in `schema-reference.md`:

- **Already auto-applied** — matches a CodeRabbit default pattern (`**/AGENTS.md`, `**/AGENT.md`,
  `**/CLAUDE.md`, `**/GEMINI.md`, `.github/copilot-instructions.md`,
  `.github/instructions/*.instructions.md`, `**/.cursorrules`, `**/.cursor/rules/*`,
  `**/.windsurfrules`, `**/.clinerules/*`, `**/.rules/*`). Matching is **case-sensitive** — a
  `claude.md` or `Agents.md` is *not* auto-applied; put it in the second bucket.
- **Not currently applied** — everything else you found.

For the first bucket, note where each file sits: a default-pattern file applies to **its own directory
and everything below it**, so `src/frontend/CLAUDE.md` already only governs `src/frontend/**`. Nothing
to configure for those.

**Ask** (show both bucket lists first, with file paths):

> We scanned the repo for coding-guideline documents.
>
> **Already applied by default** (each to its own directory and below): `<list>`
> **Found but not currently applied:** `<list>`
>
> **How should we handle the unapplied documents?**
>
> - **Apply them globally** — use them as review criteria for every file.
> - **Scope them to specific paths** — e.g. the backend guide only applies to `services/**`.
> - **Don't apply them** — they're not review criteria.

If the user picks *scope*, ask a follow-up per document (or propose a mapping and let them correct it):
which files should this document govern? Infer a sensible default from the document's name and
contents — `docs/frontend.md` → `src/frontend/**/*.{js,jsx,ts,tsx}` — and confirm it.

**Mapping.** `filePatterns` entries come in two forms, and both work:

- **Plain string** — a glob for the guideline documents. Applies to the directory the document lives in
  and below; a document at the repo root (or in `docs/`, which is outside the source tree) therefore
  needs an `applyTo` if it should only govern part of the code.
- **Object `{files, applyTo}`** — `files` is the guideline document(s), `applyTo` is the glob of source
  files they govern. Use this for any guideline stored away from the code it describes.

`filePatterns` **extends** the defaults; it never replaces them. List only the *new* documents —
restating `**/CLAUDE.md` and friends adds nothing.

Apply globally — plain strings, new documents only:
```yaml
knowledge_base:
  code_guidelines:
    enabled: true
    filePatterns:
      - "**/CODING_STANDARDS.md"
      - "docs/engineering-standards.md"
```

Scope to paths — object form with `applyTo`:
```yaml
knowledge_base:
  code_guidelines:
    enabled: true
    filePatterns:
      - files: "docs/guidelines/backend.md"
        applyTo: "{services,packages/api}/**"
      - files: "docs/guidelines/frontend.md"
        applyTo: "src/frontend/**/*.{js,jsx,ts,tsx}"
```

Mixing both forms in one list is fine. Do **not** also restate the scoping in
`reviews.path_instructions` — `applyTo` is the mechanism; a duplicate path instruction only adds noise.

Don't apply: omit `filePatterns` entirely (defaults stay active). If the user wants guidelines off
completely, set `knowledge_base.code_guidelines.enabled: false`. Individual auto-detected files can
also be disabled in the CodeRabbit UI without deleting them — mention this if the user wants to drop
one default-pattern file but keep the rest.

**Constraints** (see `schema-reference.md` for the full list): only text/documentation files are
eligible (`.md`, `.mdc`, `.yaml`, `.txt`, …) — never point `files` at source code; each entry ≤ 512
characters; repo-relative paths only (no leading `/`, no `..`, no backslashes); at most 50 files are
expanded from globs per review, so prefer specific paths over broad globs like `**/*.md`.

---

## Q3 — Guideline documents in other repositories

Guidelines in another repo are pulled in through **`code_guidelines.filePatterns`** using
`repo:path` (same organization) or `owner/repo:path` syntax — *not* through `linked_repositories`.
`linked_repositories` (Q5) gives the reviewer cross-repo code context; it does not make another repo's
documents into review criteria.

**Ask:**

> **Are there coding-standards documents in *other* repositories that should inform reviews here?**
> For example a central `engineering-standards` or `platform-standards` repo.
> List the repo and, if you know them, the document paths (or leave blank for none).

**Analyze, if you can.** When the user names a repo but not paths, and `gh` is authenticated, list
candidate documents rather than guessing:

```bash
gh api "repos/<owner>/<repo>/git/trees/HEAD?recursive=1" --jq '.tree[] | select(.type=="blob") | .path' \
  | grep -Ei '\.(md|mdc|txt|ya?ml)$' | head -60
```

Show what you found and ask which documents apply, and to which files in *this* repo — e.g.
`python/**/*.md` → `**/*.py`, `frontend/react.md` → `src/**/*.{tsx,jsx}`. A cross-repo document with
no `applyTo` governs this whole repo; use that only for genuinely org-wide standards. If you can't list
the repo, write the paths the user gives you and tell them to double-check them.

**Mapping** — add to the same `filePatterns` list as Q2:
```yaml
knowledge_base:
  code_guidelines:
    enabled: true
    filePatterns:
      - "engineering-standards:general/code-review.md"        # org-wide, whole repo
      - files: "engineering-standards:python/**/*.md"
        applyTo: "**/*.py"
      - files: "acme/platform-standards:frontend/react.md"     # owner/repo form
        applyTo: "src/frontend/**/*.{js,jsx,ts,tsx}"
```

Use the short `repo:path` form when the repo shares this repo's owner; use `owner/repo:path`
otherwise or when in doubt.

Tell the user:
- The source repo must be in the same GitHub organization (GitLab top-level group / Bitbucket Cloud
  workspace) and accessible to the CodeRabbit installation; otherwise the entry is inert.
- Max 50 cross-repository entries per repo, and the 50-files-per-review glob cap applies here too.
- To try a guideline on a single PR before committing it to config, they can put a
  `@coderabbitai configuration override` block in the PR description with the same
  `knowledge_base.code_guidelines.filePatterns` entry (PR author must be a repo collaborator).

If the user *also* wants the reviewer to see that repo's code (not just its documents), add it in Q5
as well.

---

## Q4 — Noisy file types

**Analyze first.** Find generated, vendored, and lockfile-style content that inflates diffs:

```bash
git ls-files | sed -n 's/.*\.\([A-Za-z0-9_]*\)$/\1/p' | sort | uniq -c | sort -rn | head -30
git ls-files | grep -Ei '(^|/)(dist|build|out|vendor|node_modules|target|\.next|coverage|__snapshots__|migrations|generated|gen)/|\.(lock|snap|min\.js|min\.css|map|pb\.go|g\.dart|generated\.ts|pyc|svg|png|jpg|jpeg|gif|ico|woff2?)$|(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|Gemfile\.lock|go\.sum|Cargo\.lock)$' | head -40
```

Group the hits into named categories (lockfiles, build output, snapshots, generated clients, binary
assets, vendored code) with a file count each.

**Ask** (show the categories and counts):

> Based on your repository, these are common but probably not worth reviewing:
>
> `<category — N files — example path>`
>
> **Exclude them from reviews?**
>
> - **Exclude all of them** — cleanest diffs.
> - **Let me pick** — walk through category by category.
> - **Exclude none** — review everything.

**Mapping.** Exclusions are `!`-prefixed glob patterns:
```yaml
reviews:
  path_filters:
    - "!**/*.lock"
    - "!**/package-lock.json"
    - "!**/pnpm-lock.yaml"
    - "!**/dist/**"
    - "!**/__snapshots__/**"
    - "!**/*.min.js"
    - "!**/generated/**"
```

**Warn the user about two things:**
- `path_filters` also drives sparse-checkout, so excluded files aren't cloned. Don't exclude a directory
  the reviewer needs as *context* (e.g. a schema dir) just because you don't want comments on it — use
  `path_instructions` telling the reviewer to stay quiet there instead.
- Migrations are excluded by many teams and are exactly where breaking changes hide. Recommend keeping
  them in review unless the user is sure.

---

## Q5 — Related repositories

**Analyze first.** Look for cross-repo coupling to suggest candidates: API client packages in manifest
files (`package.json`, `go.mod`, `requirements.txt`, `pom.xml`), submodules in `.gitmodules`, repo URLs
in CI workflows, and `owner/repo` mentions in the README.

**Ask** (lead with any candidates you found):

> **Which other repositories are relevant to changes made here?**
> CodeRabbit uses these to catch breaking changes across service boundaries — e.g. a backend repo whose
> API this client consumes, or a shared types package.
> `<candidates found>`
> List as `owner/repo`, or say none.

**Mapping:**
```yaml
knowledge_base:
  automatic_repository_linking: true    # let CodeRabbit infer links too
  linked_repositories:
    - repository: myorg/backend-api
      instructions: >
        This repo consumes the backend-api HTTP contract. Flag changes here that
        depend on endpoints or response shapes not present in backend-api.
```

Max 20 entries. Format is `owner/repo` (Azure DevOps uses `Project/repo`).

---

## Q6 — What appears on the PR

Three sub-questions. Ask them in sequence.

### Q6a — Summary

> **Do you want a high-level summary comment on each PR?**
> ([example](https://github.com/coderabbit-demo/starter-config-resource))
>
> - **Yes, as its own section**
> - **Yes, but fold it into the walkthrough comment**
> - **No summary**

```yaml
reviews:
  high_level_summary: true                # false for "No summary"
  high_level_summary_in_walkthrough: false # true for "fold into walkthrough"
```

### Q6b — Summary style (only if Q6a was yes)

> **What should the summary contain?**
>
> - **Brief** — a description of the changes in 50 words or less.
> - **Risk-scored** — a merge-confidence score of 1-5 (5 = very safe), then a brief description.
> - **Detailed** — a full breakdown of the changes made.

```yaml
# Brief
reviews:
  high_level_summary_instructions: "Give a brief description of the changes in 50 words or less."

# Risk-scored
reviews:
  high_level_summary_instructions: >
    Begin with `Merge Confidence: <score>/5`, where 5 is very safe and 1 is very risky.
    Base the score on potential impact — not diff size — including correctness, security,
    operational risk, architectural scope, dependency changes, and rollback complexity.
    Follow with a brief description of the changes.

# Detailed
reviews:
  high_level_summary_instructions: "Give a detailed breakdown of the changes made, grouped by area of the codebase."
```

### Q6c — Walkthrough

> **The walkthrough is a per-file breakdown posted with each review. How should it appear?**
>
> - **Collapsed** — keep it out of the way; I want to focus on the review comments.
> - **Expanded** — I want the details visible every time.

```yaml
reviews:
  collapse_walkthrough: true   # false for expanded
```

**If expanded**, ask which extras to include (multi-select):

> **Which walkthrough sections do you want?**
>
> - **Sequence diagrams** — Mermaid diagrams of changed control flow.
> - **Changed files summary** — table of every file with a one-line description.
> - **Review effort estimate** — a complexity/effort rating for the PR.
> - **Poem** — CodeRabbit closes the walkthrough with a poem.

```yaml
reviews:
  sequence_diagrams: true          # default true
  changed_files_summary: true      # default true
  estimate_code_review_effort: true # default true
  poem: true                       # default false
```
Set unselected ones to `false` explicitly, since three of the four default to `true`.

### Q6d — Fun

> **Keep CodeRabbit's playful touches (ASCII art in chat replies, fortunes on in-progress reviews)?**
>
> - **Keep them on**
> - **Turn them off**

```yaml
# Turn them off
reviews:
  in_progress_fortune: false
  poem: false
chat:
  art: false
```
Keeping them on requires no keys (all are on by default except `poem`).

---

## Q7 — Merge gates

Pre-merge checks are *gates*, not display settings — they post a pass/fail status on the PR. `warning`
surfaces the issue without blocking; `error` marks the check failed.

**Ask:**

> **Should CodeRabbit gate merges on anything?**
>
> - **No gates** — review comments only.
> - **Hygiene gates** — PR title and description quality, linked-issue coverage.
> - **Hygiene plus custom policy checks** — add org-specific rules (security, privacy, performance).

```yaml
# No gates
reviews:
  pre_merge_checks:
    title: { mode: "off" }
    description: { mode: "off" }
    docstrings: { mode: "off" }
    issue_assessment: { mode: "off" }

# Hygiene gates
reviews:
  pre_merge_checks:
    title:
      mode: warning
      requirements: "Follow Conventional Commits: https://www.conventionalcommits.org/en/v1.0.0/"
    description:
      mode: warning
    issue_assessment:
      mode: warning
    docstrings:
      mode: "off"
```

**If custom policy checks**, offer the catalog (multi-select) and copy the full instruction blocks from
`examples/enterprise.coderabbit.yaml`:

> **Which policy checks do you want?**
>
> - **Sensitive data & privacy** — flags PII, credentials, and confidential-data exposure.
> - **Security, audit & regulatory controls** — SOC 2 / ISO 27001 / PCI DSS / HIPAA / GDPR control integrity.
> - **Performance & algorithmic complexity** — N+1 queries, O(n²) hot paths, unbounded growth.
> - **Something else** — draft a custom check from the user's description.

```yaml
reviews:
  pre_merge_checks:
    custom_checks:
      - name: Sensitive Data Protection and Privacy
        mode: error
        instructions: >
          - Flag exposure of PII, credentials, trade secrets, or confidential company assets
          - ...
```

Recommend starting every custom check at `mode: warning` and promoting to `error` after a week of
observing false-positive rates. Say so when you write them.

---

## After Q7 — hand off, don't ask

The interview ends at Q7. Issue trackers (Jira, Linear, GitHub/GitLab Issues) and external context
sources (Notion, Confluence, MCP servers, web search) are **not** interview questions — they are
dashboard setup. Do not write `knowledge_base.jira`, `knowledge_base.linear`, `knowledge_base.issues`,
or `knowledge_base.mcp` keys on the strength of an interview answer.

Why: those keys gate *permission*, not *connection*. Their defaults (`usage: auto`) already permit
reviews to use any source the org has connected, and no YAML value can perform the OAuth handshake or
register an MCP server. A config full of `usage: enabled` keys looks like it did something and did not.

Deliver the hand-off text in **Step 4** of `SKILL.md` instead, trimmed to what the repo actually needs.

The one exception is *disabling*. If the user explicitly asks to seal reviews off from everything
outside the repository, that is a real YAML change:

```yaml
knowledge_base:
  web_search:
    enabled: false
  mcp:
    usage: disabled
```

Write that only on an explicit request, never as a default.
