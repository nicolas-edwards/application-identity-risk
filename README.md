# application-identity-risk

This repository shares an example of the kind of fraud work I have done in the past.

It models first-line identity risk screening when a customer applies for an account: application details are compared against a synthetic identity database. It does not cover transaction monitoring, account takeover, or post-onboarding fraud.

## How to run

1. Build the reference identities (one-time setup):
   `uv run python scripts/build_ref_identities.py` → `data/ref/reference_identities.csv`
2. Generate applications and labels (repeatable, driven by `config/generator.yaml`):
   `uv run python -m application_identity_risk.generation.generate_fraud_data` → `data/raw/`

## Data

Every data source has a parametrizable synthetic generator. Fraud is designed as fraud rings: each ring shares a small pool of addresses and phones across its applications, within a defined time window. The overall fraud rate is an outcome of the ring definitions, and the generator reports it.

- **Applications**: `{application_datetime, account_id, identity_id, name, address, phone, cookie, ip}`
- **Labels**: `{account_id, is_fraud, fraud_ring_id}`, written separately from applications. Labels are treated as complete and available for this version; label delay is out of scope.

Planned feature sources:

- `name_address`: `{observed_at, name, address}`
- `cookie`: `{observed_at, cookie_id, ip?, address?}`
- `ip_attributes`: `{observed_at, ip, asn, geo_location}`

## Features

All sources are combined into linkage indicators (e.g. how many earlier applications share this address or phone). Linkage counts are point-in-time: each application only sees applications that came before it.

Joins are monitored on input and output to verify that no rows are lost or duplicated.

A visual shows how each feature sorts the population into higher and lower fraud-rate groups.

## Model and evaluation

- Train/test splits: random, and past/present (time cutoff).
- Model: XGBoost.
- Scoring: applications after the cutoff are scored in batches, and scoring time is measured.
- Outputs (CSV):
  - PR curve points
  - ROC curve points
  - Recall and sample size at N% precision, for N in 1%, 2%, … 99%

## Status and deliberate v1 omissions

Implemented: reference identity generation. In progress: application/label generator (applications and phones/addresses only; cookie and IP come next).

Out of scope for v1: noise and typos in identities, households and other legitimate shared attributes, synthetic identities, rolling-window features, label delay. Precision-based results depend on the fraud rate, which is reported alongside them.