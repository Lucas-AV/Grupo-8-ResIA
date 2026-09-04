# Schema compatibility

The final `data/processed/dataset.csv` keeps the existing columns. The first unnamed
column is a sequential file index kept for compatibility with current scripts.

Required logical columns are `track_id`, `artists`, `album_name`, `track_name`,
`popularity`, `duration_ms`, `explicit`, all audio features, `time_signature`
and `track_genre`.

For the 2025 source, `artist_names` becomes `artists`, `main_genres` becomes
`track_genre`, `|` between artists becomes `;`, and `0`/`1` explicit values
become `False`/`True`. Multiple genres create one row per genre. No missing
value is invented.
