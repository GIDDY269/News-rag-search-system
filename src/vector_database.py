from typing import Optional, List

from bytewax.outputs import DynamicSink, StatelessSinkPartition
from qdrant_client import QdrantClient 
from qdrant_client.models import  Distance,PointStruct


from src.config.setting import Settings
from src.utils.logger import setup_logger
from src.config.pydantic_models import EmbedDocument


settings = Settings()
logger = setup_logger()



class QdrantVectorSink(StatelessSinkPartition):
    '''
    A sink that writes embeddings to qdrant vector database collection'''

    def __init__(self,
                 client: QdrantClient,
                 collection_name :str = None):
        
        self._client = client
        self._qdrant_batch_size = settings.QDRANT_BATCH_SIZE
        self._collection_name = collection_name


       
        if self._client.collection_exists(collection_name) is False:
            self._client.create_collection(
                    collection_name=collection_name,
                    vectors_config={
                        "size": settings.EMBEDDING_MODEL_MAX_INPUT_LENGTH,
                        "distance": Distance.COSINE
                    }
                )
            logger.info(f"Collection '{collection_name}' created successfully.")
        
        

    
    def write_batch(self,documents: List[EmbedDocument]):

        ''' Write a batch pf document embeddings to the configured qdrant Vector database collection
        
        Args:
            documents (List[EmbeddedDocument]): The documents to write.
        '''

        vectors  = [
            PointStruct(
                id = doc.doc_id,
                vector= doc.embedding,
                payload=doc.metadata
            ) for doc in documents
        ]

        for i in range(0, len(vectors), self._qdrant_batch_size):
            batch_vectors = vectors[i : i + self._qdrant_batch_size]
            try:
                self._client.upsert(
                    collection_name=self._collection_name,
                    wait =True,
                    points=batch_vectors
                )
                logger.info(
                    f"Upserted {len(batch_vectors)} points to collection '{self._collection_name}'."
                )
            except Exception as e:
                logger.error(f"Caught an exception during batch upsert {e}")



    
class QdrantVectorOutput(DynamicSink):
    '''A class representing the Qdrant vector output'''
    

    def __init__(
            self,
            vector_size:int = settings.EMBEDDING_MODEL_MAX_INPUT_LENGTH,
            collection_name: str = settings.QDRANT_COLLECTION_NAME,
            client: Optional[QdrantClient] = None   
            ):
        
        self._collection_name = collection_name
        self._vector_size = vector_size

        if client:
            self.client = client
        else :
            self.client = QdrantClient(
                url = settings.QDRANT_ENDPOINT,
                api_key= settings.QDRANT_API_KEY
            )

    def build(
            self, step_id: str , worker_index:int , 
            worker_count:int) -> StatelessSinkPartition:
        
        return QdrantVectorSink(self.client,self._collection_name)
        