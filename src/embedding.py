import traceback
from pathlib import Path
from threading import Lock
from typing import Optional, Union


import numpy as np
from transformers import AutoTokenizer, AutoModel

from config.setting import Settings
from utils.logger import setup_logger


logger = setup_logger()
settings = Settings()


class SingletonMeta(type): # Singleton metaclass, metaclasses are classes that define the behavior of other classes. They are used to create classes that can have special behavior, such as enforcing a single instance of a class.
    """A thread-safe implementation of Singleton."""
    _instances = {}
    _lock: Lock = Lock()
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances: # Check if the instance already exists
            # Acquire the lock to ensure thread safety, when a thread has a lock, no other thread can acquire it until the lock is released.
            # This is important to prevent multiple threads from creating multiple instances of the class.
            with cls._lock:
                if cls not in cls._instances: # double-checked locking
                    # Check if the class is a subclass of Embeddings model
                    # double checking is necessary to ensure that the instance is created only once as a thread can create an instance before the current thread acquires the lock.
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]
    

class TextEmbedder(metaclass=SingletonMeta):
    ''' A class for embedding text using a pre-trained model.
    This class is a singleton, meaning that only one instance of it can exist at a time.'''

    def __init__(self, model_id: str = settings.EMBEDDING_MODEL_ID,
                 max_input_length: int = settings.EMBEDDING_MODEL_MAX_INPUT_LENGTH,
                 device: str = settings.EMBEDDING_MODEL_DEVICE,
                 cache_dir : Optional[Path] = None,
                 token_limit: int = 256,):
        
        self._model_id = model_id
        self._max_input_length = int(max_input_length)
        self._device = device
        self._token_limit = token_limit

        self._tokenizer = AutoTokenizer.from_pretrained(model_id)
        self._model = AutoModel.from_pretrained(model_id, cache_dir= str(cache_dir) if cache_dir else None).to(self._device)
        self._model.eval()

    @property
    def model_id(self) -> str:
        return self._model_id
    
    @property
    def max_input_length(self) -> int:
        return int(self._max_input_length)
    
    @property 
    def tokenizer(self) -> AutoTokenizer:
        return self._tokenizer
    
    @property
    def token_limit(self) -> str:
        return self._token_limit
    

    def __call__(self, text: str , to_list: bool =True) -> Union[np.ndarray, list]:

        try:
            tokenized_text = self._tokenizer(
                text,
                truncation = True,
                max_length = self._max_input_length,
                return_tensors = "pt",
                padding = True).to(self._device )
            
        except Exception as e:
            logger.error(f"Error tokenizing text: {text}\n{traceback.format_exc()}")
            logger.error(f"Error tokeninzing the following input text : {text}")

            return [] if to_list else np.array([]) # returns empty list or array if tokenization fails
        
        try:
            result = self._model(**tokenized_text)
        except Exception as e:
            logger.error(f"Error running model on tokenized text: {text}\n{traceback.format_exc()}")
            logger.error(f"Error running model ({self._model_id}) on the following input text : {text}")
            return [] if to_list else np.array([])
        
        embeddings = result.last_hidden_state[:,0,:].cpu().detach().numpy()
        if to_list:
            return embeddings.flatten().tolist()
        else:
            return embeddings
                            
                    
