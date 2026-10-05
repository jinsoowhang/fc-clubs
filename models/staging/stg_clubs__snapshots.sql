select
    edition,
    platform_pool,
    club_alias,
    observed_at,
    reported_games,
    reported_wins,
    reported_draws,
    reported_losses,
    reported_goals_for,
    reported_goals_against,
    skill_rating
from {{ source('clubs', 'club_snapshots') }}
