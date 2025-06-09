import requests
import feedparser
from bs4 import BeautifulSoup
from typing import Dict, Any
import hashlib


def fetch_techcrunch_articles(url: str) -> Dict[str,Any]:

    """
    Fetch news articles from techcrunch AI section 
    
    return :
        Dict contain news information
    """

    feed  = feedparser.parse(url)
    result = []

    for entry in feed.entries:
        article = {
            'id': hashlib.md5(entry.id.encode()).hexdigest(),  # Unique ID based on the link
            'title': entry.title,
            'link': entry.link,
            'published': entry.published,
            'summary': entry.summary,
            'content': '',
            'author' : entry.author if 'author' in entry else 'Unknown',
            'source' : 'techcrunch',
        }

        # Fetch the full content of the article
        response = requests.get(entry.link)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for paragraph in soup.find('div',class_="article-body-commercial-selector article-body-viewer-selector dcr-11jq3zt").find_all('p'):
                article['content'] += paragraph.get_text() + '\n'

                

        result.append(article)
        
    return result



if __name__ == '__main__':
    res = fetch_techcrunch_articles("https://www.theguardian.com/uk/rss")
    print(res)