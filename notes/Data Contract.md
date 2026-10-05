# Data contract and metric definitions

Version 1. Scope: FC27 public Clubs match endpoints, three observed match categories.

## Privacy boundary

Only source responses in memory may contain player or club identities. The sanitizer
creates new dictionaries from explicit numerical fields. It aggregates appearances
by broad role and discards names, account IDs, arbitrary fields, nationalities,
platform namespaces, customization, and event text. Unknown roles become `unknown`.
No source-response JSON, named-player table, or reidentification mapping is stored.

Match deduplication uses HMAC-SHA256 over edition, platform pool, and source match ID
with a random salt stored in the ignored database. These internal match keys are
technical linkage, not public export fields. The collector never stores source club
IDs or target names. It re-discovers them from process configuration each run.

## Persisted relations

| Relation | Grain | Allowed data |
| --- | --- | --- |
| `raw.club_matches` | Edition/pool/scope/alias/match key | Match time, goals for/against, outcome, DNF, first/last seen |
| `raw.club_role_matches` | Club-match/role | Appearance/rated counts, rating sum, goals, assists, shots, passing/tackling attempts/completions, saves, red cards |
| `raw.club_snapshots` | Edition/pool/alias/observed time | Reported games/results/goals and skill rating |
| `raw.collection_checks` | Edition/pool/alias/scope/check time | Status and number of returned matches |
| `raw.metadata` | Technical setting name | Dataset kind, random salt, and salted target-identity guard |

Match and role data update atomically. Rereads preserve first-seen time and replace
the current role set to handle corrected or removed role observations. A malformed
payload rejects the whole response before writing any match from that payload.
Independent clubs/scopes may succeed while another fails; prior data is not deleted.
A salted club-identity guard prevents merging a different discovered club into an
existing alias/pool. Changing a target requires a separate database; original club
IDs and names remain unrecorded. Collector/build commands share a fail-fast file
lock so an analytical rebuild cannot overwrite a concurrent collection.

The source match list must be an array, including a genuinely empty array. Null,
error objects, nonnumerical scores, malformed player maps, and invalid timestamps
are rejected. Numeric fields accept finite nonnegative numbers or numeric strings;
counts must be integers. Known result codes are mapped by category. New unrecognized
league/playoff result codes yield `unknown`, never an inferred completed win.

## Metrics

- Completed match: non-DNF with a known win/draw/loss outcome.
- Completed win rate: completed wins / completed matches; null if none.
- DNF rate: DNF matches / captured matches. Source award flags and observed DNF
  result codes determine DNF; counts do not establish who intentionally quit.
- Goals per match: score goals / all captured matches, including DNF and unknown
  outcomes. Source awarded scores are not reinterpreted as actual playing events.
- Friendly outcome: compare source goals; league outcome flags may be zero there.
- Pass/tackle accuracy: summed completions / summed attempts, never the average of
  individual percentages. A missing count in any role appearance makes the aggregate
  for that measure null; zero attempts also yield null.
- Average rating: sum of known game ratings / rated appearances. Missing ratings
  reduce the rated count; reports retain this count. Ratings are game-generated.
- Role appearance: one returned player row. It is not a distinct-person identity.
- Session: matches within a club, pool, edition, and scope separated by gaps no
  greater than 90 minutes. This is an inference, not game telemetry. Rebuilding
  after newly captured older matches can change session numbers. Timestamps are UTC.
- Daily trends show only captured dates. Missing dates are not filled with zero.

Reported overall totals have `stat_scope = source_overall`. They are not substituted
for captured match counts or reconciled as if all modes shared the same source scope.
No per-90 rate, formation attribution, player progression, causal build comparison,
or advanced-event metric is implemented without verified supporting data.

## Coverage and limitations

- `ok`: a valid nonempty response below the reported maximum window size.
- `window_full`: at least ten matches returned; older unseen history may exist.
- `empty`: a valid empty array. It does not prove the club never played the scope.
- `unavailable`: discovery/access failed.
- `invalid`: response contract failed.

No status establishes full season completeness. The latest status is exposed in
`mart_collection_coverage`; failed reads cannot silently become empty successful
collections. Network reads are sequential, spaced by at least one second, bounded
by a timeout and maximum response size, and not retried indefinitely.

Publishing any real aggregates needs a separate content/linkage review. Synthetic
fixtures are the reproducible public examples. GitHub ownership and commit
attribution are acceptable. The eventual website UI must omit creator names,
handles, email addresses, profile links, and creator credits.
