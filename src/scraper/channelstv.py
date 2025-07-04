import feedparser
from typing import Dict, Any
from bs4 import BeautifulSoup
import hashlib
from utils.data_clean import clean_full

def extract_image_url(content):
    html = content[0]['value']  # get the HTML string
    soup = BeautifulSoup(html, 'html.parser')
    img_tag = soup.find('img')  # find the first <img> tag
    if img_tag and img_tag.get('src'):
        return img_tag['src']
    return None

def fetch_channel_articles(url: str) -> Dict[str,Any]:

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
            'image_url': extract_image_url(entry.content),
            'published': entry.published,
            'summary': entry.summary,
            'content': entry.content[0].value,
            'author' : entry.author if 'author' in entry else 'Unknown',
            'source' : 'channelstv',
        }

        result.append(article)
    
    return result

        

#if __name__ == '__main__':
 #   result = fetch_channel_articles("https://www.channelstv.com/feed/")
  #  print(f'content with cleaning : {result}')
