# FC Clubs project plan

Status: implementation authorized on 2026-10-04; local collector and dbt baseline implemented. Live collection works for Club B; Club A discovery remains unresolved. Website/publication are later work.

## Accepted requirements

- Track two clubs, referenced here as Club A and Club B. Target names remain in the conversation; this document does not save a mapping to public labels.
- Answer whether club performance is improving, how contribution varies, and how sessions compare.
- Produce useful club analytics with portfolio-quality models, metric documentation, and verification.
- Eventually cover league, playoff, and friendly matches. Add other Grounds activities only if access is verified or a manual source is explicitly selected.
- Use dbt for analytics engineering. An eventual website is a later deliverable.
- No additional service fees. Use existing local hardware and open-source software. No paid hosting, paid warehouse, paid dbt service, domain purchase, or OpenAI API integration is planned.
- Do not identify the creator in the website UI. GitHub account ownership and commit attribution are acceptable.

## Recommended stack

Python collection managed with uv → in-memory privacy filter → DuckDB → dbt Core using dbt-duckdb → local reports → eventual reviewed website exports.

The adapter connects dbt to local DuckDB files and supports reading/writing external JSON, CSV, and Parquet data. This supports a small local setup without a managed database service. [Adapter documentation](https://github.com/duckdb/dbt-duckdb), [dbt local installation](https://docs.getdbt.com/docs/local/install-dbt).

The first implementation uses Python 3.12, uv, DuckDB, dbt Core, and dbt-duckdb with locked dependencies. Live capture and synthetic demo use separate local databases. Version selection is recorded in uv.lock; no managed service or AI API is used.

### Stack familiarity from a private reference review

The reference was inspected read-only. This summary deliberately omits its project name, location, account configuration, business data, and implementation code.

Observed stack and practices:

- Python 3.12, uv, a packaged `src/` layout, and CLI entry points.
- dbt Core and dbt-duckdb for local reproducibility, with a separate BigQuery/hosted-dbt analytical path.
- Root-level dbt configuration, staging/intermediate/marts layers, explicit grains, and `stg_<source>__<entity>`, `int_`, `dim_`, and `fct_` naming.
- SQLite, SQLAlchemy, and Alembic for transactional application state.
- FastAPI/Uvicorn, server-rendered Jinja templates, HTMX, CSS, and focused JavaScript for the local website.
- pytest, Ruff, SQLFluff with dbt templating, generic and singular dbt tests, pre-commit hooks, and GitHub Actions.
- Strict source contracts, reproducible snapshot loading, explicit missing-data semantics, synthetic fixtures, architecture/ADR documentation, and checks excluding private files from publication.

Planning implications:

1. Keep the proposed local Python/uv + DuckDB + dbt Core stack: it matches demonstrated tooling familiarity and the zero-service-fee requirement. Do not copy dependency pins without checking compatibility when implementation starts.
2. Adopt the familiar dbt model layers, grain documentation, test conventions, and synthetic fixtures. Add privacy checks for content as well as file paths; ignoring sensitive files alone does not satisfy the no-identifying-data requirement.
3. Use FastAPI + Jinja + HTMX as the preferred local website option if server-rendered interaction is needed. For eventual public hosting, a static version of reviewed aggregate exports remains the initial recommendation; public hosting is still undecided.
4. Make dbt marts the authority for FC27 analytical metrics. The reference's operational website computes dashboards from SQLite services while dbt runs downstream. Here, a website should consume dbt-produced results rather than duplicate metric logic in Python.
5. SQLite/SQLAlchemy/Alembic are familiar options, but add them only if mutable annotations, review workflows, or durable collection state require transactional storage. A read-only analytics project does not automatically need a second database.
6. BigQuery and hosted dbt are familiar, but remain outside the initial FC27 architecture. Their existing reference configuration is not evidence that a new deployment satisfies this project's zero-cost and data-privacy constraints.
7. Carry over architectural patterns, not private code, data, configuration, external integrations, or account identity.

Local collection depends on the machine being awake and connected during collection windows. Missing the rolling match window can lose data. A continuously available free hosted collector is not promised. Choose scheduling after the playing pattern and publication lag are known.

## Privacy requirements

1. The website UI must omit creator names, emails, personal usernames, profile links, and creator credits. Keep configuration/examples generic and avoid unnecessary personal machine paths.
2. GitHub account ownership and normal commit attribution are acceptable; no pseudonymous publishing account is required. Do not infer or record which player is the creator in analytical data.
3. Future API responses may contain player names, gamertags, account IDs, and other identifiers. Filter them in memory before persistence. No full-response files, exception-body dumps, or unsanitized fixtures.
4. Use an explicit allowlist of necessary match/club measures and raw statistical counters. Schema changes should not automatically introduce new persisted fields.
5. Do not retain stable player pseudonyms, hashes of player IDs, or identity mapping tables by default. These still permit linking people over time. Initial contribution reporting is club/role-level rather than named individual comparisons.
6. Public artifacts should default to generic club labels, aggregate measures, and coarse dates. Source club IDs, match IDs, precise times, source links, and rare combinations can enable linkage; evaluate them before publication. Internal technical match keys, if needed, remain outside public exports.
7. Review staged repository files to exclude private runtime data and generated artifacts. Review the future website's UI, including headers, footers, credits, contact sections, and profile links, for creator attribution. GitHub publication and website deployment still require an explicit request.

The latest clarification narrows creator privacy to the website UI and supersedes the earlier repository-anonymity requirement. Source/player privacy still supersedes the research brief's original raw-response preservation and player-identity options. Sanitized source observations can still support reproducible transformations and versioned statistical mappings.

## Initial analytical deliverable

Recommended first deliverable: compare club results and trends across time, plus session summaries and broad role contribution.

Candidate models:

- Match: one game edition + platform pool + match key.
- Club-match: one match + participating club.
- Club-role-match: one club-match + broad position group, containing aggregated statistics without persistent player identity.
- Club snapshot: one club + observation time + source scope.

Initial metrics: completed-match win rate, goals for/against per match, DNF rate, weighted passing/tackling success, broad-role contributions, and rating trends. Include match scope, sample sizes, capture coverage, and metric definitions. Sessions need a stated grouping rule; repeated player appearances must not be presented as distinct people.

Persistent individual progression and lineup chemistry are deferred because they conflict with the current no-identifying-data default. Build effectiveness and formations also require verified or manually provided context.

## Phases and success criteria

### 1. Feasibility and final design

Confirm platform pool and both club identities in memory. Inspect a small read-only sample without saving identifying response content. Verify match categories, available fields, history window, and publication lag. Produce a field allowlist, metric contracts, and a proposed collection schedule.

Pass criteria: both intended clubs are discoverable; selected metrics have supporting fields; sanitizer rules cover all retained structures; keys support repeated reads without duplicating matches; unavailable scopes and incomplete history have explicit handling.

### 2. Collection and dbt models — baseline implemented

Build a minimal local collector with sanitization before any write. Add staged, fact, and aggregate models, meaningful grain/relationship/metric checks, and source coverage reporting. Keep configuration and data out of public artifacts when they reveal linkage.

Pass criteria: repeated collection is idempotent; no identifying fields persist in files/logs/fixtures; model grains hold; calculations agree with a small checked sample; tests and documentation describe important limits.

### 3. Broader scopes and validated event metrics

Expand to available playoffs/friendlies with scope-specific outcome rules. Validate selected advanced counters before incorporating them. Record unsupported Grounds activities as coverage gaps rather than successful empty collections.

### 4. Website — separately requested

Create a website consuming reviewed aggregate exports. Prefer a static site initially to avoid a paid runtime. Select and verify hosting limits/privacy behavior at that time. A public website does not require exposing the development repository or source data.

## Implementation state

Implemented three match-category reads, exact club-name discovery, privacy filtering
before persistence, idempotent/correctable club and role facts, overall snapshots,
availability observations, and analytical marts for results, roles, days, and inferred
sessions. CLI reports identify demo/live datasets and surface coverage status.

Automated verification uses invented responses and full dbt builds. The initial
HTTP transport received HTTP 403. Switching to Impit's Chrome network profile
returned valid JSON: Club B was found in common-gen5 and ten league matches were
sanitized and captured, with successful empty playoff/friendly reads and an overall
snapshot. The full league window signals possible missing older history. Club A
still had no exact name match in the current-generation search. Access can change;
this establishes one successful live collection for Club B.
No scheduler, website, hosted deployment, Git initialization, or author attribution
has been created. See README.md and [Data Contract](Data%20Contract.md).

## Still needed

- Nintendo-specific participation, if applicable. Mixed PS5/Xbox Series/PC players share the current-generation pool; individual player platforms are unnecessary.
- Typical playing frequency and session length to plan collection.
- Confirm Club A's exact in-game name and pool to resolve its discovery.

No personal name, email, EA login, gamertag, or payment information is needed.

Platform clarification: players use multiple consoles. Use the existing common-gen5
default as a working assumption for mixed PS5/Xbox Series/PC clubs. EA documents
Nintendo as separate from that cross-play group; an nx lookup is only relevant to
a Nintendo club. Transport access and pool selection are separate checks.
[EA cross-play documentation](https://help.ea.com/en/articles/ea-sports-fc/cross-play/).
