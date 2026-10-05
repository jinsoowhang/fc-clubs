# FC Clubs project memory

## Scope and preferences

- Project goal: useful FC27 Pro Clubs analytics with portfolio-quality analytics engineering documentation.
- Implementation was explicitly authorized on 2026-10-04. First milestone is the local collector and dbt analytics; website/publication remain later work.
- User supplied the Reddit API-change thread linked in the research brief.
- Two target clubs were supplied in the conversation. Persistent project documents use Club A and Club B without saving an identity mapping.
- Eventual scope: league, playoff, and friendly matches; other Grounds activities depend on verified availability.
- Accepted questions: club improvement over time, contribution, and session performance. Under the privacy constraint, contribution initially means club/role-level measures.
- Required transformation tool: dbt. A website is an eventual goal, not the current phase.
- Additional service budget: zero. Prefer existing local hardware and open-source tools; no paid services or OpenAI API integration are planned.
- Latest creator-privacy clarification: GitHub account ownership and normal commit attribution are acceptable. Privacy applies to the eventual website UI: no creator name, email, handle, personal profile links, or creator credits. A pseudonymous GitHub account is not required. Keep project examples generic and avoid unnecessary personal machine paths. This supersedes the earlier requirement for creator anonymity across all project/repository metadata; player/source-data privacy remains in force.
- Data privacy default: no persistent player names, gamertags, account IDs, or reidentification mappings. Sanitize before writing responses, logs, fixtures, databases, or exports. Public output uses generic club labels and aggregates.
- Exact pool confirmation and playing schedule remain unconfirmed. Club B is discoverable in common-gen5; Club A returned no exact match in earlier checks of either pool and the latest common-gen5 check.
- Latest clarification: club players use multiple consoles. Keep common-gen5 as the working pool for PS5/Xbox Series/PC cross-play; this is an inference, not confirmation of Nintendo participation. Player-specific platform information is unnecessary and must not be collected.
- Plan: `notes/Project Plan.md`. Proposed local stack: Python managed with uv, DuckDB, dbt Core with dbt-duckdb. Only dbt is user-selected; the remaining tools are recommendations.
- A private reference was reviewed read-only for stack familiarity; do not record its name/path or copy its private code, data, credentials, or external account configuration into this project.
- Reference tooling observed: Python/uv, dbt Core/DuckDB, BigQuery/hosted dbt, SQLite/SQLAlchemy/Alembic, FastAPI/Uvicorn, Jinja/HTMX, pytest/Ruff/SQLFluff, pre-commit and GitHub Actions. Familiarity is inferred from project usage, not a separate stack approval.
- Prefer familiar dbt layers/naming, explicit grains, synthetic fixtures, and meaningful model tests. For FC27, website metrics should consume dbt marts/exports. SQLite is conditional on operational needs; hosted warehouse services remain deferred.

## Research state — 2026-10-04

- Research brief: `notes/FC27 Data Research and Project Options.md`.
- Accepted initial direction: own-club performance history with documented metrics; advanced counters are a later extension. Apply the newer privacy requirements in `notes/Project Plan.md` to the earlier research options.
- Public Clubs website JSON is undocumented and separate from EA's account-connected Community API for approved Ultimate Team partners.
- Community references report league/friendly/playoff match access and a rolling maximum of ten recent matches without pagination. Club-specific live feasibility remains unverified.
- FC27 references report `common-gen5` and `nx` pools, annual club-ID reuse, and no game-year selector. Record edition and pool explicitly in future data.
- Candidate clients: `1erkandogan/fc27-clubs-api` (Python) and `alex-jordan547/proclubs-sdk` (TypeScript). The latter excludes warehousing/bulk scraping from its supported scope.
- `Interactive-63/eafc-pro-clubs-api-research` documents event-count mappings and publishes a CSV described as 51,395 player-match rows. File presence/documentation verified; contents and reuse conditions not independently checked.
- Rush, small-sided games, Kickabouts, and Live Tournament endpoints were not confirmed.
- Metric planning must address DNF outcomes, percentage weighting, names versus IDs, missing fields, clock semantics, event-mapping confidence, and incomplete captured history.

## Workspace

- Workspace was empty and was not a Git repository at the start of research.
- Implemented Python/uv package, allowlisted in-memory sanitizer, DuckDB storage, three-scope collector, synthetic demo, dbt layers/marts, local report command, and scoped verification scripts.
- Dependencies are locked in uv.lock. Use `uv sync --locked --all-groups` and `bash scripts/check.sh`.
- `uv run fc-clubs demo`, then `uv run fc-clubs build --database data/demo.duckdb` and `uv run fc-clubs report --database data/demo.duckdb` exercise the synthetic pipeline.
- Live target names are process environment values only (`FC_CLUB_A_NAME`, `FC_CLUB_B_NAME`); pool variables default to common-gen5. No target names or direct identifiers are saved.
- Sanitized match rows and broad-role aggregates are persisted; salted match keys and a salted club-identity guard are technical local metadata. No player pseudonyms, player IDs, account names, or raw responses.
- Database locks coordinate collection and dbt builds. dbt runs in disposable generic temporary directories, publishes database changes only after a successful build, and does not leave manifests/logs in the workspace.
- Initial urllib-based live collection received HTTP 403 for both targets, also reproduced in the user's terminal. A maintained Clubs client documents Impit with a Chrome network profile; this differs from changing a User-Agent string alone.
- Replaced urllib transport with Impit 0.13.2, locked through uv. Fresh clients use the Chrome profile, verified TLS, no redirects or account cookies, a ten-second timeout, sequential one-second spacing, and a streamed five-megabyte limit. Errors expose only safe codes; non-200 responses are rejected without reading the body and no automatic retries occur.
- Latest live discovery succeeds for Club B in common-gen5; Club A returns club_not_found from valid JSON. Club B collection saved ten sanitized league matches, successful empty playoff/friendly checks, and an overall snapshot. The league window is full, so older history may be missing. This is one successful collection, not a guarantee of continued access or complete history.
- Transport regression tests cover streaming, response bounds, error-body suppression, connection/stream failures, TLS/redirect settings, and request spacing. Latest full check passes 37 Python tests, lint/formatting, SQL lint, and public-file checks. The live dbt build passes 14 models and 21 data tests.
- See `notes/Data Contract.md` for grains, DNF/null/weighted-rate rules, and coverage limitations.
- Notes stay under this project's `notes/` directory in the existing `Project` tree.
- Public release audit: `notes/Public Release Readiness.md`. Current source is suitable for an initial Linux/WSL MVP; inspected content and clean-copy locked-install/demo/build/report checks pass. The user's later clarification removes GitHub identity as a privacy blocker; website UI must omit creator attribution. No LICENSE or CI workflow exists yet; those are recommended release additions, not requirements for GitHub visibility.
- Public GitHub publication was explicitly requested after the privacy clarification, including a repository README and placement as the third Current Projects item below the existing second entry. Use the repository name `fc-clubs`, publish reviewed source and synthetic examples, and keep runtime data private. The workspace now has a main-branch Git repository. Publication target: `https://github.com/jinsoowhang/fc-clubs`.
