
from typing import Optional, Union,List

import google.generativeai as genai

import numpy as np


from config.setting import Settings
from utils.logger import setup_logger


logger = setup_logger()
settings = Settings()



class GoogleTextEmbedder():

    def __init__(self,model_id:str =settings.GOOGLE_EMBEDDING_MODEL) :
        
        self._model_id  = model_id
        self._genai = genai.configure(api_key=settings.GOOGLE_API_KEY)


    def __call__(self,text:str ,task_type:str='RETRIEVAL_DOCUMENT') -> list[float] :
        """"Generates an embedding for the given text using Google's embedding model"""
        logger.info('Generating embedding for text using Google Generative AI')
        try:
            response = genai.embed_content(
                model = self._model_id,
                content = [text],
                task_type=task_type
            )
            return response['embedding'][0]
        
        except Exception as e :
            logger.info(f'Error generating embeddings : {e}')
            return None

    @property
    def model_id(self) -> str:
        return self._model_id
                            
                    
