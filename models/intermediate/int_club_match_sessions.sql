with previous_matches as (
    select
        *,
        lag(played_at) over (
            partition by edition, platform_pool, club_alias, match_scope
            order by played_at, match_key
        ) as previous_played_at
    from {{ ref('stg_clubs__matches') }}
),

session_boundaries as (
    select
        *,
        case
            when previous_played_at is null then 1
            when
                played_at > previous_played_at + interval '{{ var("session_gap_minutes") }} minutes'
                then 1
            else 0
        end as starts_session
    from previous_matches
)

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
    last_seen_at,
    sum(starts_session) over (
        partition by edition, platform_pool, club_alias, match_scope
        order by played_at, match_key
        rows between unbounded preceding and current row
    ) as session_number
from session_boundaries
