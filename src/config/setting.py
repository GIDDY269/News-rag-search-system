from pydantic_settings import BaseSettings 





class Settings(BaseSettings):

    KAFKA_BOOTSTRAP_SERVERS : str
    KAFKA_TOPIC: str
    KAFKA_USERNAME: str
    KAFKA_PASSWORD: str
    KAFKA_SECURITY_PROTOCOL: str
    KAFKA_SASL_MECHANISM: str
    KAFKA_ACKS: str

    
    NEWSAPI_KEY: str
    NEWSDATAIO_KEY: str
    NEWS_TOPIC: str 
    ARTICLES_BATCH_SIZE: int = 5 

    FETCH_WAIT_WINDOW: int = 3600  # seconds (30 minutes)


    GOOGLE_EMBEDDING_MODEL :str = "models/text-embedding-004" #(8192)
    GOOGLE_API_KEY :str
    GOOGLE_CHUNCK_MAX_INPUT_LENGTH : int = 2000
    GOOGLE_CHUNCK_OVERLAP: int = 200
    GOOGLE_VECTOR_SIZE : int = 768


    EMBEDDING_MODEL_ID: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_MODEL_MAX_INPUT_LENGTH: int = 384
    EMBEDDING_MODEL_DEVICE: str = "cpu"
    

    QDRANT_BATCH_SIZE : int = 7
    QDRANT_COLLECTION_NAME : str 
    QDRANT_ENDPOINT : str
    QDRANT_API_KEY : str
    QDRANT_CLUSTER : str



    TECHCRUNCH_URL : str = 'https://techcrunch.com/feed/'
    THEVERGE_URL : str = 'https://www.theverge.com/rss/index.xml'
    CHANNELSTV_URL : str = 'https://www.channelstv.com/feed/'
    ARISE_URL : str = 'https://www.arise.tv/feed/'
    ARTS_URL : str = "https://feeds.arstechnica.com/arstechnica/index"
    CBS_URL : str = "https://www.cbssports.com/rss/headlines/soccer/"


    GROQ_API_KEY: str
    GROQ_MODEL_ID: str 


    class config:
        env_file = ".env"



