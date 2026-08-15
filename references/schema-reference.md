# CodeRabbit Schema v2 Reference

Authoritative source: `https://coderabbit.ai/integrations/schema.v2.json`
(fetched and flattened for this skill — re-fetch if a key here looks stale).

Always start the generated file with:
```yaml
# yaml-language-server: $schema=https://coderabbit.ai/integrations/schema.v2.json
```

---

## Traps — read these before writing YAML

1. **Root rejects unknown keys.** The root schema is `additionalProperties: false`. Only these ten
   keys are valid at the top level:
   `language`, `tone_instructions`, `early_access`, `enable_free_tier`, `inheritance`, `reviews`,
   `chat`, `knowledge_base`, `code_generation`, `issue_enrichment`.
   Everything else nests. Common mistakes — these are **not** root keys:
   `profile`, `path_instructions`, `path_filters`, `pre_merge_checks`, `custom_checks`, `auto_review`,
   `high_level_summary`, `sequence_diagrams`, `collapse_walkthrough`, `poem`, `commit_status`,
   `suggested_reviewers`, `slop_detection`, `code_guidelines`, `request_changes_workflow`.

2. **Misplaced keys inside a section are silently ignored.** Nested objects mostly don't set
   `additionalProperties: false`, so a typo under `reviews:` won't error — it just never takes effect.
   Check every key against the index below rather than trusting a clean validation run.

3. **`custom_checks` lives under `reviews.pre_merge_checks`**, not at root and not directly under
   `reviews`.

4. **`code_guidelines` lives under `knowledge_base`**, not at root.

5. **`filePatterns` *extends* the defaults — it does not replace them**, and **object-form
   `{files, applyTo}` entries are silently dropped.** The schema accepts the object form
   (`files` and `applyTo` are both `z.string()`, documented as comma-separated globs), but the
   reviewer filters the array with `.filter(p => typeof p === "string")` and then concatenates
   `DEFAULT_GUIDELINE_FILE_PATTERNS`. Net effect: restated defaults are duplicates, and any scoped
   entry never gets indexed. Write plain strings and express scoping through
   `reviews.path_instructions`. See Q2 in `question-flow.md` for the pattern and the verification
   command.

6. **`path_filters` drives sparse-checkout.** Excluded paths aren't cloned, so they can't be used as
   review context either.

7. **Three walkthrough extras default to `true`** (`sequence_diagrams`, `changed_files_summary`,
   `estimate_code_review_effort`). To omit them you must write `false` explicitly.

8. **Quoting `off`.** YAML parses bare `off` as boolean false. Always write `mode: "off"`.

---

## Key index

Format: `key [type] default — notes`

### Root
```
language              [string]  "en-US"   — LanguageTool locale
tone_instructions     [string]  ""        — global voice/persona for all output
early_access          [bool]    false
enable_free_tier      [bool]    true
inheritance           [bool]    false     — inherit org-level config from CodeRabbit admins
reviews               [object]
chat                  [object]
knowledge_base        [object]
code_generation       [object]
issue_enrichment      [object]
```

### `reviews`
```
profile                          [string]  "chill"  — enum: quiet | chill | assertive
request_changes_workflow         [bool]    false
high_level_summary               [bool]    true
high_level_summary_instructions  [string]  ""
high_level_summary_placeholder   [string]  "@coderabbitai summary"
high_level_summary_in_walkthrough[bool]    false
auto_title_placeholder           [string]  "@coderabbitai"
auto_title_instructions          [string]  ""
review_status                    [bool]    true
review_details                   [bool]    false
review_progress                  [bool]    true
commit_status                    [bool]    true   — false stops CodeRabbit posting a commit status
fail_commit_status               [bool]    false
collapse_walkthrough             [bool]    true
changed_files_summary            [bool]    true
sequence_diagrams                [bool]    true
estimate_code_review_effort      [bool]    true
assess_linked_issues             [bool]    true
related_issues                   [bool]    true
related_prs                      [bool]    true
suggested_labels                 [bool]    true
auto_apply_labels                [bool]    false
labeling_instructions            [array]   []     — items: {label, instructions}
mutually_exclusive_groups        [object]  {}
suggested_reviewers              [bool]    true
auto_assign_reviewers            [bool]    false
suggested_reviewers_instructions [array]   []     — items: {reviewers:[{handle,type}], instructions}
in_progress_fortune              [bool]    true
poem                             [bool]    false
enable_prompt_for_ai_agents      [bool]    true
path_filters                     [array]   []     — glob strings; `!` prefix excludes
path_instructions                [array]   []     — items: {path, instructions}
abort_on_close                   [bool]    true
disable_cache                    [bool]    false
slop_detection.enabled           [bool]    true
slop_detection.label             [string]
auto_review.enabled              [bool]    true
auto_review.description_keyword  [string]  ""
auto_review.auto_incremental_review        [bool] true
auto_review.auto_pause_after_reviewed_commits [int] 5
auto_review.ignore_title_keywords[array]   []
auto_review.labels               [array]   []
auto_review.drafts               [bool]    false
auto_review.base_branches        [array]   []     — regex strings, e.g. [".*"] for all branches
auto_review.ignore_usernames     [array]   []
finishing_touches.docstrings.enabled       [bool] true
finishing_touches.unit_tests.enabled       [bool] true
finishing_touches.simplify.enabled         [bool] false
finishing_touches.autofix.enabled          [bool] true
finishing_touches.fix_ci.enabled           [bool] true
finishing_touches.resolve_merge_conflict.enabled [bool] true
finishing_touches.custom         [array]   []     — items: {enabled, name, instructions}
pre_merge_checks.override_requested_reviewers_only [bool] false
pre_merge_checks.docstrings.mode [string]  "warning" — enum: off | warning | error
pre_merge_checks.docstrings.threshold      [number] 80
pre_merge_checks.title.mode      [string]  "warning"
pre_merge_checks.title.requirements        [string] ""
pre_merge_checks.description.mode[string]  "warning"
pre_merge_checks.issue_assessment.mode     [string] "warning"
pre_merge_checks.custom_checks   [array]   []     — items: {name, mode, instructions}
post_merge_actions               [array]   []     — items: {enabled, name, prompt}
tools.<tool>.enabled             [bool]           — see tool list below
```

### `chat`
```
chat.art                         [bool]    true
chat.allow_non_org_members       [bool]    true
chat.auto_reply                  [bool]    true
chat.integrations.jira.usage     [string]  "auto"  — enum: auto | enabled | disabled
chat.integrations.linear.usage   [string]  "auto"
```

### `knowledge_base`
```
opt_out                          [bool]    false  — true disables the whole knowledge base
web_search.enabled               [bool]    true
code_guidelines.enabled          [bool]    true
code_guidelines.filePatterns     [array]   []     — string globs; ADDED to the defaults, not
                                                    substituted. {files, applyTo} objects validate
                                                    but are dropped at runtime — see trap 5.
learnings.scope                  [string]  "auto" — enum: local | global | auto
learnings.approval_delay         [int]     0
issues.scope                     [string]  "auto"
jira.usage                       [string]  "auto"
jira.project_keys                [array]   []
jira.excluded_project_keys       [array]   []
linear.usage                     [string]  "auto"
linear.team_keys                 [array]   []
pull_requests.scope              [string]  "auto"
mcp.usage                        [string]  "auto" — 'auto' disables MCP on public repos
mcp.disabled_servers             [array]
automatic_repository_linking     [bool]    false
linked_repositories              [array]   []     — max 20; items: {repository, instructions}
```

### `code_generation`
```
docstrings.language              [string]  "en-US"
docstrings.path_instructions     [array]   []     — items: {path, instructions}
unit_tests.path_instructions     [array]   []     — items: {path, instructions}
```

### `issue_enrichment`
```
auto_enrich.enabled              [bool]    false
planning.enabled                 [bool]    true
planning.auto_planning.enabled   [bool]    true
planning.auto_planning.labels    [array]   []
labeling.labeling_instructions   [array]   []     — items: {label, instructions}
labeling.auto_apply_labels       [bool]    false
```

---

## Default `code_guidelines.filePatterns`

CodeRabbit always scans these. Anything you put in `filePatterns` is added to this list, never
substituted for it — so do not restate these entries.

```
**/.cursorrules
.github/copilot-instructions.md
**/CLAUDE.md
**/GEMINI.md
**/.cursor/rules/*
**/.windsurfrules
**/.clinerules/*
**/.rules/*
**/AGENT.md
**/AGENTS.md
**/REVIEW.md
```

Scoped form — **accepted by the schema, ignored by the reviewer.** Both fields are required and each
takes comma-separated globs, so this validates cleanly and then does nothing (see trap 5):
```yaml
# DO NOT EMIT — the reviewer drops every non-string entry.
- files: "docs/backend-standards.md"
  applyTo: "services/**,packages/api/**"
```
Use a plain string in `filePatterns` plus a `reviews.path_instructions` entry instead.

---

## Supported tools (`reviews.tools.<name>.enabled`)

`actionlint, ast-grep, biome, blinter, brakeman, buf, checkmake, checkov, circleci, clang, clippy,
cppcheck, detekt, dotenvLint, emberTemplateLint, eslint, fbinfer, flake8, fortitudeLint, github-checks,
gitleaks, golangci-lint, hadolint, htmlhint, languagetool, luacheck, markdownlint, oasdiff, opengrep,
osvScanner, oxc, phpcs, phpmd, phpstan, pmd, presidio, prismaLint, psscriptanalyzer, pylint,
reactDoctor, regal, rubocop, ruff, semgrep, shellcheck, shopifyThemeCheck, skillspector, smartyLint,
sqlfluff, squawk, stylelint, swiftlint, tflint, trivy, trufflehog, yamllint, zizmor`

All are enabled by default. Only write a `tools` block to turn something **off**, or to point a tool at
a config file (`config_file` is supported by `swiftlint`, `golangci-lint`, `detekt`, `pmd`, `semgrep`,
`sqlfluff`) or set a level (`phpstan.level`, `languagetool.level`).

---

## Settings that are *not* in the YAML

Tell the user to use the CodeRabbit dashboard for these — the YAML only gates whether reviews may use
them once connected:

- Jira / Linear / Confluence / Notion authentication (Integrations)
- MCP server registration (Integrations → MCP)
- Org-level base configuration inherited via `inheritance: true`
- Repository installation and access scope
