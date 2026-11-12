import csv
import random
import uuid
import yaml
from pathlib import Path
from typing import Dict, List, Tuple


# Input files
CONFIG_PATH = Path("config/identities.yaml")
LOCATIONS_PATH = Path("data/reference/locations.csv")

#Output files
OUTPUT_PATH = Path("data/identities/identities.csv")


# Bunch of hardcoded names for the first prototype. 
# In some future version, these will be sourced and sample from actual Census data.


# Name pools with realistic distributions
first_names = [
    "James", "John", "Robert", "Michael", "William",
    "David", "Richard", "Joseph", "Thomas", "Charles",
    "Christopher", "Daniel", "Matthew", "Anthony", "Mark",
    "Donald", "Steven", "Paul", "Andrew", "Joshua",
    "Kenneth", "Kevin", "Brian", "George", "Timothy",
    "Edward", "Ronald", "Jason", "Jeffrey", "Ryan",
    "Jacob", "Gary", "Nicholas", "Eric", "Jonathan",
    "Stephen", "Larry", "Justin", "Scott", "Brandon",
    "Benjamin", "Samuel", "Gregory", "Frank", "Peter",
    "Jack", "Dennis", "Jerry", "Tyler", "Aaron",
    "Nathan", "Henry", "Jacob", "Austin", "Jose",
    "Adam", "Nathan", "Zachary", "Douglas", "Henry"
]

last_names = [
    "Smith", "Johnson", "Williams", "Brown", "Jones",
    "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris",
    "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright",
    "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall",
    "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
    "Turner", "Phillips", "Cruz", "Edwards", "Collins",
    "Stewart", "Morris", "Morris", "Murphy", "Cook"
]

street_types = [
    "Street", "Avenue", "Boulevard", "Lane", "Drive",
    "Road", "Court", "Way", "Circle", "Place",
    "Parkway", "Trail", "Cove", "Vista", "Heights",
    "Grove", "Hill", "Meadow", "Valley", "Ridge",
    "Brook", "Creek", "Summit", "Corner", "Crossing"
]

# Middle names mapping (kept for identity generation)
middle_names = {
    "James": "Alexander", "John": "Michael", "Robert": "James",
    "Michael": "John", "William": "Edward", "David": "Alexander",
    "Richard": "James", "Joseph": "Anthony", "Thomas": "James",
    "Charles": "William", "Christopher": "James", "Daniel": "James",
    "Matthew": "James", "Anthony": "Paul", "Mark": "Anthony",
    "Donald": "James", "Steven": "James", "Paul": "James",
    "Andrew": "James", "Joshua": "James", "Kenneth": "James",
    "Kevin": "James", "Brian": "James", "George": "James",
    "Timothy": "James", "Edward": "James", "Ronald": "James",
    "Jason": "James", "Jeffrey": "James", "Ryan": "James",
    "Jacob": "James", "Gary": "James", "Nicholas": "James",
    "Eric": "James", "Jonathan": "James", "Stephen": "James",
    "Larry": "James", "Justin": "James", "Scott": "James",
    "Brandon": "James", "Benjamin": "James", "Samuel": "James",
    "Gregory": "James", "Frank": "James", "Peter": "James",
    "Jack": "James", "Dennis": "James", "Jerry": "James",
    "Tyler": "James", "Aaron": "James", "Nathan": "James",
    "Henry": "James", "Austin": "James", "Jose": "Jose",
    "Adam": "James", "Zachary": "James", "Douglas": "Douglas"
}

# State abbreviations (kept for reference)
state_abbreviations = {
    "California": "CA", "Texas": "TX", "Florida": "FL", "New York": "NY",
    "Illinois": "IL", "Pennsylvania": "PA", "Ohio": "OH", "Georgia": "GA",
    "North Carolina": "NC", "Michigan": "MI", "New Jersey": "NJ",
    "Virginia": "VA", "Washington": "WA", "Arizona": "AZ", "Massachusetts": "MA",
    "Tennessee": "TN", "Indiana": "IN", "Missouri": "MO", "Maryland": "MD",
    "Wisconsin": "WI", "Colorado": "CO", "Minnesota": "MN", "Oregon": "OR",
    "South Carolina": "SC", "Alabama": "AL", "Louisiana": "LA", "Kentucky": "KY",
    "Oklahoma": "OK", "Connecticut": "CT", "Utah": "UT", "Iowa": "IA",
    "Mississippi": "MS", "Arkansas": "AR", "Nevada": "NV", "Nebraska": "NE",
    "Idaho": "ID", "New Hampshire": "NH", "Hawaii": "HI", "Maine": "ME",
    "Vermont": "VT", "Delaware": "DE", "Rhode Island": "RI"
}

def load_config(CONFIG_PATH) -> Dict:
    """Load configuration from YAML file, with defaults."""
    config_path = Path(CONFIG_PATH)
    config = {"not_read":-1}
    if config_path.exists():
        with open(config_path, "r") as f:
            config.update(yaml.safe_load(f) or {})
    return config


def generate_address() -> str:
    """Generate a random street address (street_number + street_type)."""
    street_type = random.choice(street_types)
    street_number = random.randint(100, 9999)
    return f"{street_number} {street_type}"


def generate_phone(area_code: str) -> str:
    """Generate a phone number from the given area code."""
    exchange = random.randint(100, 999)
    line_number = random.randint(1000, 9999)
    return f"({area_code}) {exchange}-{line_number}"


def load_locations(filepath: str = LOCATIONS_PATH) -> List[Dict]:
    """
    Load locations from a CSV file.
    
    Expected columns: city, state, zip_prefix, area_code, latitude, longitude, weight
    
    Returns a list of dicts keyed by city for weighted random selection.
    """
    locations = []
    with open(filepath, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            locations.append({
                "city": row["city"],
                "state": row["state"],
                "zip_prefix": row["zip_prefix"],
                "area_code": row["area_code"],
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "weight": float(row["weight"]) if row["weight"] else 1.0,
            })
    return locations


def weighted_choice(locations: List[Dict]) -> Dict:
    """Select a random location from the list using weighted probabilities."""
    weights = [loc["weight"] for loc in locations]
    total_weight = sum(weights)
    normalized = [w / total_weight for w in weights]
    return random.choices(locations, weights=normalized, k=1)[0]


def generate_zip(zip_prefix: str) -> str:
    """
    Generate a full zip code from a prefix.
    
    Zip codes are 5-digit strings. The prefix is the first 3 digits.
    We preserve the leading zero by treating it as a string.
    """
    # Zip prefix is always 3 digits (e.g., "941", "200", "021")
    # Generate the last 2 digits
    suffix = random.randint(0, 99)
    return f"{zip_prefix}{suffix:02d}"


def jitter_coordinate(base: float, jitter_factor: float = 0.001) -> float:
    """
    Jitter a coordinate by a small random amount.
    
    Args:
        base: The base coordinate value.
        jitter_factor: Maximum deviation in degrees (default 0.001°).
    
    Returns:
        The jittered coordinate.
    """
    jitter = random.uniform(-jitter_factor, jitter_factor)
    return base + jitter


def generate_identity() -> Dict:
    """Generate a single synthetic identity record."""
    # --- Location module ---
    locations = load_locations(LOCATIONS_PATH)
    ref_location = weighted_choice(locations)
    
    # Extract reference location data
    city = ref_location["city"]
    state = ref_location["state"]
    zip_prefix = ref_location["zip_prefix"]
    area_code = ref_location["area_code"]
    
    # Jitter lat/lon
    base_lat = ref_location["latitude"]
    base_lon = ref_location["longitude"]
    lat = jitter_coordinate(base_lat)
    lon = jitter_coordinate(base_lon)
    
    # Generate zip code as string (preserves leading zeros)
    zip_code = generate_zip(zip_prefix)
    
    # --- Address generation (kept as before) ---
    address = generate_address()
    
    # --- Phone generation ---
    phone = generate_phone(area_code)
    
    # --- Identity ID ---
    identity_id = str(uuid.UUID(int=random.getrandbits(128), version=4))
    
    # --- Name generation ---
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    middle_name = random.choice(list(middle_names.keys()))
    middle_name_value = middle_names.get(middle_name, middle_name)
    
    return {
        "identity_id": identity_id,
        "first_name": first_name,
        "last_name": last_name,
        "middle_name": middle_name_value,
        "address": address,
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "phone": phone,
        "latitude": lat,
        "longitude": lon,
    }


def main(num_identities: int = 1000):
    """Generate `num_identities` synthetic records."""
    records = []
    for _ in range(num_identities):
        record = generate_identity()
        records.append(record)
    
    # Write to CSV
    output_path = Path(OUTPUT_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        "identity_id", "first_name", "last_name", "middle_name",
        "address", "city", "state", "zip_code", "phone",
        "latitude", "longitude"
    ]
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    print(f"Generated CSV file: {output_path}")
    print(f"Total rows: {len(records)}")
    print(f"Unique cities: {len(set(r['city'] for r in records))}")
    print(f"Unique states: {len(set(r['state'] for r in records))}")


if __name__ == "__main__":
    config = load_config(CONFIG_PATH)
    num_identities = config["num_identities"]
    random.seed(config["random_seed"])
    main(num_identities)