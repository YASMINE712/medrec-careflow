# Data handling

Original workspace CSVs are kept locally but ignored by Git until their source and redistribution rights are established. They are not patient records known to this project, but their provenance is unverified.

For a clean clone, run `python scripts/create_fixture.py`. It creates an explicitly synthetic workflow fixture with arbitrary labels and refuses to overwrite an existing Training.csv. The other original CSVs are unused by the new application.

Never place private health records in this directory. See docs/MODEL_CARD.md for evaluation limits.
