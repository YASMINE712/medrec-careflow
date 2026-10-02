# Model card

## Intended use

An educational example of the software path from symptoms to a clinician-only experimental suggestion. It must not guide diagnosis, emergency triage, medication choice, or patient treatment.

## Training and ETL

Input: local `data/Training.csv`, binary symptom columns and a `prognosis` label. Pandas deterministically renames duplicate headers (the original has two `fluid_overload` columns); the exported feature list is authoritative. Full duplicate rows are removed before the 75/25 stratified split, seed 42. Conflicting labels for identical feature vectors stop training. Logistic regression uses max_iter=2000 and is compared with a most-frequent dummy classifier. No hyperparameter selection is performed against the holdout. Exported coefficients are from the training partition, not refitted on test data.

Original local data audit: 4,920 rows; 4,616 duplicates removed; 304 unique rows; 132 features; 41 labels; 228 training rows; 76 holdout rows. Internal accuracy and macro F1 are both 1.0. Small template-like data explain why this is not a meaningful clinical performance claim. No patient identifiers or independent patient groups are available for patient-level splitting.

Public clones and CI use an authored synthetic fixture with arbitrary A/B/C labels. Those labels carry no medical meaning. The fixture exists to exercise ETL, inference, and application integration without redistributing unlicensed data.

## Outputs and safeguards

One top-ranked label is visible to clinicians only. No numerical confidence is presented, as calibration has not been assessed. Patient summaries require independently entered clinician text. Medication, diet and exercise CSV recommendations from the original app are not used. The model cannot assess urgency or unknown conditions. Missing model files produce an explicit unavailable state.

## Limitations

Dataset provenance, representativeness, collection protocol and redistribution rights are unverified. No external, prospective, fairness, calibration or robustness validation has been performed. Exact deduplication does not eliminate template-family leakage. No clinical or regulatory readiness is claimed. Deep learning is not warranted for this dataset.

## Reproducibility

Run `python -m ml.train`. `ml/artifacts/metrics.json` records SHA-256 of the input, partition counts, seed, class ordering, metrics, and confusion matrix. `model.json` stores feature order and coefficients without executable pickle content. Restart the app after retraining. Dependency ranges are maintained and audited; use a reviewed lockfile for a specific production release.
