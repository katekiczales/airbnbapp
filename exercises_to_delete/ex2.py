import json
import sqlite3
# PART A

# Define the property class
class Property:
    def __init__(self, property_id, location, type_, price_per_night, features, tags):
        self.property_id = property_id # number
        self.location = location # string
        self.type = type_ # string
        self.price_per_night = price_per_night # number
        self.features = features # list of string
        self.tags = tags # list of string

    def __repr__(self):
        return (f"Property({self.property_id}, {self.location}, {self.type}, "
                f"${self.price_per_night})")

    # Convert a Property object to a dictionary or JSON object
    def to_dict(self):
        return {
            "property_id": self.property_id,
            "location": self.location,
            "type": self.type,
            "price_per_night": self.price_per_night,
            "features": self.features,
            "tags": self.tags
        }

    # Convert a dictionary or JSON object to a Property object (creating the object)
    @classmethod
    def from_dict(cls, data):
        return cls(
            data["property_id"],
            data["location"],
            data["type"],
            data["price_per_night"],
            data["features"],
            data["tags"]
        )

# Define the User class
class User:
    def __init__(self, user_id, name, group_size, preferred_environment, budget):
        self.user_id = user_id # number
        self.name = name # string
        self.group_size = group_size # number
        self.preferred_environment = preferred_environment # string
        self.budget = budget # number

    # Returns true if the property is a good fit for the user
    # Currently, bases 'good fit' on budget and environment (location)
    def matches(self, property_obj):
        price = property_obj.price_per_night <= self.budget
        environment = self.preferred_environment == property_obj.location

        return price and environment

    def __repr__(self):
        return f"User({self.user_id}, {self.name}, ${self.budget})"

    # Convert a User object to a dictionary or JSON object
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "group_size": self.group_size,
            "preferred_environment": self.preferred_environment,
            "budget": self.budget
        }

    # Convert a dictionary or JSON object to a User object (creating the object)
    @classmethod
    def from_dict(cls, data):
        return cls(
            data["user_id"],
            data["name"],
            data["group_size"],
            data["preferred_environment"],
            data["budget"]
        )

# PART B
# Create Property objects
properties = [
    Property(1, "Vancouver", "Condo", 200, ["WiFi", "Kitchen"], ["city", "modern"]),
    Property(2, "Whistler", "Cabin", 350, ["Fireplace", "Hot Tub"], ["mountain", "ski"])
]

#Create User objects
users = [
    User(1, "Francis", 2, "Vancouver", 250),
    User(2, "Kate", 4, "Whistler", 400)
]

# Save the property and user objects to JSON but first converting them to dictionaries
with open("ex1properties.json", "w") as f:
    json.dump([p.to_dict() for p in properties], f, indent=4)

with open("ex1users.json", "w") as f:
    json.dump([u.to_dict() for u in users], f, indent=4)

print("Successfully saved all properties and users to JSON files.")

# Load the properties and users from JSON, converting them into their respective objects
with open("ex1properties.json", "r") as f:
    loaded_properties = [Property.from_dict(p) for p in json.load(f)]

with open("ex1users.json", "r") as f:
    loaded_users = [User.from_dict(u) for u in json.load(f)]

print("Loaded properties:", loaded_properties)
print("Loaded users:", loaded_users)

# Test the user match function works after reloading
print(loaded_users[0].matches(loaded_properties[0]))  # True

# PART C
def init_db(conn: sqlite3.Connection) -> None:
    # Create the users and properties tables in the DB
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            group_size INTEGER NOT NULL,
            preferred_environment TEXT NOT NULL,
            budget REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS properties (
            property_id INTEGER PRIMARY KEY,
            location TEXT NOT NULL,
            type TEXT NOT NULL,
            price_per_night REAL NOT NULL,
            features TEXT NOT NULL, -- JSON array stored as TEXT
            tags TEXT NOT NULL      -- JSON array stored as TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_properties_price
            ON properties(price_per_night);
    """)
    conn.commit()