# Dataset research

## Sources used together

| Source | Decision | Why |
| --- | --- | --- |
| Maharshi Pandya — Spotify Tracks Dataset | Used | Complete schema, 114,000 rows, audio features and track genres. |
| Serkan Tüysüz — Top 10K Spotify Songs 2025 | Used | Recent and independent collection with track ID, album, explicit flag and audio features. Its `main_genres` field is mapped to `track_genre`. |

## Sources not merged

| Candidate | Decision | Why |
| --- | --- | --- |
| 114K Kaggle republishers | Rejected | Copies of the Maharshi source; they add no tracks after deduplication. |
| Spotify 1Million Tracks | Rejected | Does not contain `album_name` or `explicit`. |
| 30K Spotify Songs | Rejected | Does not contain `explicit` or `time_signature`; playlist genre also has a different meaning. |
| Ultimate Spotify Tracks DB | Rejected | Missing album and explicit fields and has unclear reuse terms. |
| Weekly Spotify Tracks | Rejected | Missing `explicit` and `track_genre`. |

The ETL uses only accepted sources. A future candidate must pass the same
schema and provenance checks before it is added.
