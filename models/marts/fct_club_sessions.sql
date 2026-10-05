select
    edition,
    platform_pool,
    club_alias,
    match_scope,
    session_number,
    min(played_at) as session_started_at,
    max(played_at) as last_match_at,
    count(*) as captured_matches,
    count(*) filter (where is_completed) as completed_matches,
    count(*) filter (where is_dnf) as dnf_matches,
    count(*) filter (where outcome = 'unknown') as unknown_outcomes,
    count(*) filter (where is_completed and outcome = 'win') as completed_wins,
    sum(goals_for) as goals_for,
    sum(goals_against) as goals_against,
    1.0 * count(*) filter (where is_completed and outcome = 'win')
    / nullif(count(*) filter (where is_completed), 0) as completed_win_rate
from {{ ref('fct_club_matches') }}
group by edition, platform_pool, club_alias, match_scope, session_number
