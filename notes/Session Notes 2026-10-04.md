# Session Notes 2026-10-04

## Request

Research online options for an FC27 Pro Clubs analytics engineering project using data from The Grounds. Research and planning only; no implementation.

## Work completed

- Read the supplied Reddit API-change thread and followed its TypeScript client link.
- Reviewed official EA descriptions of The Grounds and the separate FC Community API.
- Compared Python/TypeScript clients, documented source grains, rolling-history limitations, and advanced event counters.
- Confirmed the presence of a community research CSV described as 51,395 player-match rows; did not download its contents.
- Reviewed tracker owners' descriptions as secondary references; no export interface was established.
- Saved the research brief and project memory.

## Proposed direction

Start with own-club match history and trustworthy performance metrics. Consider sanitized static research data for early modeling exploration and add validated advanced counters later.

## Open decisions

Platform, playing schedule, live-data feasibility, dataset reuse conditions, and authorization to begin implementation. dbt is selected; the remaining local stack is proposed.

## Verification and limits

Research claims are linked to source authors or official EA pages. Verified documentation/file presence, not club-specific live API behavior, CSV quality, or tracker exports. Local checks confirm documentation-only artifacts and resolving relative links. No implementation or dependency changes. Workspace is not a Git repository, so no commit was possible.

## Requirements follow-up

- Two club targets supplied; saved documents use Club A/B without an identity mapping.
- Accepted suggested analytical goals and useful analytics with portfolio-quality documentation.
- Eventual league/playoff/friendly coverage, dbt transformations, and an eventual website.
- Zero additional service budget; proposed local Python/uv, DuckDB, and dbt Core stack checked against adapter documentation.
- Explicit creator privacy and no recorded personal information. Future collection must sanitize before persistence; public reports default to club/role aggregates with generic club labels.
- Created `Project Plan.md`, updated memory, and marked earlier raw-data/player-identity research suggestions as superseded by privacy requirements.
- No data collection, package installation, Git initialization, or implementation.

## Private reference stack review

- Reviewed reference instructions, dependency declarations, dbt configuration, architecture/ADRs, representative Python/web and SQL models, test definitions, and verification/file-publication scripts.
- Confirmed familiar Python/uv, dbt Core/DuckDB and BigQuery, SQLite/SQLAlchemy/Alembic, FastAPI/Jinja/HTMX, and quality-tooling patterns.
- Updated the FC27 plan with these patterns while preserving the zero-service-fee constraint and privacy requirements. Proposed that FC27 website metrics come from dbt outputs; transactional SQLite is conditional rather than assumed.
- Kept the reference name/path and private content out of saved summaries. Did not read secret files, source datasets, or personal Git identity configuration; did not modify or run the reference application.
- Scoped verification: checked Markdown links and documentation-only inventory, and scanned document content for personal filesystem paths and private reference identifiers. Application tests were not run because this session changed only planning documents.

## Implementation milestone

Implementation was explicitly authorized after the reference review.

- Created Python/uv package and locked local DuckDB/dbt dependencies.
- Implemented exact-name discovery and sequential, bounded league/playoff/friendly reads. Source response content and URLs are never written to logs.
- Added allowlisted in-memory privacy filtering, broad-role statistics, missing-data semantics, salted match keys, and a salted target guard. Original player identities are discarded.
- Added transactional correction-aware loading, independent source availability checks, reported-total snapshots, and collector/build file locks.
- Created dbt staging/intermediate/marts models and metric contracts for results, DNF handling, weighted accuracy, UTC-day trends, and inferred sessions.
- Added a synthetic demo and local report command. dbt builds run in disposable generic temporary paths and replace the warehouse only on success.
- Added Python privacy/transaction/metric tests, dbt grain/relationship/invariant tests, Ruff/SQLFluff checks, and a public-file checker.
- Updated README, plan, data contract, and memory. No real identifiers or reference-project identity were copied into public source documents.

Live feasibility: initial discovery found Club B in common-gen5; Club A had no exact
match in either checked pool. Later project-environment discovery/collection received
HTTP 403 for both. An alternate HTTP client also received 403, with a non-JSON error
body. No real matches were captured. Availability records remain distinct from
successful empty reads and from the separate synthetic demonstration.

Remaining work: platform/name confirmation for the unresolved target, live access,
playing schedule, validated advanced counters, and eventually the website. No paid
services, background collection, external publication, or Git identity initialization.

Final verification: `bash scripts/check.sh` passed: 24 Python tests, Python lint/formatting, SQL lint, and public-file checks. The demo dbt build completed 14 models and 21 data tests. Documentation links resolve. Application/source code is unchanged after this verification; no Git commit was created because the workspace has no repository or anonymous author configuration.

Platform follow-up: mixed-console participation was clarified. Checked official EA
cross-play documentation; retain common-gen5 for the PS5/Xbox Series/PC group as
the working assumption. Nintendo is separate. No per-player platform information
was recorded and no source code or collection behavior changed. Live access remains
unresolved; the next diagnostic is discovery from the local terminal with transient
environment configuration.

## HTTP 403 follow-up

The user reproduced HTTP 403 for both targets from the local terminal. The existing
urllib client provided a browser User-Agent but did not use a browser network
profile. Reviewed [the maintained Clubs SDK's transport documentation](https://github.com/alex-jordan547/proclubs-sdk)
and [Impit's Python documentation](https://apify.github.io/impit/python/). A bounded,
read-only Impit probe returned HTTP 200 with valid JSON and an exact Club B match.
This supported changing the transport; it does not prove the reason for every 403.

- Added Impit 0.13.2 through uv and updated the lockfile; removed unused urllib
  request/error imports and the manually fixed User-Agent.
- Use a fresh Chrome-profile client per request with verified TLS, redirects
  disabled, no EA account credentials/cookies, the existing timeout/rate limits,
  and a streamed five-megabyte body limit. Reject non-200 statuses before reading
  response content; keep safe error codes and no automatic retries.
- Added 13 transport test cases for settings, streaming JSON, rejected statuses,
  body bounds, malformed JSON, connection/stream failures, request spacing, and
  endpoint allowlisting. All fixtures are synthetic.
- Actual CLI discovery now finds Club B in common-gen5. Club A's valid search
  response has no exact match; requested exact in-game name and pool confirmation.
- Live Club B collection captured ten sanitized league matches, successful empty
  playoff/friendly reads, and an overall snapshot. The full league window may omit
  older history. No raw responses, source names/IDs, or player identity fields were
  written by the collector.
- Built the live warehouse successfully: 14 models and 21 dbt data tests passed.
  The local live report is available. Updated README, plan, and memory to reflect
  one successful collection and the remaining Club A discovery issue.

Verification: `bash scripts/check.sh` passed all 37 Python tests, Python
lint/formatting, SQL lint, and public-file checks. The live build and report also
succeeded. No publication, paid service, scheduler, or Git initialization occurred.

## Public GitHub readiness audit

The user asked whether the project is ready for public GitHub publication.

- Audited the 51 candidate public files, including dotfiles and notes; the existing
  checker and additional in-memory identity/credential-pattern scans passed.
  Target identities and creator/private-reference identifiers were searched only
  in memory, without saving their values in audit files.
- Verified a clean copy with no runtime data, existing virtual environment, or
  live configuration. Locked installation, synthetic demo, dbt build, and report
  passed; the build completed 14 models and 21 data tests and the documented
  synthetic report matched.
- Verified eleven representative private/runtime paths are excluded by project
  ignore rules, using a disposable Git repository with no commits or remote.
  The project workspace remains outside Git.
- Checked official GitHub documentation for account ownership, commit attribution,
  noreply usernames, and licensing. Source checks cannot establish the privacy of
  a future publishing account or commit metadata.
- Saved `Public Release Readiness.md` and updated memory. The code is suitable for
  an initial source-only MVP. Publishing identity and first-commit metadata still
  need review to satisfy creator anonymity. License and CI additions are recommended
  but are not required for a public repository.

No application code changed, no license was selected, and no account configuration,
persistent Git initialization, or external publishing action was performed. The
prior 37-test full verification remains applicable; scoped clean-copy and content
checks were run for this audit.

## Creator privacy scope clarification

The user clarified that GitHub identity/attribution is acceptable and only the
website UI should omit creator identity. This supersedes the earlier requirement
for an unlinked publishing account and pseudonymous commit metadata.

- Updated README, plan, data contract, release readiness, and memory to reflect
  website-only creator privacy. GitHub is ready for an initial public MVP under
  the clarified scope; license and CI remain recommended additions.
- Future website headers, footers, credits, contact/about areas, and personal
  profile links must not identify the creator. There is no website implementation
  to modify yet. Source/player data filtering and runtime-data exclusions remain
  required.
- Removed the public-file check's author-attribution rejection to allow normal
  GitHub attribution. Private-file and personal-machine-path checks remain.
- No account configuration, repository creation, commits, or publication performed.

Scoped verification: public-file and Ruff checks pass; a temporary fixture confirms
author fields are accepted while a private environment file is still rejected.

## Public repository and profile publication

The user explicitly requested pushing the project to public GitHub, writing a
project README, and adding it as the third Current Projects item below the existing
second item in their GitHub profile.

- Verified GitHub authentication and that the target repository name was available.
- Initialized this project's Git repository on main after authorization.
- Expanded README with project purpose/status, a Mermaid pipeline, stack table,
  clone/demo quickstart, live configuration, metric choices, layout, verification,
  privacy behavior, and planned scope. Examples remain synthetic or placeholders.
- Prepared the profile entry following its existing emoji/link/description/stack
  style. Verified the profile checkout matched the remote and had no prior edits.
  Only the new third entry is inserted; all other README content is preserved.
- Updated project memory and release readiness. No runtime databases, environment
  files, raw responses, cache directories, or generated dbt artifacts are intended
  for the release. No license or CI workflow was added to this request.

Scoped verification: README local links and commands resolve; profile ordering is
skills first, the existing project second, and FC Clubs third. Public-file checks
pass. Application code has not changed since the prior 37-test verification and
clean-copy demo build with 14 models and 21 dbt tests.

Pre-publication verification also ran the complete `bash scripts/check.sh` suite
against the new staged repository: all 37 Python tests, lint/formatting, SQL lint,
and public-file checks passed. Reviewed all 52 staged files; no live data, target
identities, environment files, or generated outputs are staged. README links resolve
and the profile-only insertion check passes.
