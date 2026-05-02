import json
import logging
import os
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
from datetime import datetime, timedelta
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define file paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NEWS_DATA_PATH = os.path.join(SCRIPT_DIR, 'news_analysis_results.json')
EXTERNAL_DATA_PATH = os.path.join(SCRIPT_DIR, 'external_crime_data.csv')  # Adjust if your external data is in a different format
OUTPUT_PATH = os.path.join(SCRIPT_DIR, '..', '..', 'static', 'map_data.geojson')

def geocode_location(location_name, city="Mumbai, India"):
    """Geocode a location name to get coordinates."""
    geolocator = Nominatim(user_agent="safesteps-app")
    
    # Add city name to make geocoding more accurate
    search_query = f"{location_name}, {city}"
    
    try:
        # Try to geocode with the full query
        location = geolocator.geocode(search_query, timeout=10)
        
        if location is None:
            # If that fails, try just the location name
            location = geolocator.geocode(location_name, timeout=10)
            
        if location is None:
            # If still no results, try with just Mumbai
            location = geolocator.geocode(f"{location_name}, Mumbai", timeout=10)
            
        # Wait to avoid hitting rate limits
        time.sleep(1)
        
        if location:
            return [location.longitude, location.latitude]
        else:
            logger.warning(f"No coordinates found for location: {location_name}")
            return None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        logger.error(f"Geocoding error for {location_name}: {str(e)}")
        return None

def determine_safety_level(crime_count):
    """Determine safety level based on crime count."""
    if crime_count < 20:
        return "green"
    elif crime_count < 50:
        return "yellow"
    else:
        return "red"

def load_news_data():
    """Load location data from news analysis."""
    try:
        with open(NEWS_DATA_PATH, 'r') as f:
            news_data = json.load(f)
        
        locations = []
        for location, count in news_data.items():
            locations.append({
                "name": location.strip().title(),
                "crime_count": count,
                "safety_level": determine_safety_level(count)
            })
        
        logger.info(f"Loaded {len(locations)} locations from news analysis")
        return locations
    except FileNotFoundError:
        logger.warning(f"News data file not found: {NEWS_DATA_PATH}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Error parsing news data file: {NEWS_DATA_PATH}")
        return []

def load_external_data():
    """Load location data from external dataset."""
    try:
        # Adjust this based on your external data format
        df = pd.read_csv(EXTERNAL_DATA_PATH)
        
        locations = []
        for _, row in df.iterrows():
            # Adjust column names based on your CSV structure
            locations.append({
                "name": row['location'].strip().title(),
                "crime_count": int(row['crime_count']),
                "safety_level": row.get('safety_level', determine_safety_level(int(row['crime_count'])))
            })
        
        logger.info(f"Loaded {len(locations)} locations from external dataset")
        return locations
    except FileNotFoundError:
        logger.warning(f"External data file not found: {EXTERNAL_DATA_PATH}")
        return []
    except Exception as e:
        logger.error(f"Error loading external data: {str(e)}")
        return []

def combine_data(news_locations, external_locations):
    """Combine and deduplicate location data."""
    # Create a dictionary to store combined data
    combined = {}
    
    # Process news locations
    for loc in news_locations:
        name = loc["name"].lower()
        combined[name] = loc
    
    # Process external locations, merging with existing if needed
    for loc in external_locations:
        name = loc["name"].lower()
        if name in combined:
            # If location exists, update crime count and recalculate safety level
            combined[name]["crime_count"] += loc["crime_count"]
            combined[name]["safety_level"] = determine_safety_level(combined[name]["crime_count"])
        else:
            combined[name] = loc
    
    # Convert back to list
    result = list(combined.values())
    logger.info(f"Combined {len(result)} unique locations")
    return result

# def generate_geojson(locations):
#     """Generate GeoJSON from location data."""
#     features = []
    
#     # Create a dictionary to track duplicate coordinates
#     coord_adjustment = {}
    
#     for loc in locations:
#         name = loc["name"]
#         coords = geocode_location(name)
        
#         if coords:
#             # Check if these coordinates already exist
#             coord_key = f"{coords[0]:.4f},{coords[1]:.4f}"
            
#             if coord_key in coord_adjustment:
#                 # Slightly adjust coordinates to avoid overlap
#                 coord_adjustment[coord_key] += 1
#                 offset = 0.0005 * coord_adjustment[coord_key]
#                 coords[0] += offset
#                 coords[1] += offset
#             else:
#                 coord_adjustment[coord_key] = 0
            
#             feature = {
#                 "type": "Feature",
#                 "geometry": {
#                     "type": "Point",
#                     "coordinates": coords
#                 },
#                 "properties": {
#                     "name": name,
#                     "crime_count": loc["crime_count"],
#                     "safety_level": loc["safety_level"]
#                 }
#             }
#             features.append(feature)
    
#     geojson = {
#         "type": "FeatureCollection",
#         "features": features
#     }
    
#     logger.info(f"Generated map data with {len(features)} markers")
#     return geojson


def generate_geojson(locations):
    """Generate GeoJSON from location data with timestamps."""
    features = []
    
    # Create a dictionary to track duplicate coordinates
    coord_adjustment = {}
    
    # Generate some random dates in the past 6 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 6 months ago
    
    for loc in locations:
        name = loc["name"]
        coords = geocode_location(name)
        
        if coords:
            # Check if these coordinates already exist
            coord_key = f"{coords[0]:.4f},{coords[1]:.4f}"
            
            if coord_key in coord_adjustment:
                # Slightly adjust coordinates to avoid overlap
                coord_adjustment[coord_key] += 1
                offset = 0.0005 * coord_adjustment[coord_key]
                coords[0] += offset
                coords[1] += offset
            else:
                coord_adjustment[coord_key] = 0
            
            # Generate crime incidents with timestamps
            incidents = []
            for _ in range(loc["crime_count"]):
                # Random date between start_date and end_date
                random_days = random.randint(0, (end_date - start_date).days)
                incident_date = start_date + timedelta(days=random_days)
                
                # Random crime type
                crime_types = ["Theft", "Assault", "Robbery", "Vandalism", "Other"]
                crime_type = random.choice(crime_types)
                
                incidents.append({
                    "date": incident_date.strftime("%Y-%m-%d"),
                    "type": crime_type
                })
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": coords
                },
                "properties": {
                    "name": name,
                    "crime_count": loc["crime_count"],
                    "safety_level": loc["safety_level"],
                    "incidents": incidents
                }
            }
            features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    logger.info(f"Generated map data with {len(features)} markers")
    return geojson

def save_geojson(geojson, output_path):
    """Save GeoJSON to file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    logger.info(f"Saved map data to {output_path}")

def main():
    # Load data from both sources
    news_locations = load_news_data()
    external_locations = load_external_data()
    
    # Combine data
    combined_locations = combine_data(news_locations, external_locations)
    
    # Generate GeoJSON
    geojson = generate_geojson(combined_locations)
    
    # Save GeoJSON
    save_geojson(geojson, OUTPUT_PATH)
    
    # Print summary for debugging
    print("\nLocation Summary:")
    for i, feature in enumerate(geojson["features"]):
        props = feature["properties"]
        coords = feature["geometry"]["coordinates"]
        print(f"{i+1}. {props['name']}: {props['crime_count']} crimes, Safety: {props['safety_level']}, Coords: {coords}")

if __name__ == "__main__":
    main()