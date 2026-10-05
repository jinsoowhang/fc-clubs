select
    edition,
    platform_pool,
    club_alias,
    match_scope,
    checked_at,
    status,
    returned_matches
from {{ source('clubs', 'collection_checks') }}
