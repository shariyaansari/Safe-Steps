import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
from datetime import datetime
import logging
import random
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define Kurla sub-areas for better location detection
KURLA_AREAS = [
    "kurla", "kurla west", "kurla east", "kurla station", "bkc", "nehru nagar", "tilak nagar",
    "kohinoor", "bail bazar", "chunabhatti", "chembur", "saki naka", "asalpha",
    "vinoba bhave nagar", "lbs marg", "kamani", "premier colony",
    "kalina", "santacruz east", "cst road", "vidyavihar", "lokmanya tilak terminus",
    "sion", "industrial estate", "jarimari", "safed pool", "naupada"
]

def scrape_all_sources():
    """Scrape news from all defined sources"""
    # Create directory for storing data
    news_analysis_dir = os.path.join('static', 'data', 'news_analysis')
    if not os.path.exists(news_analysis_dir):
        os.makedirs(news_analysis_dir)
    
    # List to store all articles
    all_articles = []
    
    # Scrape Hindustan Times
    try:
        ht_articles = scrape_hindustan_times()
        all_articles.extend(ht_articles)
        logger.info(f"Retrieved {len(ht_articles)} articles from Hindustan Times")
    except Exception as e:
        logger.error(f"Failed to retrieve data from Hindustan Times: {str(e)}")
    
    # Scrape Mumbai Mirror
    try:
        mm_articles = scrape_mumbai_mirror()
        all_articles.extend(mm_articles)
        logger.info(f"Retrieved {len(mm_articles)} articles from Mumbai Mirror")
    except Exception as e:
        logger.error(f"Failed to retrieve data from Mumbai Mirror: {str(e)}")
    
    # Scrape Mid-Day
    try:
        midday_articles = scrape_midday()
        all_articles.extend(midday_articles)
        logger.info(f"Retrieved {len(midday_articles)} articles from Mid-Day")
    except Exception as e:
        logger.error(f"Failed to retrieve data from Mid-Day: {str(e)}")
    
    # Scrape Times of India
    try:
        toi_articles = scrape_times_of_india()
        all_articles.extend(toi_articles)
        logger.info(f"Retrieved {len(toi_articles)} articles from Times of India")
    except Exception as e:
        logger.error(f"Failed to retrieve data from Times of India: {str(e)}")
    
    # Scrape Google News
    try:
        google_articles = scrape_google_news()
        all_articles.extend(google_articles)
        logger.info(f"Retrieved {len(google_articles)} articles from Google News")
    except Exception as e:
        logger.error(f"Failed to retrieve data from Google News: {str(e)}")
    
    # Filter articles related to Kurla and crime
    kurla_crime_articles = []
    
    # Crime keywords - expanded list
    crime_keywords = [
        'crime', 'theft', 'robbery', 'murder', 'assault', 'attack', 
        'kidnap', 'rape', 'molest', 'harass', 'arrest', 'police', 
        'criminal', 'victim', 'gang', 'knife', 'gun', 'weapon', 
        'stolen', 'burglary', 'fraud', 'scam', 'extortion', 'violence',
        'accident', 'danger', 'unsafe', 'threat', 'security', 'incident',
        'investigation', 'suspect', 'accused', 'court', 'jail', 'prison'
    ]
    
    for article in all_articles:
        title_lower = article.get('title', '').lower()
        content_lower = article.get('content', '').lower()
        
        # Check if article mentions Kurla or any of its sub-areas
        is_kurla_related = False
        for area in KURLA_AREAS:
            if area in title_lower or area in content_lower:
                is_kurla_related = True
                # Add the detected location to the article
                article['detected_location'] = area
                break
        
        # Check if article is crime-related (more lenient now)
        is_crime_related = any(keyword in title_lower or keyword in content_lower for keyword in crime_keywords)
        
        # More lenient filtering - include if it's about Kurla, even if crime isn't explicitly mentioned
        if is_kurla_related:
            kurla_crime_articles.append(article)
    
    logger.info(f"Found {len(kurla_crime_articles)} articles mentioning Kurla")
    
    # Save to CSV
    if kurla_crime_articles:
        df = pd.DataFrame(kurla_crime_articles)
        csv_path = os.path.join('static', 'data', 'news_analysis', 'kurla_crime_articles.csv')
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved {len(kurla_crime_articles)} articles to kurla_crime_articles.csv")
    else:
        # Create an empty DataFrame with columns to prevent the "No columns to parse" error
        df = pd.DataFrame(columns=['title', 'content', 'date', 'url', 'source', 'detected_location'])
        csv_path = os.path.join('static', 'data', 'news_analysis', 'kurla_crime_articles.csv')
        df.to_csv(csv_path, index=False)
        logger.info("No articles found. Created empty CSV file with headers.")
        
        # For testing purposes, create some sample data if no articles found
        create_sample_articles()

def create_sample_articles():
    """Create sample articles for testing when no real articles are found"""
    logger.info("Creating sample articles for testing")
    
    sample_articles = []
    crime_types = ['theft', 'robbery', 'assault', 'harassment', 'vehicle theft']
    
    # Create more realistic sample data
    incidents = [
        {
            'title': "Theft reported near Kurla Station",
            'content': "A wallet was stolen from a commuter at Kurla Station during rush hour. Police have registered a case and are reviewing CCTV footage.",
            'location': "kurla station",
            'crime': "theft"
        },
        {
            'title': "Mobile snatching incident in Nehru Nagar",
            'content': "Two individuals on a motorcycle snatched a mobile phone from a pedestrian in Nehru Nagar area. Local police have increased patrolling.",
            'location': "nehru nagar",
            'crime': "robbery"
        },
        {
            'title': "Vehicle theft in BKC parking lot",
            'content': "A car was reported stolen from the parking lot of a commercial complex in BKC. Police are investigating the incident.",
            'location': "bkc",
            'crime': "vehicle theft"
        },
        {
            'title': "Woman harassed near Kurla East",
            'content': "A woman reported being harassed by unknown individuals near Kurla East. Police have filed a complaint and are searching for suspects.",
            'location': "kurla east",
            'crime': "harassment"
        },
        {
            'title': "Assault case reported in Tilak Nagar",
            'content': "A man was assaulted by a group of individuals in Tilak Nagar following an argument. The victim has been hospitalized.",
            'location': "tilak nagar",
            'crime': "assault"
        },
        {
            'title': "Chain snatching incident in Kurla West",
            'content': "An elderly woman's gold chain was snatched by two individuals on a motorcycle in Kurla West. Police have registered a case.",
            'location': "kurla west",
            'crime': "robbery"
        },
        {
            'title': "Break-in at shop in Kurla Market",
            'content': "A shop in Kurla Market was broken into during the night. Cash and valuables worth approximately Rs. 50,000 were stolen.",
            'location': "kurla west",
            'crime': "burglary"
        },
        {
            'title': "Pickpocketing reported at Lokmanya Tilak Terminus",
            'content': "Several cases of pickpocketing have been reported at Lokmanya Tilak Terminus. Police have advised travelers to remain vigilant.",
            'location': "lokmanya tilak terminus",
            'crime': "theft"
        },
        {
            'title': "Two arrested for mobile theft in Kurla",
            'content': "Police arrested two individuals involved in a series of mobile phone thefts in the Kurla area. Several stolen phones were recovered.",
            'location': "kurla",
            'crime': "theft"
        },
        {
            'title': "Woman's purse snatched in Chunabhatti",
            'content': "A woman's purse was snatched by an individual on a bicycle in Chunabhatti. Police are searching for the suspect.",
            'location': "chunabhatti",
            'crime': "theft"
        },
        {
            'title': "Robbery at jewelry store in Kurla",
            'content': "A jewelry store in Kurla was robbed by armed individuals. Police have formed special teams to track down the suspects.",
            'location': "kurla",
            'crime': "robbery"
        },
        {
            'title': "Vehicle vandalism reported in Nehru Nagar",
            'content': "Several vehicles parked in Nehru Nagar were vandalized during the night. Police are investigating the incident.",
            'location': "nehru nagar",
            'crime': "vandalism"
        },
        {
            'title': "Scuffle breaks out at Kurla Station",
            'content': "A scuffle broke out between two groups at Kurla Station. Police intervened to control the situation.",
            'location': "kurla station",
            'crime': "assault"
        },
        {
            'title': "Elderly man robbed in Kurla East",
            'content': "An elderly man was robbed of his pension money in Kurla East. Police have registered a case and are searching for the suspects.",
            'location': "kurla east",
            'crime': "robbery"
        },
        {
            'title': "Two-wheeler theft in BKC",
            'content': "A two-wheeler was reported stolen from a parking area in BKC. Police are reviewing CCTV footage from the area.",
            'location': "bkc",
            'crime': "vehicle theft"
        }
    ]
    
    # Generate articles from incidents
    for i, incident in enumerate(incidents):
        # Create date range from past 30 days
        date = (datetime.now() - pd.Timedelta(days=i*2)).strftime("%Y-%m-%d")
        
        article = {
            'title': incident['title'],
            'content': incident['content'],
            'date': date,
            'url': "https://example.com/sample",
            'source': "Sample Data",
            'detected_location': incident['location']
        }
        
        sample_articles.append(article)
    
    df = pd.DataFrame(sample_articles)
    csv_path = os.path.join('static', 'data', 'news_analysis', 'kurla_crime_articles.csv')
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved {len(sample_articles)} sample articles to kurla_crime_articles.csv")

def get_headers():
    """Get random user agent headers to avoid blocking"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
    ]
    
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }

def scrape_hindustan_times():
    """Scrape news from Hindustan Times"""
    articles = []
    
    # Use search URL instead of topic page
    url = "https://www.hindustantimes.com/search?q=kurla%20crime"
    
    try:
        headers = get_headers()
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find article elements - updated selectors
        article_elements = soup.select('.searchList li') or soup.select('.listingPage li') or soup.select('.cartHolder')
        
        for article in article_elements:
            try:
                title_element = article.select_one('h3.hdg3') or article.select_one('h2.hdg3') or article.select_one('.media-heading')
                title = title_element.text.strip() if title_element else "No title"
                
                link_element = article.select_one('a')
                link = link_element['href'] if link_element and 'href' in link_element.attrs else ""
                if link and not link.startswith('http'):
                    link = f"https://www.hindustantimes.com{link}"
                
                # Get article content if available
                content = ""
                if link:
                    try:
                        article_response = requests.get(link, headers=get_headers(), timeout=10)
                        article_soup = BeautifulSoup(article_response.text, 'html.parser')
                        content_elements = article_soup.select('div.storyDetail p') or article_soup.select('div.article-body p')
                        content = ' '.join([p.text.strip() for p in content_elements])
                    except Exception as e:
                        logger.warning(f"Could not fetch content for {link}: {str(e)}")
                
                # Try to extract date
                date_element = article.select_one('span.dateTime') or article.select_one('.time-dt')
                date_str = date_element.text.strip() if date_element else ""
                date = datetime.now().strftime("%Y-%m-%d")  # Default to today if no date found
                
                articles.append({
                    'title': title,
                    'content': content,
                    'date': date,
                    'url': link,
                    'source': 'Hindustan Times'
                })
                
                # Be nice to the server
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error parsing article: {str(e)}")
                continue
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Hindustan Times: {str(e)}")
        raise
        
    return articles

def scrape_mumbai_mirror():
    """Scrape news from Mumbai Mirror"""
    articles = []
    
    # Mumbai Mirror has been discontinued, but we'll use Times of India's Mumbai section as a replacement
    url = "https://timesofindia.indiatimes.com/city/mumbai"
    
    try:
        headers = get_headers()
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find article elements
        article_elements = soup.select('.main-content .article') or soup.select('.card-container')
        
        for article in article_elements:
            try:
                title_element = article.select_one('h3') or article.select_one('figcaption')
                title = title_element.text.strip() if title_element else "No title"
                
                # Only process if it might be related to Kurla
                if not any(area in title.lower() for area in KURLA_AREAS):
                    continue
                
                link_element = article.select_one('a')
                link = link_element['href'] if link_element and 'href' in link_element.attrs else ""
                if link and not link.startswith('http'):
                    link = f"https://timesofindia.indiatimes.com{link}"
                
                # Get article content if available
                content = ""
                if link:
                    try:
                        article_response = requests.get(link, headers=get_headers(), timeout=10)
                        article_soup = BeautifulSoup(article_response.text, 'html.parser')
                        content_elements = article_soup.select('.article-content p') or article_soup.select('._3WlLe p')
                        content = ' '.join([p.text.strip() for p in content_elements])
                    except Exception as e:
                        logger.warning(f"Could not fetch content for {link}: {str(e)}")
                
                # Try to extract date
                date_element = article.select_one('.date-time') or article.select_one('.publish-time')
                date_str = date_element.text.strip() if date_element else ""
                date = datetime.now().strftime("%Y-%m-%d")  # Default to today if no date found
                
                articles.append({
                    'title': title,
                    'content': content,
                    'date': date,
                    'url': link,
                    'source': 'Mumbai Mirror/TOI'
                })
                
                # Be nice to the server
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error parsing article: {str(e)}")
                continue
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Mumbai Mirror/TOI: {str(e)}")
        raise
        
    return articles

def scrape_midday():
    """Scrape news from Mid-Day"""
    articles = []
    
    # Use search URL instead of direct page
    url = "https://www.mid-day.com/search?q=kurla"
    
    try:
        headers = get_headers()
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find article elements - updated selectors
        article_elements = soup.select('.article-box') or soup.select('.listing-article') or soup.select('.searchlist-container .item')
        
        for article in article_elements:
            try:
                title_element = article.select_one('h2') or article.select_one('h3') or article.select_one('.headline')
                title = title_element.text.strip() if title_element else "No title"
                
                link_element = article.select_one('a')
                link = link_element['href'] if link_element and 'href' in link_element.attrs else ""
                if link and not link.startswith('http'):
                    link = f"https://www.mid-day.com{link}"
                
                # Get article content if available
                content = ""
                if link:
                    try:
                        article_response = requests.get(link, headers=get_headers(), timeout=10)
                        article_soup = BeautifulSoup(article_response.text, 'html.parser')
                        content_elements = article_soup.select('.article-content p') or article_soup.select('.article-body p')
                        content = ' '.join([p.text.strip() for p in content_elements])
                    except Exception as e:
                        logger.warning(f"Could not fetch content for {link}: {str(e)}")
                
                # Try to extract date
                date_element = article.select_one('.date') or article.select_one('.article-date')
                date_str = date_element.text.strip() if date_element else ""
                date = datetime.now().strftime("%Y-%m-%d")  # Default to today if no date found
                
                articles.append({
                    'title': title,
                    'content': content,
                    'date': date,
                    'url': link,
                    'source': 'Mid-Day'
                })
                
                # Be nice to the server
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error parsing article: {str(e)}")
                continue
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Mid-Day: {str(e)}")
        raise
        
    return articles

def scrape_times_of_india():
    """Scrape news from Times of India"""
    articles = []
    
    # Use search URL instead of direct page
    url = "https://timesofindia.indiatimes.com/topic/kurla"
    
    try:
        headers = get_headers()
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find article elements - updated selectors
        article_elements = soup.select('.article') or soup.select('.topic-card') or soup.select('.media')
        
        for article in article_elements:
            try:
                title_element = article.select_one('span.title') or article.select_one('h3') or article.select_one('figcaption')
                title = title_element.text.strip() if title_element else "No title"
                
                link_element = article.select_one('a')
                link = link_element['href'] if link_element and 'href' in link_element.attrs else ""
                if link and not link.startswith('http'):
                    link = f"https://timesofindia.indiatimes.com{link}"
                
                # Get article content if available
                content = ""
                if link:
                    try:
                        article_response = requests.get(link, headers=get_headers(), timeout=10)
                        article_soup = BeautifulSoup(article_response.text, 'html.parser')
                        content_elements = article_soup.select('div._3WlLe p') or article_soup.select('div.ga-headlines p')
                        content = ' '.join([p.text.strip() for p in content_elements])
                    except Exception as e:
                        logger.warning(f"Could not fetch content for {link}: {str(e)}")
                
                # Try to extract date
                date_element = article.select_one('span.date') or article.select_one('span.time')
                date_str = date_element.text.strip() if date_element else ""
                date = datetime.now().strftime("%Y-%m-%d")  # Default to today if no date found
                
                articles.append({
                    'title': title,
                    'content': content,
                    'date': date,
                    'url': link,
                    'source': 'Times of India'
                })
                
                # Be nice to the server
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error parsing article: {str(e)}")
                continue
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Times of India: {str(e)}")
        raise
        
    return articles

def scrape_google_news():
    """Scrape news from Google News"""
    articles = []
    
    # Use Google News search for Kurla crime
    url = "https://news.google.com/search?q=kurla%20crime%20mumbai&hl=en-IN&gl=IN&ceid=IN%3Aen"
    
    try:
        headers = get_headers()
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find article elements - Google News specific selectors
        article_elements = soup.select('article') or soup.select('.NiLAwe')
        
        for article in article_elements:
            try:
                title_element = article.select_one('h3') or article.select_one('h4')
                title = title_element.text.strip() if title_element else "No title"
                
                link_element = article.select_one('a')
                link = link_element['href'] if link_element and 'href' in link_element.attrs else ""
                if link and link.startswith('./articles/'):
                    link = f"https://news.google.com/{link[2:]}"
                
                # Get source and time
                source_element = article.select_one('.wEwyrc') or article.select_one('.SVJrMe')
                source = source_element.text.strip() if source_element else "Google News"
                
                time_element = article.select_one('time')
                date_str = time_element.text.strip() if time_element else ""
                date = datetime.now().strftime("%Y-%m-%d")  # Default to today if no date found
                
                # For Google News, we don't fetch content as it redirects to original sources
                content = f"Source: {source}. Date: {date_str}"
                
                articles.append({
                    'title': title,
                    'content': content,
                    'date': date,
                    'url': link,
                    'source': f"Google News - {source}"
                })
                
                # Limit to 10 articles from Google News
                if len(articles) >= 10:
                    break
                
                # Be nice to the server
                time.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Error parsing article: {str(e)}")
                continue
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Google News: {str(e)}")
        raise
        
    return articles

if __name__ == "__main__":
    scrape_all_sources()
