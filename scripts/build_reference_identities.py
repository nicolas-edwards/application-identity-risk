import csv
import random
import uuid
import yaml

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

city_names = [
    "Springfield", "Shelbyville", "Fairview", "Oakwood", "Riverton",
    "Brookfield", "Hillside", "Maplewood", "Riverdale", "Willow Creek",
    "Pine Valley", "Lakeside", "Summit", "Greenfield", "Meadowbrook",
    "Hillcrest", "Oak Hill", "Fair Oaks", "Riverside", "Sunrise",
    "Downtown", "Westfield", "Northview", "Southport", "Eastwood",
    "Centerville", "Village", "Haven", "Harbor", "Bay",
    "Harbor", "Cove", "Glen", "Brook", "Falls",
    "Mills", "Vale", "Creek", "Springs", "Park",
    "Grove", "Cedar", "Elm", "Ash", "Willow",
    "Pine", "Birch", "Maple", "Cedar", "Oak"
]

state_names = ["CA", "TX", "FL", "NY", "IL", "PA", "OH", "GA", "NC", "MI",
    "NJ", "VA", "WA", "AZ", "MA", "TN", "IN", "MO", "MD", "WI",
    "CO", "MN", "OR", "SC", "AL", "LA", "KY", "OK", "CT",
    "UT", "IA", "NC", "MS", "AR", "WI", "NV", "NE", "ID", "NH",
    "Hawaii", "Hawai'i", "Maine", "Vermont", "New Hampshire",
    "Delaware", "Rhode Island", "Connecticut", "New Jersey", "Maryland"]

state_names = ["CA", "TX", "FL", "NY", "IL", "PA", "OH", "GA", "NC", "MI",
    "NJ", "VA", "WA", "AZ", "MA", "TN", "IN", "MO", "MD", "WI",
    "CO", "MN", "OR", "SC", "AL", "LA", "KY", "OK", "CT",
    "UT", "IA", "NC", "MS", "AR", "WI", "NV", "NE", "ID", "NH",
    "HI", "ME", "VT", "NH", "DE", "RI", "CT", "NJ", "MD"]

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

state_to_abbreviation = {
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


num_identites = 15000

random.seed(42)

# Open config file 
with open("config/reference_identities.yaml") as f:
    config = yaml.safe_load(f)
    random.seed(config["random_seed"])
    num_identities = config["num_identites"]
    


rows = []

for i in range(num_identities):
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    
    middle_name = random.choice(list(middle_names.keys()))
    middle_name_value = middle_names.get(middle_name, middle_name)
    
    street_type = random.choice(street_types)
    street_number = random.randint(100, 9999)
    street_address = f"{street_number} {street_type}"
    
    city = random.choice(city_names)
    state = random.choice(state_names)
    zip_code = f"{random.randint(10000, 99999)}-{random.randint(0, 999):04d}"
    
    area_code = random.choice([201, 212, 301, 303, 305, 307, 309, 310, 312, 313,
                               404, 408, 410, 503, 505, 512, 602, 605, 615, 702,
                               703, 704, 707, 708, 801, 804, 813, 901, 907, 915,
                               916, 919, 972, 980, 985, 986])
    exchange = random.randint(100, 999)
    line_number = random.randint(1000, 9999)
    phone = f"({area_code}) {exchange}-{line_number}"
    identity_id = str(uuid.UUID(int=random.getrandbits(128), version=4)) 
    
    row = [identity_id, first_name, last_name, middle_name_value, street_address, city, state, zip_code, phone]
    rows.append(row)

# Write to CSV
with open("data/reference/reference_identities.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["identity_id", "first_name", "last_name", "middle_name", "address", "city", "state", "zip_code", "phone"])
    writer.writerows(rows)

print("Generated CSV file: reference_identities.csv")
print(f"Total rows: {len(rows)}")