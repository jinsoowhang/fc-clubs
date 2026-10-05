select
    edition,
    platform_pool,
    club_alias,
    match_scope,
    cast(played_at at time zone 'UTC' as date) as played_date,
    count(*) as captured_matches,
    count(*) filter (where is_completed) as completed_matches,
    count(*) filter (where is_completed and outcome = 'win') as completed_wins,
    count(*) filter (where is_dnf) as dnf_matches,
    sum(goals_for) as goals_for,
    sum(goals_against) as goals_against,
    1.0 * count(*) filter (where is_completed and outcome = 'win')
    / nullif(count(*) filter (where is_completed), 0) as completed_win_rate
from {{ ref('fct_club_matches') }}
group by edition, platform_pool, club_alias, match_scope, played_date
