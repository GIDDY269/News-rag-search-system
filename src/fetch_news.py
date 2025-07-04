import datetime
import os
import functools
from typing import Callable, List, Any


from pydantic import ValidationError
from config.setting import Settings
from utils.logger import setup_logger
from config.pydantic_models import *
from scraper.techcrunch import fetch_techcrunch_articles
from scraper.theverge import fetch_theverge_articles
from scraper.channelstv import fetch_channel_articles
from scraper.arise import fetch_arise_articles
from scraper.arts_tech import fetch_art_tech_articles
from scraper.cbssport import fetch_cbs_articles

from dotenv import load_dotenv
load_dotenv()

settings = Settings()

logger = setup_logger()


def handle_article_fetcing(func: Callable) -> Callable:
    """Decorator to handle article fetching and 
    logging errors from the articles fetching process."""


    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> List[Any]:
        try:
            articles = func(*args, **kwargs)
            if not articles:
                logger.warning("No articles fetched.")
            return articles
        
        except ValidationError as e:
            logger.error(f'Validation error while processing articles: {e}')
        except Exception as e:
            logger.error(f"Error fetching articles: {e}")
            logger.exception(e,"Exception occurred", exc_info=True)
        return []
    
    return wrapper

def time_window(hours: int) -> str:

    '''generate the datetime pairs for the specificied time window'''

    now = datetime.datetime.now()
    end_datetime = now + datetime.timedelta(hours=hours)

    return now.datetime.strfttime("%Y-%m-%dT%H:%M:%S"), end_datetime.strftime("%Y-%m-%dT%H:%M:%S")


class NewsFetcher:

    '''
    A class to fetch news articles from different sources'''

    def __init__(self):
       pass

    @handle_article_fetcing
    def fetch_from_techcrunch(self) -> List[Dict]:
        '''fetch news from techcrunch'''
        return [TechCrunchModel(**article).to_base()
                for article in fetch_techcrunch_articles(settings.TECHCRUNCH_URL)]
    
    @handle_article_fetcing
    def fetch_from_theverge(self) -> List[Dict]:
        '''fetch news from theverge'''
        return [TheVergeModel(**article).to_base()
                for article in fetch_theverge_articles(settings.THEVERGE_URL)]
    
    @handle_article_fetcing
    def fetch_from_channelstv(self) -> List[Dict]:
        '''fetch news from channelstv'''
        return [ChannelstvModel(**article).to_base()
                for article in fetch_channel_articles(settings.CHANNELSTV_URL)]
    
    @handle_article_fetcing
    def fetch_from_arise(self) -> List[Dict]:
        '''fetch news from arise'''
        return [AriseModel(**article).to_base()
                for article in fetch_arise_articles(settings.ARISE_URL)]
    

    @handle_article_fetcing
    def fetch_from_art(self) -> List[Dict]:
        '''fetch news from arise'''
        return [ArtsModel(**article).to_base()
                for article in fetch_art_tech_articles(settings.ARTS_URL)]
    
    @handle_article_fetcing
    def fetch_from_cbs(self) -> List[Dict]:
        '''fetch news from arise'''
        return [CbsModel(**article).to_base()
                for article in fetch_cbs_articles(settings.CBS_URL)]
    
    @property
    def sources(self) -> List[callable] :
        '''List of news fetching functions'''
        return [
                self.fetch_from_techcrunch,self.fetch_from_theverge,
                self.fetch_from_channelstv,self.fetch_from_arise,
                self.fetch_from_art,self.fetch_from_cbs]

