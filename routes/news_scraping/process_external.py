import os
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_external_datasets():
    """
    Download or generate external datasets for crime analysis.
    If datasets already exist, this function will validate them and only regenerate if necessary.
    """
    # Create directory for storing external data
    external_data_dir = os.path.join('static', 'data', 'external')
    if not os.path.exists(external_data_dir):
        os.makedirs(external_data_dir)
    
    # Path to the external crime data file
    external_data_path = os.path.join(external_data_dir, 'kurla_crime_data.csv')
    
    # Check if the file already exists
    if os.path.exists(external_data_path):
        try:
            # Validate existing data
            df = pd.read_csv(external_data_path)
            required_columns = ['date', 'location', 'crime_type', 'severity']
            
            if all(col in df.columns for col in required_columns) and len(df) >= 100:
                logger.info(f"External dataset already exists with {len(df)} records and valid columns")
                
                # Update the dataset status file
                update_dataset_status(df)
                return True
            else:
                logger.warning("Existing external dataset is missing required columns or has insufficient data")
        except Exception as e:
            logger.error(f"Error validating existing external dataset: {str(e)}")
    
    # If we get here, we need to generate a new dataset
    logger.info("Generating new external dataset...")
    
    try:
        # Define locations and crime types
        locations = [
            "Kurla West", "Kurla East", "Kurla Station Area", 
            "BKC", "Nehru Nagar", "Tilak Nagar"
        ]
        
        crime_types = [
            "Theft", "Robbery", "Assault", "Harassment", 
            "Vehicle Theft", "Pickpocketing", "Burglary"
        ]
        
        # Generate random data
        np.random.seed(42)  # For reproducibility
        
        num_records = 300
        data = {
            'date': [str(date) for date in pd.date_range(start='2023-01-01', periods=num_records)],
            'location': np.random.choice(locations, num_records),
            'crime_type': np.random.choice(crime_types, num_records),
            'severity': np.random.choice(['Low', 'Medium', 'High'], num_records)
        }
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Add more incidents to certain areas to create hotspots
        hotspot_locations = ["Kurla Station Area", "Nehru Nagar"]
        additional_records = 50
        
        for location in hotspot_locations:
            hotspot_data = {
                'date': [str(date) for date in pd.date_range(start='2023-06-01', periods=additional_records)],
                'location': [location] * additional_records,
                'crime_type': np.random.choice(crime_types, additional_records, 
                                              p=[0.3, 0.2, 0.2, 0.1, 0.1, 0.05, 0.05]),
                'severity': np.random.choice(['Medium', 'High'], additional_records, p=[0.3, 0.7])
            }
            hotspot_df = pd.DataFrame(hotspot_data)
            df = pd.concat([df, hotspot_df])
        
        # Save to CSV
        df.to_csv(external_data_path, index=False)
        logger.info(f"Generated and saved {len(df)} records to {external_data_path}")
        
        # Update the dataset status file
        update_dataset_status(df)
        
        return True
    
    except Exception as e:
        logger.error(f"Error generating external dataset: {str(e)}")
        return False

def update_dataset_status(df):
    """Update the dataset status JSON file with information about the external dataset"""
    try:
        status_file = os.path.join('static', 'data', 'dataset_status.json')
        
        # Create default status object if file doesn't exist
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status_data = json.load(f)
        else:
            status_data = {
                "datasets": {
                    "external_data": {},
                    "news_analysis": {}
                },
                "status": "ok"
            }
        
        # Update external data status
        status_data["datasets"]["external_data"] = {
            "columns": list(df.columns),
            "locations": len(df['location'].unique()),
            "rows": len(df),
            "sample": df.head(3).to_dict('records'),
            "status": "loaded",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Check if news analysis data exists
        news_analysis_file = os.path.join('static', 'data', 'news_analysis', 'crime_analysis.json')
        if os.path.exists(news_analysis_file):
            with open(news_analysis_file, 'r') as f:
                news_data = json.load(f)
                
            status_data["datasets"]["news_analysis"] = {
                "categories": len(news_data.get("crime_categories", {})),
                "incidents": len(news_data.get("recent_incidents", [])),
                "locations": len(news_data.get("crime_locations", {})),
                "status": "loaded",
                "last_updated": news_data.get("last_updated", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            }
        
        # Save updated status
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
            
        logger.info(f"Updated dataset status file: {status_file}")
        
    except Exception as e:
        logger.error(f"Error updating dataset status: {str(e)}")

if __name__ == "__main__":
    download_external_datasets()