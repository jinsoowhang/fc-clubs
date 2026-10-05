select
    *,
    1.0 * rating_sum / nullif(rated_appearances, 0) as average_rating,
    1.0 * passes_completed / nullif(passes_attempted, 0) as pass_accuracy,
    1.0 * tackles_completed / nullif(tackles_attempted, 0) as tackle_success_rate
from {{ ref('stg_clubs__role_matches') }}
