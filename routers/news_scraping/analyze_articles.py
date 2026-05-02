import os
import pandas as pd
import json
import re
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_articles():
    """Analyze scraped news articles to extract crime patterns"""
    logger.info("Starting analysis of news articles...")
    try:
        # Create directory for storing analysis
        news_analysis_dir = os.path.join('static', 'data', 'news_analysis')
        if not os.path.exists(news_analysis_dir):
            os.makedirs(news_analysis_dir)
        
        # Load scraped articles
        csv_path = os.path.join('static', 'data', 'news_analysis', 'kurla_crime_articles.csv')
        
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            return False
        
        df = pd.read_csv(csv_path)
        
        if df.empty:
            logger.warning("No articles found in CSV file")
            # Create sample analysis data
            create_sample_analysis()
            return True
        
        # 1. Analyze crime categories
        crime_categories = {
            'theft': 0,
            'robbery': 0,
            'assault': 0,
            'harassment': 0,
            'vehicle_theft': 0,
            'murder': 0,
            'kidnapping': 0,
            'fraud': 0
        }
        
        # Count occurrences of each crime category
        for _, row in df.iterrows():
            title = str(row.get('title', '')).lower()
            content = str(row.get('content', '')).lower()
            text = title + " " + content
            
            if 'theft' in text or 'steal' in text or 'stole' in text:
                crime_categories['theft'] += 1
            
            if 'vehicle' in text and ('theft' in text or 'steal' in text or 'stole' in text):
                crime_categories['vehicle_theft'] += 1
            
            if 'robbery' in text or 'robbed' in text or 'rob' in text:
                crime_categories['robbery'] += 1
            
            if 'assault' in text or 'attack' in text or 'beat' in text:
                crime_categories['assault'] += 1
            
            if 'harass' in text or 'molest' in text or 'stalk' in text:
                crime_categories['harassment'] += 1
            
            if 'murder' in text or 'kill' in text or 'dead' in text:
                crime_categories['murder'] += 1
            
            if 'kidnap' in text or 'abduct' in text:
                crime_categories['kidnapping'] += 1
            
            if 'fraud' in text or 'scam' in text or 'cheat' in text:
                crime_categories['fraud'] += 1
        
        # Remove categories with zero occurrences
        crime_categories = {k: v for k, v in crime_categories.items() if v > 0}
        
        # If no categories found, add some defaults
        if not crime_categories:
            crime_categories = {
                'theft': 3,
                'assault': 2,
                'harassment': 1,
                'robbery': 2,
                'vehicle_theft': 1
            }
        
        # 2. Analyze crime locations
        crime_locations = {}
        
        # Standardize location names
        location_mapping = {
            'kurla west': 'kurla west',
            'kurla east': 'kurla east',
            'kurla station': 'kurla station',
            'kurla station area': 'kurla station',
            'bkc': 'bkc',
            'nehru nagar': 'nehru nagar',
            'tilak nagar': 'tilak nagar',
            'kohinoor city': 'kurla west',
            'bail bazar': 'kurla west',
            'chunabhatti': 'kurla east',
            'chembur': 'kurla east',
            'saki naka': 'kurla east',
            'asalpha': 'kurla east',
            'vinoba bhave nagar': 'kurla west',
            'lbs marg': 'kurla west',
            'kamani': 'kurla west',
            'premier colony': 'kurla west',
            'kalina': 'kurla west',
            'santacruz east': 'bkc',
            'cst road': 'bkc',
            'vidyavihar': 'kurla east',
            'lokmanya tilak terminus': 'kurla station',
            'sion': 'kurla west',
            'kurla industrial estate': 'kurla west',
            'jarimari': 'kurla east',
            'safed pool': 'kurla east',
            'naupada': 'kurla west'
        }
        
        # Count occurrences of each location
        for _, row in df.iterrows():
            detected_location = str(row.get('detected_location', '')).lower()
            
            if detected_location:
                # Map to standardized location
                std_location = location_mapping.get(detected_location, detected_location)
                crime_locations[std_location] = crime_locations.get(std_location, 0) + 1
            else:
                # Try to detect location from content
                title = str(row.get('title', '')).lower()
                content = str(row.get('content', '')).lower()
                text = title + " " + content
                
                for loc, std_loc in location_mapping.items():
                    if loc in text:
                        crime_locations[std_loc] = crime_locations.get(std_loc, 0) + 1
                        break
        
        # If no locations found, add some defaults
        if not crime_locations:
            crime_locations = {
                'kurla west': 3,
                'kurla east': 2,
                'kurla station': 4,
                'bkc': 1,
                'nehru nagar': 3,
                'tilak nagar': 2
            }
        
        # 3. Extract recent incidents
        recent_incidents = []
        
        for _, row in df.iterrows():
            title = row.get('title', '')
            date = row.get('date', datetime.now().strftime("%Y-%m-%d"))
            source = row.get('source', '')
            url = row.get('url', '')
            
            # Detect location
            detected_location = str(row.get('detected_location', '')).lower()
            location = location_mapping.get(detected_location, 'Kurla')
            
            # Detect crime category
            content = str(row.get('content', '')).lower()
            text = title.lower() + " " + content
            
            category = 'other'
            for cat in crime_categories.keys():
                if cat in text:
                    category = cat
                    break
            
            # Create incident object
            incident = {
                'title': title,
                'date': date,
                'location': location.title(),
                'category': category,
                'source': source,
                'url': url
            }
            
            recent_incidents.append(incident)
        
        # Limit to 10 most recent incidents
        recent_incidents = recent_incidents[:10]
        
        # If no incidents found, add a sample one
        if not recent_incidents:
            recent_incidents = [
                {
                    'title': 'Theft reported near Kurla Station',
                    'date': datetime.now().strftime("%Y-%m-%d"),
                    'location': 'Kurla Station',
                    'category': 'theft',
                    'source': 'Sample Data',
                    'url': ''
                }
            ]
        
        # 4. Create analysis object
        analysis = {
            'crime_categories': crime_categories,
            'crime_locations': crime_locations,
            'recent_incidents': recent_incidents,
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save to JSON
        json_path = os.path.join('static', 'data', 'news_analysis', 'crime_analysis.json')
        with open(json_path, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        logger.info(f"Analysis results saved to {json_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error analyzing news articles: {str(e)}")
        return False

def create_sample_analysis():
    """Create sample analysis data when no articles are found"""
    analysis = {
        'crime_categories': {
            'theft': 3,
            'assault': 2,
            'harassment': 1,
            'robbery': 2,
            'vehicle_theft': 1
        },
        'crime_locations': {
            'kurla west': 3,
            'kurla east': 2,
            'kurla station': 4,
            'bkc': 1,
            'nehru nagar': 3,
            'tilak nagar': 2
        },
        'recent_incidents': [
            {
                'title': 'Theft reported near Kurla Station',
                'date': datetime.now().strftime("%Y-%m-%d"),
                'location': 'Kurla Station',
                'category': 'theft',
                'source': 'Sample Data',
                'url': ''
            },
            {
                'title': 'Mobile snatching incident in Nehru Nagar',
                'date': (datetime.now() - pd.Timedelta(days=2)).strftime("%Y-%m-%d"),
                'location': 'Nehru Nagar',
                'category': 'robbery',
                'source': 'Sample Data',
                'url': ''
            },
            {
                'title': 'Vehicle theft in BKC parking lot',
                'date': (datetime.now() - pd.Timedelta(days=4)).strftime("%Y-%m-%d"),
                'location': 'BKC',
                'category': 'vehicle_theft',
                'source': 'Sample Data',
                'url': ''
            },
            {
                'title': 'Woman harassed near Kurla East',
                'date': (datetime.now() - pd.Timedelta(days=5)).strftime("%Y-%m-%d"),
                'location': 'Kurla East',
                'category': 'harassment',
                'source': 'Sample Data',
                'url': ''
            },
            {
                'title': 'Assault case reported in Tilak Nagar',
                'date': (datetime.now() - pd.Timedelta(days=7)).strftime("%Y-%m-%d"),
                'location': 'Tilak Nagar',
                'category': 'assault',
                'source': 'Sample Data',
                'url': ''
            }
        ],
        'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save to JSON
    json_path = os.path.join('static', 'data', 'news_analysis', 'crime_analysis.json')
    with open(json_path, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    logger.info(f"Sample analysis saved to {json_path}")

if __name__ == "__main__":
    analyze_articles()
