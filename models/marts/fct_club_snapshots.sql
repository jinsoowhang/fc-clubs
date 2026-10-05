select
    *,
    'source_overall' as stat_scope
from {{ ref('stg_clubs__snapshots') }}
