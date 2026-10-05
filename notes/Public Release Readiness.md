# Public release readiness

Reviewed 2026-10-04. Initial scope: assess a source-only GitHub release. Publication
was subsequently authorized and completed; see the follow-up below.

## Verdict

The current implementation is suitable for an initial public MVP on Linux/WSL.
Source-content checks and clean-copy demo reproduction pass. The user's later
clarification permits GitHub account ownership and normal commit attribution;
a pseudonymous GitHub identity is not required. Creator privacy applies to the
eventual website UI, which has not been implemented yet.

## Verified

- Reviewed the 51 candidate public files present at the start of the audit,
  including dotfiles, configuration, dependency lockfile, tests, and project notes.
- The existing public-file checker passes. Additional in-memory searches detected
  no supplied creator handles, target club names, private-reference identity,
  personal email addresses, personal filesystem paths, recognizable private-key
  blocks, or recognizable GitHub/OpenAI token strings in candidate files. These
  checks are evidence about the inspected files, not a guarantee against every
  possible form of identification.
- Actual runtime databases, environments, caches, generated dbt outputs, and
  secrets directories were excluded from the inspected public inventory.
- Tested the project ignore rules in a disposable Git repository against eleven
  representative runtime/private paths; all were excluded. At the time of the
  initial audit, the workspace was outside Git, with no commits or remote to inspect.
- Copied only candidate public files into a clean temporary directory, excluding
  dependencies and runtime data. The documented locked install, demo, dbt build,
  and report all succeeded without live configuration. The demo build passed 14
  models and 21 data tests; both aliases matched the documented synthetic report.
- The latest full source verification remains the prior successful 37 Python
  tests, Python lint/formatting, SQL lint, and public-file checks. This audit did
  not change application code or repeat that full suite.

## Publication scope and website privacy

- GitHub account ownership and normal author/committer attribution are acceptable
  under the clarified requirement. An unlinked account is not a release prerequisite.
- The future website UI must omit creator names, handles, email addresses, personal
  profile links, and creator credits, including in headers, footers, contact areas,
  and about sections.
- Review the actual staged file inventory before pushing. Keep runtime databases,
  raw responses, logs, real report exports, and local environment values out of
  the public repository. Uploading the entire workspace bypasses Git ignore rules.

[GitHub repository ownership](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository),
[commit email configuration](https://docs.github.com/en/account-and-profile/how-tos/email-preferences/setting-your-commit-email-address),
[noreply address format](https://docs.github.com/en/account-and-profile/reference/email-addresses-reference).

## Recommended release additions

There is no LICENSE file or GitHub Actions workflow yet. Neither prevents a public
source repository, but an explicit license establishes reuse permissions and
automated checks make future changes easier to assess. A permissive license such
as MIT is a reasonable option for the original application code; choose it
deliberately. Normal copyright attribution is acceptable. A code license does not establish
permission to redistribute upstream game data.

[GitHub licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).

Use the existing synthetic demo for public examples and future CI. Document the
release as an initial collector/dbt project: Club A discovery remains unresolved,
live access is undocumented and variable, captured history is incomplete, and
the website and scheduler are later work. These limits do not prevent sharing
the current source and reproducible synthetic pipeline.

## Publication follow-up

The user subsequently authorized creating and pushing the public `fc-clubs`
repository and adding it as the third item in the GitHub profile's Current Projects.
The README now covers architecture, stack, quickstart, live configuration, metric
choices, quality checks, privacy, and project scope. Source and synthetic examples
are the release contents; runtime data remains excluded. Git was initialized on
main only after this explicit publication request.

Publication completed at [fc-clubs](https://github.com/jinsoowhang/fc-clubs). Verified
PUBLIC visibility, the main branch, matching remote README, and all 52 published
files without private runtime data. The remote profile README lists FC Clubs third,
directly below its existing second item. The full verification suite passed again
before the initial publication commit.
