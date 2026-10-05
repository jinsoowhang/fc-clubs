select match_key
from {{ ref('fct_club_role_matches') }}
where
    appearances <= 0
    or rated_appearances < 0 or rated_appearances > appearances
    or average_rating < 0 or average_rating > 10
    or pass_accuracy < 0 or pass_accuracy > 1
    or tackle_success_rate < 0 or tackle_success_rate > 1
    or (passes_attempted = 0 and pass_accuracy is not null)
    or (tackles_attempted = 0 and tackle_success_rate is not null)
