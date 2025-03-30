import os
import json
import random

# Make sure the directory exists
os.makedirs(os.path.join('static', 'data', 'news_analysis'), exist_ok=True)

# Path to the crime analysis JSON file
json_path = os.path.join('static', 'data', 'news_analysis', 'crime_analysis.json')

# Check if the file exists
if os.path.exists(json_path):
    # Load existing data
    with open(json_path, 'r') as f:
        data = json.load(f)
else:
    # Create new data structure if file doesn't exist
    data = {
        "crime_categories": {
            "theft": 3,
            "assault": 2,
            "harassment": 1,
            "robbery": 2,
            "vehicle_theft": 1
        },
        "recent_incidents": [
            {
                "title": "Theft reported near Kurla Station",
                "date": "2023-07-15",
                "location": "Kurla Station",
                "category": "theft",
                "description": "A wallet was stolen from a commuter at Kurla Station."
            }
        ],
        "crime_locations": {}  # This is empty and we'll fill it
    }

# Add location data if it's empty
if not data.get("crime_locations"):
    # Add some sample locations with crime counts
    locations = {
        "kurla west": random.randint(1, 3),
        "kurla east": random.randint(1, 3),
        "kurla station": random.randint(2, 5),
        "bkc": random.randint(0, 2),
        "nehru nagar": random.randint(2, 4),
        "tilak nagar": random.randint(1, 3)
    }
    
    data["crime_locations"] = locations

# Save the updated data
with open(json_path, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Updated crime_analysis.json with location data")
print(f"Added crime counts for {len(data['crime_locations'])} locations")