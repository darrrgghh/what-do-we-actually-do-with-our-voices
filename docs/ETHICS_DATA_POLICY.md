# Ethics and Data Policy

## Human-subject data handling

This project includes interview and survey materials from human participants.
All publication-facing outputs must be de-identified before release.

## Restricted data classes

- Direct identifiers: names, emails, IP addresses, exact geolocation
- Indirect identifiers: free-text self-disclosure that can re-identify a participant
- Raw media: source audio and full raw transcripts

These materials remain local and are excluded by `.gitignore`.

## Public data classes

- De-identified participant IDs (e.g., `A`-`R`, `QX_###`)
- Aggregated statistics and summary tables
- Coded excerpts reviewed for identifiability risk
- Reproducible scripts that do not embed private data

## IRB and compliance notes

- Maintain IRB protocol metadata in manuscript and submission package.
- Do not upload raw consent-linked datasets to public repositories.
- Any quote in manuscript must be reviewed for residual identification risk.

## Release checklist

Before public release:

1. Remove direct identifiers from all CSV/TSV files.
2. Remove exact geolocation and IP columns.
3. Replace personal names in text excerpts where needed.
4. Verify `git status` does not include restricted files.
5. Re-run pipeline from approved de-identified inputs.

