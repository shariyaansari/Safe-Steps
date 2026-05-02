import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define file paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_DATA_PATH = os.path.join(SCRIPT_DIR, '..', '..', 'static', 'map_data.geojson')

# Manual coordinates for locations that fail geocoding
MANUAL_COORDINATES = {
    "kurla": [72.8891, 19.0748],
    "kurla station": [72.8777, 19.0658],
    "kurla west": [72.8800, 19.0700],
    "kurla east": [72.8900, 19.0750],
    "bkc": [72.8680, 19.0630],
    "nehru nagar": [72.8720, 19.0550],
    "tilak nagar": [72.8850, 19.0580]
}

def fix_coordinates():
    """Add missing coordinates and fix any issues in the map data."""
    try:
        # Load existing map data
        with open(MAP_DATA_PATH, 'r') as f:
            map_data = json.load(f)
        
        features = map_data["features"]
        original_count = len(features)
        
        # Check for features with missing coordinates
        locations_with_coords = {feature["properties"]["name"].lower() for feature in features}
        
        # Add features for locations with manual coordinates that aren't already in the data
        for location_name, coords in MANUAL_COORDINATES.items():
            # Skip if this location is already in the data
            if any(feature["properties"]["name"].lower() == location_name for feature in features):
                continue
                
            # Create a new feature with default values
            new_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": coords
                },
                "properties": {
                    "name": location_name.title(),
                    "crime_count": 0,  # Default value, update if you have actual data
                    "safety_level": "green"  # Default value
                }
            }
            
            features.append(new_feature)
            logger.info(f"Added manual coordinates for {location_name}")
        
        # Save updated map data
        with open(MAP_DATA_PATH, 'w') as f:
            json.dump(map_data, f, indent=2)
        
        logger.info(f"Updated map data: {original_count} original features, {len(features)} after fixes")
        
    except FileNotFoundError:
        logger.error(f"Map data file not found: {MAP_DATA_PATH}")
    except json.JSONDecodeError:
        logger.error(f"Error parsing map data file: {MAP_DATA_PATH}")
    except Exception as e:
        logger.error(f"Error fixing coordinates: {str(e)}")

if __name__ == "__main__":
    fix_coordinates()