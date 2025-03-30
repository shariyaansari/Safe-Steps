from news_scraper import scrape_all_sources
from analyze_articles import analyze_articles
from process_external import download_external_datasets
from generate_map_data import generate_map_data
import logging
import os
import json
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to console
    ]
)
logger = logging.getLogger(__name__)

def run_news_analysis():
    """
    Run the complete news analysis process:
    1. Scrape news articles from all sources
    2. Analyze the articles to extract crime information
    3. Validate or download external datasets
    4. Generate map data from all sources
    
    Returns:
        bool: True if the analysis was successful, False otherwise
    """
    start_time = datetime.now()
    logger.info(f"Starting news analysis pipeline at {start_time}")
    
    # Create necessary directories
    os.makedirs(os.path.join('static', 'data', 'news_analysis'), exist_ok=True)
    os.makedirs(os.path.join('static', 'data', 'external'), exist_ok=True)
    os.makedirs(os.path.join('static', 'data', 'map'), exist_ok=True)
    
    try:
        # Check if we already have data
        status_file = os.path.join('static', 'data', 'dataset_status.json')
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status_data = json.load(f)
                
            external_status = status_data.get("datasets", {}).get("external_data", {}).get("status")
            news_status = status_data.get("datasets", {}).get("news_analysis", {}).get("status")
            
            if external_status == "loaded" and news_status == "loaded":
                logger.info("Both datasets are already loaded. Checking if updates are needed...")
        
        logger.info("Step 1: Running news scraper...")
        scrape_all_sources()
        
        logger.info("Step 2: Analyzing news articles...")
        analyze_articles()
        
        logger.info("Step 3: Validating external datasets...")
        download_external_datasets()
        
        logger.info("Step 4: Generating map data...")
        generate_map_data()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"News and data analysis completed successfully in {duration:.2f} seconds")
        return True
    except Exception as e:
        logger.error(f"Error in news analysis: {str(e)}")
        return False

# This allows you to run the module directly
if __name__ == "__main__":
    run_news_analysis()