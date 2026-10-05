select
    edition,
    platform_pool,
    club_alias,
    match_scope,
    count(*) as captured_matches,
    count(*) filter (where is_completed) as completed_matches,
    count(*) filter (where is_dnf) as dnf_matches,
    count(*) filter (where outcome = 'unknown') as unknown_outcomes,
    count(*) filter (where is_completed and outcome = 'win') as completed_wins,
    1.0 * count(*) filter (where is_completed and outcome = 'win')
    / nullif(count(*) filter (where is_completed), 0) as completed_win_rate,
    1.0 * count(*) filter (where is_dnf) / count(*) as dnf_rate,
    1.0 * sum(goals_for) / count(*) as goals_for_per_match,
    1.0 * sum(goals_against) / count(*) as goals_against_per_match,
    min(played_at) as first_captured_match_at,
    max(played_at) as last_captured_match_at
from {{ ref('fct_club_matches') }}
group by edition, platform_pool, club_alias, match_scope
