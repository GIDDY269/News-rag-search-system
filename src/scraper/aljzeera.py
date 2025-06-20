import requests
import feedparser
from bs4 import BeautifulSoup
from typing import Dict, Any
import hashlib


def fetch_bbcsport_articles(url: str) -> Dict[str,Any]:

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
            'source' : 'bbcsport',
        }

        # Fetch the full content of the article
        try:
            response = requests.get(entry.link)
            if response.status_code == 200:
        
                soup = BeautifulSoup(response.content, 'html.parser')
                rs = soup.find('div',class_="ssrcss-1o5p6v2-RichTextContainer e5tfeyi1").find_all('p')
                for paragraph in rs:
                    if paragraph:
                        article['content'] += paragraph.get_text() + '\n'
                    else:
                        article['content']  = ''  

                    

            result.append(article)
        except Exception as e:
            print(f"Parsing error for {entry.link}: {e}")
      
        
    return result



if __name__ == '__main__':
    res = fetch_bbcsport_articles("https://feeds.bbci.co.uk/sport/football/rss.xml")
    print(res)