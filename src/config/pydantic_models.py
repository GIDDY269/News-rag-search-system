from pydantic import BaseModel, Field,field_validator
from typing import List, Optional, Dict, Union , Any
from uuid import uuid4
from datetime import datetime
import hashlib
import json


from dateutil import parser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from unstructured.staging.huggingface import chunk_by_attention_window


from utils.logger import setup_logger
from utils.data_clean import clean_full, remove_html_tags, normalize_whitespace
from embedding import TextEmbedder


logger = setup_logger()

class DocumentSource(BaseModel):
    id : Optional[str]
    name : str



class RefinedDocument(BaseModel):
    doc_id : str
    is_new : Optional[bool] = Field(default=None, description='Flag to indicate if the document is new or seen before')
    full_text : str = ''
    metadata : dict = {}
    
    @classmethod
    def from_base(cls, base: "BaseDocument") -> 'RefinedDocument':
        '''convert the BaseDocument to a RefinedDocument object'''

        refined = RefinedDocument(doc_id=str(base.article_id))
        refined.full_text = '.'.join([base.title, base.content])
        refined.metadata = {
            'title': base.title,
            'url': base.url,
            'content' : base.content,
            'published_at': base.published_at,
            'source_name': base.source_name,
            'image_url': base.image_url,
            'description': base.description,
            'author': base.author
        }

        \
        return refined

class ChuckedDocument(BaseModel):
    ''' convert the RefinedDocument to a ChuckedDocument object
    '''
    doc_id :str
    chunk_id : str
    full_raw_text : str
    text : str
    metadata : Dict[str, Union[str,Any]]


    @classmethod
    def from_refined(cls, refined_doc: RefinedDocument,embedding_model:TextEmbedder) -> list['ChuckedDocument']:

        chunks = ChuckedDocument.chunkenize(
            refined_doc.full_text, embedding_model
        )

        return [
            cls(
                doc_id = refined_doc.doc_id,
                chunk_id = hashlib.md5(chunk.encode()).hexdigest(),
                full_raw_text = refined_doc.full_text,
                text = chunk,
                metadata = refined_doc.metadata
            )

            for chunk in chunks
        ]
    
    @staticmethod
    def chunkenize(text: str, embedding_model:TextEmbedder) -> list[str]:

        splitter = RecursiveCharacterTextSplitter()
        text_sections = splitter.split_text(text=text)
        chucks = []
        for text_section in text_sections:
            chucks.extend(
                chunk_by_attention_window(text_section,embedding_model.tokenizer)
            )
            
        return chucks
    

class EmbedDocument(BaseModel):
    doc_id : str
    chunk_id : str
    full_raw_text : str
    text : str
    embedding : list[float]
    metadata : Dict[str, Union[str,Any]] = {}


    @classmethod
    def from_chunked(cls, chunked_doc: ChuckedDocument, 
                     embedding_model:TextEmbedder) -> 'EmbedDocument':
        
        return cls(
            doc_id = chunked_doc.doc_id,
            chunk_id = chunked_doc.chunk_id,
            full_raw_text = chunked_doc.full_raw_text,
            text = chunked_doc.text,
            embedding = embedding_model(chunked_doc.text,to_list=True),
            metadata = chunked_doc.metadata
        )
    
    def to_payload(self) -> tuple[str , List[float],dict]:
        '''Convert the EmbedDocument to a tuple of (doc_id, embedding, metadata)'''
        return (
            self.doc_id,
            self.embedding,
            self.metadata
        )
    
    def __repr__(self) -> str:
        return f"EmbeddedDocument(doc_id={self.doc_id}, chunk_id={self.chunk_id})"





class BaseDocument(BaseModel):

    '''pydantic model to validate data coming form the different API sources 
    and format them accordingly
    '''
    article_id : Optional[str] = Field(default_factory=lambda: str(uuid4()))
    title : str = Field(default_factory=lambda:'N/A')
    url : str = Field(default_factory=lambda:'N/A')
    published_at : str = Field(
        default_factory= datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    source_name : str = Field(default_factory=lambda : 'Unknown')
    image_url : Optional[str] = Field(default_factory= lambda:None)
    content : Optional[str] = Field(default_factory = lambda:None)
    description : Optional[str] = Field(default_factory=lambda:None)
    author : Optional[Union[str,List[str]]] = Field(default_factory=lambda :'Unknown')

    
    @field_validator('author')
    def clean_author(cls,v):
        '''Convert the author field to a string if it is a list'''
        if isinstance(v, list):
            return ', '.join(v)
        if v is None:
            return 'N/A'
        return v

    @field_validator('description','title','content')
    def clean_text_fields(cls,v):

        if v is None or v == '':
            return 'N/A'
        return clean_full(v)

    @field_validator('url','image_url')
    def clean_url_fields(cls,v):
        if v is None :
            return 'N/A'
        v = remove_html_tags(v)
        v = normalize_whitespace(v)
        return v
    
    @field_validator('published_at')
    def clean_Date_fields(cls,v):
        '''Parse the datetime string from the news apis to datetime objects
        
        Errors if default format is be used'''
        try: 
            parsed_date = parser.parse(v)
            return parsed_date.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError,TypeError) as e:
            logger.error(F'Error parsing date: {v} , Usinf the default[current] date instead ')

    
    @classmethod
    def from_json(cls,data:dict) -> 'BaseDocument':   
        '''
        Convert the json data from the API to a CommonDocument object
        '''
        return cls(**data) 
    
    def to_kafka_payload(self) -> dict:
        '''Prepare the common representation for Kafka payload'''

        return self.model_dump(exclude_none=False)





class NewsAPIModel(BaseModel):

    '''
    pydantic model for news api
    '''

    source :  DocumentSource
    author : Optional[str]
    title : str
    description : Optional[str]
    url : str
    urlToImage : Optional[str]
    publishedAt : str
    content : Optional[str]

    def to_base(self) -> BaseDocument:
        '''Convert the NewsAPIModel to a CommonDocument object'''
        return BaseDocument(
    
            title = self.title,
            url = self.url,
            published_at=self.publishedAt,
            image_url=self.urlToImage,
            source_name=self.source.name,
            article_id = str(uuid4()),
            content = self.content,
            description = self.description,
            author = self.author
            )
    

class NewDataioModel(BaseModel):
    ''''pydantic model for the news data api '''

    article_id : str
    title : str
    link : str
    description : Optional[str]
    pubDate : str
    source_id : Optional[str]
    source_url : Optional[str]
    source_icon : Optional[str]
    creator : Optional[list[str]]
    image_url : Optional[str]
    content :   Optional[str]

    def to_base(self) -> BaseDocument:
        '''Convert the NewDataioModel to a CommonDocument object'''
        return BaseDocument(
            article_id = self.article_id,
            title = self.title,
            url = self.link,
            published_at=self.pubDate,
            image_url=self.image_url,
            source_name = self.source_id or 'Unknown',
            content = self.content,
            description = self.description,
            author = self.creator#", ".join(self.creator) if self.creator else None
        )

class RealDataNewsModel(BaseModel):
    '''Pydantic model for the RealDataNews API'''

    article_id : str
    title : str
    photo_url : Optional[str]
    published_datetime : str
    source_name : str
    source_url : str
    author : list[str]
    snippet : Optional[str]

    def to_base(self) -> BaseDocument:
        '''Convert the RealDataNewsModel to a CommonDocument object'''
        return BaseDocument(
            article_id = str(uuid4()),
            title = self.title,
            url = self.source_url,
            published_at=self.published_datetime,
            image_url = self.photo_url,
            source_name = self.source_name,
            description = self.snippet,
            author = self.author
        )



class TechCrunchModel(BaseModel):
    ''''pydantic model for the news data api '''

    id : str
    title : str
    link : str
    summary : Optional[str]
    published : str
    source : Optional[str]
    author : Optional[Union[str,list[str]]]
    content :   Optional[str]

    def to_base(self) -> BaseDocument:
        '''Convert the techcrunchmodel to a CommonDocument object'''
        return BaseDocument(
            article_id = self.id,
            title = self.title,
            url = self.link,
            published_at=self.published,
            source_name = self.source or 'Unknown',
            content = self.content,
            description = self.summary,
            author = self.author#", ".join(self.creator) if self.creator else None
        )

class TheVergeModel(BaseModel):
    ''''pydantic model for the news data api '''

    id : str
    title : str
    link : str
    image_url : Optional[str]
    summary : Optional[str]
    published : str
    source : Optional[str]
    author : Optional[Union[str,list[str]]]
    content :   Optional[str]

    def to_base(self) -> BaseDocument:
        '''Convert the thevergemodel to a CommonDocument object'''
        return BaseDocument(
            article_id = self.id,
            title = self.title,
            url = self.link,
            image_url = self.image_url,
            published_at=self.published,
            source_name = self.source or 'Unknown',
            content = self.content,
            description = self.summary,
            author = self.author#", ".join(self.creator) if self.creator else None
        )
    

class ChannelstvModel(BaseModel):
    ''''pydantic model for the news data api '''

    id : str
    title : str
    link : str
    image_url : Optional[str]
    summary : Optional[str]
    published : str
    source : Optional[str]
    author : Optional[Union[str,list[str]]]
    content :   Optional[str]

    def to_base(self) -> BaseDocument:
        '''Convert the thevergemodel to a CommonDocument object'''
        return BaseDocument(
            article_id = self.id,
            title = self.title,
            url = self.link,
            image_url = self.image_url,
            published_at=self.published,
            source_name = self.source or 'Unknown',
            content = self.content,
            description = self.summary,
            author = self.author#", ".join(self.creator) if self.creator else None
        )
    
class AriseModel(BaseModel):
    ''''pydantic model for the news data api '''

    id : str
    title : str
    link : str
    image_url : Optional[str]
    summary : Optional[str]
    published : str
    source : Optional[str]
    author : Optional[Union[str,list[str]]]
    content :   Optional[str]

    def to_base(self) -> BaseDocument:
        '''Convert the thevergemodel to a CommonDocument object'''
        return BaseDocument(
            article_id = self.id,
            title = self.title,
            url = self.link,
            image_url = self.image_url,
            published_at=self.published,
            source_name = self.source or 'Unknown',
            content = self.content,
            description = self.summary,
            author = self.author#", ".join(self.creator) if self.creator else None
        )
    
class ArtsModel(BaseModel):
    ''''pydantic model for the news data api '''

    id : str
    title : str
    link : str
    image_url : Optional[str]
    summary : Optional[str]
    published : str
    source : Optional[str]
    author : Optional[Union[str,list[str]]]
    content :   Optional[str]

    def to_base(self) -> BaseDocument:
        '''Convert the thevergemodel to a CommonDocument object'''
        return BaseDocument(
            article_id = self.id,
            title = self.title,
            url = self.link,
            image_url = self.image_url,
            published_at=self.published,
            source_name = self.source or 'Unknown',
            content = self.content,
            description = self.summary,
            author = self.author#", ".join(self.creator) if self.creator else None
        )