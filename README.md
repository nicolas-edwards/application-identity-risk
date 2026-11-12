# application-identity-risk
 
This repository shares an example of the kind of fraud work I have done in the past.
 
It models first-line identity risk screening when a customer applies for an account: application details are compared against a synthetic identity database. It does not cover transaction monitoring, account takeover, or post-onboarding fraud.
 
## How to run
 
1. Build the reference identities (one-time setup, driven by `config/reference_identities.yaml`):
   `uv run python scripts/build_reference_identities.py` → `data/reference/reference_identities.csv`
2. Generate applications and labels (repeatable, driven by `config/applications.yaml`):
   `uv run python -m application_identity_risk.scenarios.generate_applications` → `data/scenario/latest/`
   To keep a dataset instead of replacing `latest`, name it: `--dataset households_800` → `data/scenario/households_800/`.
## Data
 
### Reference identities
 
A pool of synthetic people: `identity_id`, name, full address, phone, latitude and longitude. Every geographic field of an identity comes from one row of `data/reference/locations.csv` (city, state, zip prefix, area code, coordinates), so they always agree. Identities are independent of one another; any sharing between applications is introduced by the application generator.
 
### Groups
 
Every application belongs to a group. A group is a set of applications that share some attribute values, and fraud and legitimate groups are produced by the same mechanism.
 
`config/applications.yaml` lists **group profiles**. Each profile is a recipe for one kind of group:
 
- `label`: legitimate or fraud.
- `groups_to_create`: how many groups the profile produces.
- `applications_per_group`: applications per group, each using a distinct identity (a number, or a `[min, max]` range).
- `pool_sizes`: which attributes the group's applications share, and how many distinct values they share. The group's first members supply the shared values; the other members draw from them. Attributes left out stay each applicant's own.
- `start_date` + `duration_days` (optional): the group's time window. The default is the whole application window.
V1 profiles:
 
| Profile | Label | Applications per group | Shares |
|---|---|---|---|
| individual | legitimate | 1 | nothing |
| household | legitimate | 2–4 | one address |
| ring | fraud | 6–30 | a few addresses and phones, within a short window |
 
Legitimate and fraud counts, and the fraud rate, are outcomes of the profiles. The generator reports them.
 
### Outputs
 
Each generated scenario is a self-contained folder, `data/scenarios/<dataset>/`:
 
- `applications.csv`: `application_datetime, account_id, identity_id, first_name, middle_name, last_name, address, city, state, latitude, longitude, zip_code, phone`
- `labels.csv`: `account_id, is_fraud, group_profile, group_id`, written separately from applications so ground truth cannot leak into features. Labels are treated as complete and available for this version; label delay is out of scope.
- `applications.yaml`: a snapshot of the config that produced the dataset.
- `data_digest.json`: a SHA-256 fingerprint of `applications.csv` and `labels.csv`. Model runs record the dataset name and this digest, so every result can be traced to the exact data it used. Generation is reproducible, so the same config and code give the same digest.
`data/scenario/index.json` lists the scenario. Everything derived from a dataset (its report, features, join statistics) is written inside its folder.
 
The generator stops before writing if the config is invalid, if group IDs repeat, or if there are not enough reference identities. After generating, it reports applications by profile, the fraud rate, and the share of legitimate and fraud applications that share an address with another application.
 
### Planned feature sources
 
- `name_address`: `{observed_at, name, address}`
- `cookie`: `{observed_at, cookie_id, ip?, address?}`
- `ip_attributes`: `{observed_at, ip, asn, geo_location}`
Cookie and IP will be added as pooled attributes, so that every value has an owner: a person, a household, a device, or a shared network such as a mobile carrier.
 
## File format conventions
 
Each file's format follows from who writes it and who reads it:
 
- **YAML** for files people write: configuration (`config/*.yaml`).
- **JSON** for outputs that code writes and that are not row-level: reports, dataset digests, join statistics.
- **CSV** for row-level data: reference identities, applications, labels, features.
## Features
 
All sources are combined into linkage indicators (for example, how many earlier applications share this full address or phone). Linkage counts are point-in-time: each application only sees applications that came before it.
 
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
 
Implemented: reference identities; group-based application and label generation (address and phone).
 
Next: a dataset report, linkage features, then the model and evaluation. Cookie and IP attributes come after v1.
 
Out of scope for v1: noise and typos in identities, roommates and repeat applicants, synthetic identities, rolling-window features, label delay. Precision-based results depend on the fraud rate, which is reported alongside them.
 
### Known limitations, slated for the next round
 
- **Random draws are shared across groups.** All groups draw from one seeded random stream, in config order. A dataset is fully reproducible, but changing one group profile (for example, adding households) shifts the random values every later group receives, including which identities, pool picks and timestamps it gets. Next round: give each group its own random stream derived from the seed and its `group_id`, and allocate identities per group, so that changing one profile leaves the others unchanged.
- **Household members apply independently in time.** Their application times are spread over the whole window rather than clustered.
- **Locations are few and approximate.** Nine cities, with coordinates entered by hand: consistent with each other, not verified against a map.

## License

Source-available under the [Business Source License 1.1](LICENSE). You are free to read, run, modify and evaluate this project for non-production use. Production use is not permitted. On 2030-11-11, the license converts to the Apache License 2.0.
