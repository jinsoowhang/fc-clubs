# FC27 data research and project options

Research date: 2026-10-04. Scope: research and planning only.

Requirements update: the selected direction is club performance history for two targets, dbt transformations, an eventual website, and no additional service fees. New privacy requirements supersede suggestions below to retain original responses, player identifiers, or publish identifiable club/player details. Use sanitized observations and club/role aggregates as specified in [Project Plan](Project%20Plan.md).

## Recommendation

Start with an analytics engineering project that preserves club match history and turns it into trustworthy performance metrics. Add advanced event counters after validating their meaning. Two targets and eventual league/playoff/friendly coverage are now selected; platform and live feasibility remain pending.

The useful portfolio story is how you handle an unstable source, limited history, changing identities, explicit data grains, reproducible transformations, and well-defined metrics. A dashboard is the consumer of that work.

Research success criteria: identify credible sources, distinguish documented observations from guarantees, compare practical project options, record data limitations, and define a feasibility checklist. Building a collector or choosing infrastructure is outside this phase.

## 1. What data access actually exists?

### Public Clubs website endpoints

The TypeScript client linked in your Reddit thread reads public Clubs JSON without EA credentials. Its maintainer describes the upstream service as undocumented and subject to change. Browser/HTTP-client behavior and hosting location can affect access. This is evidence from a client author, not an EA service guarantee. [Client repository](https://github.com/alex-jordan547/proclubs-sdk).

The Python client is another route to the same source. It offers raw JSON, flattened records, and optional pandas DataFrames. It reports no API key requirement and provides standard match statistics plus decoded event counters. It has no built-in caching or rate limiting, so a future collector would need its own modest request policy. [Python client](https://github.com/1erkandogan/fc27-clubs-api).

### Official FC Community API

EA's July 27 announcement describes a separate account-connected program for Ultimate Team data. It names FUT.GG, FUTBIN, and FUTWIZ as approved launch partners and says it is not accepting requests from other sites. That announcement does not provide a general Clubs developer API. Its account-data retention provisions should not be assumed to describe the public Clubs endpoints. [EA announcement](https://www.ea.com/games/ea-sports-fc/fc-26/news/pitch-notes-fc26-community-api-update).

### Coverage of The Grounds

EA confirms that Clubs Leagues and Playoffs live inside The Grounds, alongside Rush, small-sided games, Kickabouts, and Live Tournaments. It lists The Grounds for PS5, Xbox Series X|S, PC, and Switch 2. [Official deep dive](https://www.ea.com/games/ea-sports-fc/fc-27/news/pitch-notes-fc27-the-grounds-deep-dive).

The reviewed clients expose league, friendly, and playoff match categories. I did not find confirmed public endpoints for Rush, Kickabouts, small-sided results, or Live Tournament results. Their absence from these references does not prove that no endpoints exist. Treat those activities as an open research question rather than promised coverage. [Match reference](https://github.com/alex-jordan547/proclubs-sdk/blob/main/docs/reference/matches.mdx).

## 2. FC27 changes that affect planning

Your Reddit post reports last-generation API requests returning HTTP 400, club IDs resolving differently after the yearly switchover, and empty playoff history early in FC27. It also reports that player platform namespaces are unavailable in friendlies. [Original thread](https://www.reddit.com/r/fifaclubs/comments/1wu0u1o/what_changed_in_eas_clubs_api_with_fc_27/).

The maintainer's follow-up documentation, checked September 30 and October 1, says:

- Current-generation lookups use `common-gen5`; Nintendo uses `nx`.
- There is no observed separate Switch 2 API pool or game-year selector.
- The routes remain `/api/fc/`; the URL does not identify the edition.
- Saved club IDs should be rediscovered and confirmed after an annual release.

These are community observations. Nintendo API labels should not be interpreted as proof that every Nintendo hardware generation supports FC27 Clubs. [FC27 compatibility guide](https://proclubs-sdk.mintlify.app/docs/guides/fc27-api-changes).

Planning implications: attach `game_edition`, API platform pool, and retrieval time to every source record. Scope club keys by edition and pool. Preserve unknown raw codes. An empty playoff response needs an availability/coverage explanation, rather than a conclusion that a club has never played playoffs.

## 3. Available data and its grain

The endpoint inventory below is community documented under `https://proclubs.ea.com/api/fc`. [Endpoint observations](https://github.com/1erkandogan/fc27-clubs-api/blob/main/docs/endpoints.md).

| Source path | Observed grain / purpose | Proposed use |
| --- | --- | --- |
| `allTimeLeaderboard/search` | Club search with edition-to-date totals | Find and confirm your club |
| `currentSeasonLeaderboard/search` | Club search with current-season totals | Snapshot season progress |
| `clubs/info` | Club metadata | Club name, region, crest, stadium context |
| `clubs/overallStats` | Club aggregate record | Record, goals, streaks, skill-rating snapshots |
| `members/stats` | Current member / current-season totals | Roster and member snapshots |
| `members/career/stats` | Member career totals at that club | Aggregate reconciliation |
| `clubs/matches` | Match with nested club and player maps | Match, club-match, player-match facts |
| `club/playoffAchievements` | Club playoff history | Revisit after populated responses are available |

Recent match payloads contain IDs, timestamps, clubs, scores, results, DNF indicators, player IDs/names, broad positions, ratings, goals, assists, shots, saves, passing/tackling statistics, and aggregate counters. Field presence can vary. [Match schema reference](https://github.com/alex-jordan547/proclubs-sdk/blob/main/docs/reference/matches.mdx).

Member payloads include totals, success rates, average ratings, and Virtual Pro metadata. Numeric values can be strings, numbers, or null; individual fields are optional. These snapshots are not a substitute for a player's appearance in a particular match. [Member reference](https://github.com/alex-jordan547/proclubs-sdk/blob/main/docs/reference/members.mdx).

### Critical history limitation

The Python maintainer reports a default of five recent matches, a maximum of ten, and no pagination, based on checks through October 2. This needs confirmation for your club and match categories. Older uncaptured matches cannot be assumed recoverable. Friendly result flags may all be zero, so scores are needed to derive a result. [Observed response behavior](https://github.com/1erkandogan/fc27-clubs-api/blob/main/docs/endpoints.md).

Design implication: collect during playing sessions once implementation is authorized, with overlapping reads and deduplication. Daily collection could miss a long session. Choose frequency from observed match throughput and publication lag; no universal safe rate was established. If a gap occurs, label it explicitly. Aggregate totals might expose a discrepancy but cannot recreate missing player-match detail.

### Advanced statistics

Community mappings interpret `match_event_aggregate_0..3` as event-ID counts. Reported examples include passing direction/length, possession won/lost by pitch third, second assists, and positioning feedback. The research separates high-confidence mappings from partial and exploratory findings. These are game counters rather than a timestamped sequence of actions. [Original event research](https://github.com/Interactive-63/eafc-pro-clubs-api-research).

Named fields and decoded counters can differ: the Python documentation explains that named completed passes can include offside passes while event 215 excludes them. Direction/length counters do not always exhaust the total. Overlapping goal tags should not be summed into total goals. [Event mapping notes](https://github.com/1erkandogan/fc27-clubs-api/blob/main/docs/match-events.md).

Planning implication: store raw counters and version each mapping with its source and confidence. Publish validated metrics first. Do not promise heatmaps, passing networks, shot-location xG, detailed tactics, or Amp/build effectiveness from these counters alone; those require additional evidence and context.

## 4. Practical source options

| Option | What it offers | Main tradeoff | Assessment |
| --- | --- | --- | --- |
| Direct public Clubs JSON | Maximum control of original responses | Access and schema maintenance are yours | Viable after a small feasibility check |
| Python `fc-clubs-api` | Convenient raw/record/DataFrame access | Third-party normalization and missing collector controls | Best candidate if you prefer Python |
| TypeScript `proclubs-sdk` | Validation, typed errors, retries, optional cache | Node ecosystem and a narrower supported use case | Useful alternative and reference |
| Published research CSV | Immediate static player-match data | Sample/provenance/reuse questions; no fresh feed | Strong exploration option |
| Existing trackers | Human comparison and product inspiration | Export and historical access not established | Secondary reference |
| Manual match/session log | Tactics, builds, patch context, uncovered modes | Manual work and incomplete capture | Useful supplement or fallback |
| Screenshots/video extraction | Potential access to on-screen data | Extraction and validation can dominate the project | Defer unless uncovered modes are essential |

The TypeScript SDK explicitly excludes bulk scraping, enumeration, and data warehousing from its supported scope. Treat it as a possible low-volume reader, not a supported warehouse platform. Library code licenses do not establish rights to redistribute EA data. [SDK limitations](https://github.com/alex-jordan547/proclubs-sdk/blob/main/docs/project/limitations.mdx).

### A static dataset already exists

The event-research repository publishes `data/eafc_27_raw_player_data.csv`. Its data README reports **51,395 player-match rows**, including match IDs, timestamps, club/player information, named statistics, percentages, and raw counters. The file listing is approximately 48 MB. This session confirmed the file's presence and read the documentation; it did not download or independently profile the CSV. [Dataset description](https://github.com/Interactive-63/eafc-pro-clubs-api-research/blob/main/data/README.md).

Before adopting it, check collection dates, match types, duplicated matches, sampled clubs, missingness, and edition provenance. Confirm reuse conditions before redistribution; I did not find an explicit license in the reviewed root listing. The dataset is a convenience sample, so benchmarking it as the whole FC27 population would be unjustified.

### Existing trackers

Pro Clubs Tracker advertises recent stats and an optional archive of a club's season. FCClub.gg describes scheduled ingestion and retained FC26 records. Neither reviewed homepage established a developer export interface. They could help compare a few known matches or reveal an existing archive, but access would need confirmation. [Pro Clubs Tracker](https://proclubstracker.com/), [FCClub.gg](https://fcclub.gg/en).

Their pages also contain inconsistent/stale platform or edition wording. Prefer dated endpoint observations and official game documentation for platform conclusions. Do not interpret an advertised archive as complete historical backfill for a newly registered club.

## 5. Project directions

These are proposed scopes based on the sources above, not capabilities already validated for your club.

| Direction | Questions you could answer | AE work demonstrated | Feasibility |
| --- | --- | --- | --- |
| **Own-club performance history — recommended** | Are we improving? Who contributes by role? How do completed games differ from DNFs? | Incremental facts, identity management, snapshots, tests, documented metrics | Strongest initial scope |
| Advanced role contribution | Who progresses the ball or wins possession? What changes by broad position? | Versioned event mappings, semantic definitions, quality controls | Good second phase after validation |
| Small club benchmark/scouting cohort | How do selected clubs compare? How does standing change over time? | Cohort definitions, point-in-time snapshots, reproducible comparisons | Feasible with modest scope; sampling matters |
| Organized league/friendly analysis | Which opponents and players perform across a competition? | Fixture joins, team identity, mode-specific outcomes | Needs external fixture context and reliable capture |
| The Grounds progression/session journal | Which activities support your progress? How do builds or sessions differ? | Combining manual and automated sources; provenance | Depends on manual logging unless new endpoints are confirmed |
| Static dataset modeling study | Can we produce reliable player-match metrics from existing raw data? | Profiling, dimensional modeling, transformation tests, reproducibility | Can start without live collection |

Leaderboard rows can include rank, skill rating, division, totals, goal averages, and nested club metadata. Some ranking-only fields can be absent, especially in searches. A selected-club cohort should not be presented as global coverage. [Ranking reference](https://github.com/alex-jordan547/proclubs-sdk/blob/main/docs/reference/rankings.mdx).

## 6. Proposed model and metric contracts

Conceptual flow: source responses / optional manual records → preserved raw observations → typed staging → match and snapshot models → documented metrics → reports. Tools and hosting remain undecided.

| Model | Proposed grain |
| --- | --- |
| Match | One edition + platform pool + match ID |
| Club-match | One match + participating club |
| Player-match | One match + club + source player ID |
| Player-match event count | One player-match + raw event ID; retain bucket provenance |
| Club snapshot | One club + observed time + source/stat scope |
| Member snapshot | One club member + observed time + source/stat scope |

Use surrogate keys only after source identity behavior is understood. Member snapshots may expose names without the same player IDs available in matches; do not silently join identities by display name. Formation and tactics should be manually logged if needed, until their source coverage is established.

Initial metrics could include completed-match win rate, goals for/against per match, player goals/assists per appearance, passing accuracy from summed completions/attempts, tackling success from summed successes/attempts, and rating trends by broad position. Keep league, playoff, and friendly results distinguishable. Include sample sizes and date coverage.

Metric rules to settle before implementation:

- Define DNF treatment and show a separate DNF count/rate.
- Calculate weighted ratios from counts rather than averaging player percentages.
- Return undefined/null when denominators are zero; missing fields are not automatically zero.
- Report ratings as game-generated ratings, not an independent measure of quality.
- Prefer per-appearance measures initially. Verify clock semantics before interpreting `secondsPlayed` as football minutes or publishing per-90 figures.
- Save opponent strength as observed at the time; today's rating is not the opponent's historical rating.
- Treat lineup or build comparisons as associations. Teammates, opposition, patches, and small samples confound causal claims.
- Keep reported source aggregates separate from totals computed from the captured match subset.

## 7. Next planning steps and decision gate

1. Confirm your platform, club name, preferred modes, and two or three questions you actually want answered.
2. Select a small source sample: your club's recent matches, or the published CSV if live access is inconvenient.
3. For a future read-only feasibility exercise, confirm club identity, access from the intended host, observed history window, publication lag, and field coverage. Compare a few known results with in-game records.
4. Write a compact data dictionary with grains, source scopes, null semantics, IDs, clocks, results, and mapping confidence.
5. Decide how missing history affects the project and whether live collection is worth maintaining.
6. Choose a minimal stack only after these findings. Local file storage and SQL are one candidate; managed warehouse tooling is another if demonstrating that stack is a portfolio goal. No stack has been selected.

Proposed feasibility pass criteria: confirmed target club; scores/outcomes and named player measures agree on a small known sample; repeated reads retain stable keys; field gaps are recorded; a realistic capture schedule fits the rolling window; and unavailable modes are excluded or supplied manually. If these fail, retain the static-dataset or manual-log scope.

## 8. What was and was not verified

Reviewed the user's Reddit thread, official EA mode/API announcements, both client repositories and targeted reference pages, the original event research, the dataset description/file listing, and two trackers' own descriptions. Prioritized source authors and official EA pages over third-party summaries.

No live EA endpoint was probed for your club, no full dataset was downloaded, and no tracker export was verified. The official rankings page could not be opened through the research browser. Access behavior, ten-match retention, mappings, and FC27 platform pools therefore remain attributed observations requiring a small club-specific check. No collector, dependencies, infrastructure, or application code was created.
