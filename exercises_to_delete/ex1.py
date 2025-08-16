# Exercise 1

# Define all property listings
listing1 = {'property_id': 1,
			 'location': "Paris",
			  'type': "Condo",
              'price_per_night': 300,
              'features': ["Kitchen", "TV", "Toiletries", "Wifi"],
              'tags': ["Group trip", "Weekend trip", "Last minute trip", "Urban"]}

listing2 = {'property_id': 2,
			 'location': "London",
			  'type': "Condo",
              'price_per_night': 200,
              'features': ["Kitchen", "Clothing iron", "Wifi"],
              'tags': ["Family trip", "Weekend trip", "Urban"]}

listing3 = {'property_id': 3,
			 'location': "New York",
			  'type': "Condo",
              'price_per_night': 500,
              'features': ["Kitchen", "Clothing iron", "Wifi"],
              'tags': ["Weekend trip", "Nightlife", "Urban"]}

listing4 = {'property_id': 4,
			 'location': "Detroit",
			  'type': "House",
              'price_per_night': 400,
              'features': ["Kitchen", "TV", "Toiletries", "Wifi", "Garden"],
              'tags': ["Group trip", "Luxury", "Pets"]}

listing5 = {'property_id': 5,
			 'location': "Vancouver",
			  'type': "House",
              'price_per_night': 1000,
              'features': ["Kitchen", "Free parking", "Hot tub", "Wifi"],
              'tags': ["Long stay", "Family trip", "Beachfront"]}

property_listing = [listing1, listing2, listing3, listing4, listing5]

# Print all listings
# Citation: using the same formatting (code) as ex1 official course solution
for listing in property_listing:
    print("All property listings:")
    print(f"Property ID: {listing['property_id']}")
    print(f"Location: {listing['location']}")
    print(f"Type: {listing['type']}")
    print(f"Price per night: ${listing['price_per_night']}")
    print(f"Features: {', '.join(listing['features'])}")
    print(f"Tags: {', '.join(listing['tags'])}")
    print("-" * 40)

# Filters and prints properties under the budget
budget = 500
print(f"Properties under ${budget} per night:")
for listing in property_listing:
    if listing['price_per_night'] < budget:
        print(f"{listing['location']} - ${listing['price_per_night']}")

# Display input prompt to allow user to search listings by tag
user_search_tag = input("Enter a tag to search by: ").strip().lower()
print(f"All properties with the tag '{user_search_tag}':")
for listing in property_listing:
    if user_search_tag in [tag.lower() for tag in listing['tags']]:
        print(f"{listing['location']} - ${listing['price_per_night']}")

