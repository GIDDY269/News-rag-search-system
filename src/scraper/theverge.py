import feedparser
from typing import Dict, Any
from bs4 import BeautifulSoup
import hashlib

def extract_image_url(content):
    html = content[0]['value']  # get the HTML string
    soup = BeautifulSoup(html, 'html.parser')
    img_tag = soup.find('img')  # find the first <img> tag
    if img_tag and img_tag.get('src'):
        return img_tag['src']
    return None

def fetch_theverge_articles(url: str) -> Dict[str,Any]:

    """
    Fetch news articles from techcrunch AI section 
    
    return :
        Dict contain news information
    """

    feed  = feedparser.parse(url)
    result = []

    for entry in feed.entries:

        
        article = {
            'id': hashlib.md5(entry.id.encode()).hexdigest(),
            'title': entry.title,
            'link': entry.link,
            'published': entry.published,
            'image_url': extract_image_url(entry.content) if 'content' in entry else None,
            'summary': entry.summary,
            'content': entry.content[0].value if 'content' in entry else '',
            'author' : entry.author if 'author' in entry else 'Unknown',
            'source' : 'Theverge',
        }

        result.append(article)

        return article



if __name__ == '__main__':
    fetch_theverge_articles("https://www.theverge.com/rss/index.xml")