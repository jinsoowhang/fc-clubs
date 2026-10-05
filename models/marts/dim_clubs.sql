select distinct
    edition,
    platform_pool,
    club_alias
from (
    select
        edition,
        platform_pool,
        club_alias
    from {{ ref('stg_clubs__matches') }}
    union all
    select
        edition,
        platform_pool,
        club_alias
    from {{ ref('stg_clubs__snapshots') }}
    union all
    select
        edition,
        platform_pool,
        club_alias
    from {{ ref('stg_clubs__collection_checks') }}
)
