select
    edition,
    platform_pool,
    match_scope,
    club_alias,
    match_key,
    played_at,
    goals_for,
    goals_against,
    outcome,
    is_dnf,
    first_seen_at,
    last_seen_at
from {{ source('clubs', 'club_matches') }}
