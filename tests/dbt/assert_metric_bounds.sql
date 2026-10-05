select
    club_alias,
    match_scope
from {{ ref('mart_club_performance') }}
where
    completed_matches > captured_matches
    or dnf_matches > captured_matches
    or completed_wins > completed_matches
    or completed_win_rate < 0 or completed_win_rate > 1
    or dnf_rate < 0 or dnf_rate > 1
    or goals_for_per_match < 0 or goals_against_per_match < 0
