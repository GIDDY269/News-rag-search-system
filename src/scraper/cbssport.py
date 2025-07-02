import requests
import feedparser
from bs4 import BeautifulSoup
from typing import Dict, Any
import hashlib




def fetch_cbs_articles(url: str) -> Dict[str,Any]:

    """
    Fetch news articles from cbs sports soccer section
    
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
            'source' : 'cbssports',
        }

        

        # Fetch the full content of the article
        response = requests.get(entry.link)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for paragraph in soup.find('div',class_='Article-bodyContent').find_all('p'):
                article['content'] += paragraph.get_text() + '\n'

            

                
        result.append(article)
        
    return result



#if __name__ == '__main__':
 #   fetch_cbs_articles("https://www.cbssports.com/rss/headlines/soccer/")