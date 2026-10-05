select r.match_key
from {{ ref('fct_club_role_matches') }} as r
left join {{ ref('fct_club_matches') }} as m
    on
        r.edition = m.edition
        and r.platform_pool = m.platform_pool
        and r.match_scope = m.match_scope
        and r.club_alias = m.club_alias
        and r.match_key = m.match_key
where m.match_key is null
