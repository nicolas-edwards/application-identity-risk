"""Generate synthetic account applications and their labels from groups.
 
Every application belongs to a group (an individual, a household, a fraud ring).
Fraud and legitimate groups go through the same steps:
  1. shuffle the reference identities once with the config seed,
  2. give each group the next identities in the shuffled list, one per application,
  3. for each pooled attribute, the group's first members keep their own values and
     become the pool; the remaining members draw from that pool,
  4. assign timestamps within the group's window (default: the whole application window),
  5. write applications.csv, labels.csv and a config snapshot into a run folder.
 
Run from the project root:
    uv run python -m application_identity_risk.generation.generate_applications
    uv run python -m application_identity_risk.generation.generate_applications --run run_03
 
Without --run, the output goes to data/runs/latest/ and replaces the previous one.
"""
 
import argparse
import json
import shutil
import sys
import uuid
from pathlib import Path
 
import numpy as np
import pandas as pd
import yaml
 
CONFIG_PATH = Path("config/applications.yaml")
SCRIPT_NAME = Path(__file__).name
DEFAULT_RUN_NAME = "latest"
 
# Poolable attributes, and the columns that travel together when one is shared
POOLABLE_ATTRIBUTES = {
    "address": ["address", "city", "state", "zip_code"],
    "phone": ["phone"],
}
IDENTITY_COLUMNS = ["identity_id", "first_name", "middle_name", "last_name",
                    "address", "city", "state", "zip_code", "phone"]
VALID_LABELS = {"legitimate", "fraud"}
FRAUD_RATE_RANGE = (0.001, 0.02)  # warn outside this range
 
 
def fail(message: str) -> None:
    """Stop on an expected, explainable problem (bad config, missing input).
 
    Prints the message to stderr and exits with status 1, without a traceback.
    Unexpected errors are not routed here; they raise normally, with a traceback.
    """
    sys.exit(f"ERROR [{SCRIPT_NAME}]: {message}")
 
 
# ---------------------------------------------------------------- inputs
 
def load_config(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)
 
 
def load_identities(path: Path) -> pd.DataFrame:
    if not path.exists():
        fail(f"{path} not found. Run scripts/build_reference_identities.py first.")
    identities = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [column for column in IDENTITY_COLUMNS if column not in identities.columns]
    if missing:
        fail(f"{path} was expected to contain columns {IDENTITY_COLUMNS}, "
             f"instead contained the following columns {list(identities.columns)}, "
             f"missing {missing}. Rebuild it with scripts/build_reference_identities.py.")
    if not identities["identity_id"].is_unique:
        fail(f"{path} contains duplicate identity_id values; rebuild it.")
    return identities
 
 
def validate_group_specs(config: dict) -> None:
    window_start = pd.Timestamp(config["application_window"]["start_date"])
    window_end = pd.Timestamp(config["application_window"]["end_date"])
 
    for position, spec in enumerate(config["group_profiles"], start=1):
        name = spec.get("group_id", f"group_profiles entry {position} ({spec.get('profile')})")
 
        if spec.get("label") not in VALID_LABELS:
            fail(f"{name}: label was expected to be one of {sorted(VALID_LABELS)}, "
                 f"instead was {spec.get('label')!r}")
 
        if "group_id" in spec and spec["groups_to_create"] != 1:
            fail(f"{name}: group_id can only be set when groups_to_create is 1, "
                 f"instead groups_to_create was {spec['groups_to_create']}")
 
        smallest_group, _ = application_count_range(spec)
        if smallest_group < 1:
            fail(f"{name}: applications_per_group must be at least 1")
 
        for attribute, pool_size in spec.get("pool_sizes", {}).items():
            if attribute not in POOLABLE_ATTRIBUTES:
                fail(f"{name}: pool_sizes was expected to use attributes "
                     f"{sorted(POOLABLE_ATTRIBUTES)}, instead contained {attribute!r}")
            if not 1 <= pool_size <= smallest_group:
                fail(f"{name}: pool size for {attribute} was expected to be between 1 and "
                     f"the smallest group size ({smallest_group}), instead was {pool_size}")
 
        if "start_date" in spec:
            group_start = pd.Timestamp(spec["start_date"])
            group_end = group_start + pd.Timedelta(days=spec["duration_days"])
            if group_start < window_start or group_end > window_end:
                fail(f"{name}: window {group_start.date()} to {group_end.date()} was expected "
                     f"to fall inside the application window "
                     f"{window_start.date()} to {window_end.date()}")
 
 
def application_count_range(spec: dict) -> tuple[int, int]:
    """(min, max) applications per group: a number, or a [min, max] pair."""
    applications_per_group = spec["applications_per_group"]
    if isinstance(applications_per_group, list):
        return applications_per_group[0], applications_per_group[1]
    return applications_per_group, applications_per_group
 
 
# ---------------------------------------------------------------- generation
 
def seeded_uuids(rng: np.random.Generator, num_ids: int) -> list[str]:
    """UUID4s drawn from the seeded generator, so reruns give the same IDs."""
    return [str(uuid.UUID(bytes=rng.bytes(16), version=4)) for _ in range(num_ids)]
 
 
def random_times(rng: np.random.Generator, start: str, days: float,
                 num_timestamps: int) -> pd.Series:
    """Timestamps uniform over [start, start + days), to the second."""
    seconds = rng.uniform(0, days * 86400, size=num_timestamps).astype("int64")
    return pd.Timestamp(start) + pd.to_timedelta(seconds, unit="s")
 
 
def plan_groups(rng: np.random.Generator, config: dict) -> list[dict]:
    """Decide every group's id and size before any identity is used."""
    planned_groups = []
    for spec in config["group_profiles"]:
        min_size, max_size = application_count_range(spec)
        for group_number in range(1, spec["groups_to_create"] + 1):
            planned_groups.append({
                "spec": spec,
                "group_id": spec.get("group_id", f"{spec['profile']}_{group_number}"),
                "num_applications": int(rng.integers(min_size, max_size + 1)),
            })
 
    group_ids = pd.Series([group["group_id"] for group in planned_groups])
    duplicated_ids = sorted(group_ids[group_ids.duplicated()].unique())
    if duplicated_ids:
        fail(f"group_id values were expected to be unique across all group_profiles, "
             f"instead these repeat: {duplicated_ids}. Give each profile a distinct "
             f"profile name or group_id.")
    return planned_groups
 
 
def build_group_records(rng: np.random.Generator, group: dict, members: pd.DataFrame,
                        window: dict) -> pd.DataFrame:
    """One group's applications: shared attributes come from its own first members."""
    spec = group["spec"]
    group_records = members.copy()
    num_applications = group["num_applications"]
 
    for attribute, pool_size in spec.get("pool_sizes", {}).items():
        columns = POOLABLE_ATTRIBUTES[attribute]
        pool = members[columns].iloc[:pool_size]
        num_borrowers = num_applications - pool_size
        if num_borrowers > 0:
            picks = rng.integers(0, pool_size, size=num_borrowers)
            group_records.iloc[pool_size:, group_records.columns.get_indexer(columns)] = \
                pool.iloc[picks].to_numpy()
 
    start_date = spec.get("start_date", window["start_date"])
    duration_days = spec.get("duration_days", window_length_days(window))
    group_records["application_datetime"] = random_times(
        rng, start_date, duration_days, num_applications).to_numpy()
    group_records["is_fraud"] = spec["label"] == "fraud"
    group_records["group_profile"] = spec["profile"]
    group_records["group_id"] = group["group_id"]
    return group_records
 
 
def window_length_days(window: dict) -> int:
    return (pd.Timestamp(window["end_date"]) - pd.Timestamp(window["start_date"])).days
 
 
# ---------------------------------------------------------------- outputs
 
def write_run(run_dir: Path, applications: pd.DataFrame, labels: pd.DataFrame) -> None:
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    applications.to_csv(run_dir / "applications.csv", index=False)
    labels.to_csv(run_dir / "labels.csv", index=False)
    shutil.copy(CONFIG_PATH, run_dir / CONFIG_PATH.name)
 
    index_path = run_dir.parent / "index.json"
    run_names = json.loads(index_path.read_text()) if index_path.exists() else []
    if run_dir.name not in run_names:
        run_names.append(run_dir.name)
    index_path.write_text(json.dumps(sorted(run_names), indent=2) + "\n")
 
 
def print_summary(run_dir: Path, applications: pd.DataFrame, labels: pd.DataFrame) -> None:
    combined = applications.merge(labels, on="account_id")
    fraud_rate = combined["is_fraud"].mean()
 
    print(f"Wrote {len(applications)} applications to {run_dir}/")
    by_type = (combined.groupby(["group_profile", "is_fraud"])
               .agg(groups=("group_id", "nunique"), applications=("account_id", "size")))
    print(by_type.to_string())
    print(f"fraud rate: {fraud_rate:.2%}")
 
    # honesty check: how often does each label share a full address with another application?
    address_counts = combined.groupby(POOLABLE_ATTRIBUTES["address"])["account_id"].transform("size")
    combined["shares_address"] = address_counts > 1
    for is_fraud, share in combined.groupby("is_fraud")["shares_address"].mean().items():
        label = "fraud" if is_fraud else "legitimate"
        print(f"{label} applications sharing a full address: {share:.1%}")
 
    low, high = FRAUD_RATE_RANGE
    if not low <= fraud_rate <= high:
        print(f"WARNING: fraud rate {fraud_rate:.2%} is outside {low:.1%} to {high:.0%}")
 
 
# ---------------------------------------------------------------- main
 
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", default=DEFAULT_RUN_NAME,
                        help=f"run folder name under runs_dir (default: {DEFAULT_RUN_NAME})")
    run_name = parser.parse_args().run
 
    config = load_config(CONFIG_PATH)
    validate_group_specs(config)
    rng = np.random.default_rng(config["random_seed"])
    identities = load_identities(Path(config["paths"]["reference_identities"]))
 
    planned_groups = plan_groups(rng, config)
    num_applications_needed = sum(group["num_applications"] for group in planned_groups)
    if num_applications_needed > len(identities):
        fail(f"config needs {num_applications_needed} identities, "
             f"reference file has {len(identities)}")
 
    shuffled = identities.sample(frac=1, random_state=rng).reset_index(drop=True)
    window = config["application_window"]
    all_group_records = []
    next_identity_position = 0
    for group in planned_groups:
        members = shuffled.iloc[next_identity_position:
                                next_identity_position + group["num_applications"]]
        next_identity_position += group["num_applications"]
        all_group_records.append(build_group_records(rng, group, members, window))
 
    combined = (pd.concat(all_group_records)
                .sort_values("application_datetime", kind="stable")
                .reset_index(drop=True))
    combined["account_id"] = seeded_uuids(rng, len(combined))
 
    applications = combined[["application_datetime", "account_id", *IDENTITY_COLUMNS]]
    labels = combined[["account_id", "is_fraud", "group_profile", "group_id"]]
 
    # checks before writing
    if not (len(applications) == len(labels) == num_applications_needed):
        fail("applications and labels row counts do not match the planned groups")
    if not applications["account_id"].is_unique:
        fail("duplicate account_id values")
    if not applications["identity_id"].is_unique:
        fail("an identity was used in more than one application")
 
    run_dir = Path(config["paths"]["runs_dir"]) / run_name
    write_run(run_dir, applications, labels)
    print_summary(run_dir, applications, labels)
 
 
if __name__ == "__main__":
    main()
 
