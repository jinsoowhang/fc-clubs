with totals as (
    select
        edition,
        platform_pool,
        club_alias,
        match_scope,
        sum(captured_matches) as session_matches,
        sum(completed_matches) as session_completed,
        sum(dnf_matches) as session_dnfs
    from {{ ref('fct_club_sessions') }}
    group by edition, platform_pool, club_alias, match_scope
)

select m.club_alias
from {{ ref('mart_club_performance') }} as m
left join totals as t
    on
        m.edition = t.edition and m.platform_pool = t.platform_pool
        and m.club_alias = t.club_alias and m.match_scope = t.match_scope
where
    t.session_matches is null
    or m.captured_matches <> t.session_matches
    or m.completed_matches <> t.session_completed
    or m.dnf_matches <> t.session_dnfs
