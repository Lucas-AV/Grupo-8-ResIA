# ETL process

1. Keep every downloaded source unchanged in `data/raw`.
2. Run `python scripts/etl/enrich_dataset.py`.
3. The script checks fields and values, creates normalized source files in
   `data/processed`, removes exact repeated track-and-genre pairs, and writes
   the final `data/processed/dataset.csv`.
4. Run `python scripts/hygiene/validate_dataset.py`.
5. Read the files in `data/hygiene` before accepting a new run.

The current source always wins when the same track and genre exist in more
than one input. The same track can stay in different genres.
