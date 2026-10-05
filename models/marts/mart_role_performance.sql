with role_totals as (
    select
        edition,
        platform_pool,
        club_alias,
        match_scope,
        role,
        count(*) as captured_role_matches,
        sum(appearances) as appearances,
        sum(rated_appearances) as rated_appearances,
        sum(rating_sum) as rating_sum,
        {{ known_sum('goals') }} as goals,
        {{ known_sum('assists') }} as assists,
        {{ known_sum('shots') }} as shots,
        {{ known_sum('passes_completed') }} as passes_completed,
        {{ known_sum('passes_attempted') }} as passes_attempted,
        {{ known_sum('tackles_completed') }}
            as tackles_completed,
        {{ known_sum('tackles_attempted') }}
            as tackles_attempted,
        {{ known_sum('saves') }} as saves
    from {{ ref('fct_club_role_matches') }}
    group by edition, platform_pool, club_alias, match_scope, role
)

select
    edition,
    platform_pool,
    club_alias,
    match_scope,
    role,
    captured_role_matches,
    appearances,
    rated_appearances,
    rating_sum / nullif(rated_appearances, 0) as average_rating,
    goals,
    assists,
    shots,
    passes_completed,
    passes_attempted,
    tackles_completed,
    tackles_attempted,
    saves,
    1.0 * passes_completed / nullif(passes_attempted, 0) as pass_accuracy,
    1.0 * tackles_completed / nullif(tackles_attempted, 0) as tackle_success_rate
from role_totals
