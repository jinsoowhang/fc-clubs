with ordered_checks as (
    select
        *,
        row_number() over (
            partition by edition, platform_pool, club_alias, match_scope
            order by checked_at desc
        ) as observation_rank
    from {{ ref('stg_clubs__collection_checks') }}
)

select
    edition,
    platform_pool,
    club_alias,
    match_scope,
    checked_at as last_checked_at,
    status as latest_status,
    returned_matches,
    status = 'window_full' as history_gap_possible
from ordered_checks
where observation_rank = 1
