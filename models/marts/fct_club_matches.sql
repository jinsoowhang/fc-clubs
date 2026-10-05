select
    *,
    not is_dnf and outcome in ('win', 'draw', 'loss') as is_completed,
    goals_for - goals_against as goal_difference
from {{ ref('int_club_match_sessions') }}
