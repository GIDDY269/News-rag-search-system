from typing import Optional,Set,Dict
from datetime import datetime,timedelta,timezone
from pathlib import Path
from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.outputs import DynamicSink
from bytewax.connectors.kafka import KafkaSource

from consumer import process_messages, build_kafka_source
from embedding import GoogleTextEmbedder
from config.pydantic_models import ChuckedDocument, EmbedDocument, RefinedDocument
from utils.logger import setup_logger
from vector_database import QdrantVectorOutput



logger = setup_logger()


class deduplicates_check:
    """A class to handle deduplication of news articles based on their IDs.
    It maintains a dict of seen IDs and last seen time and checks if a new article's ID has been seen before.
    If not, it adds the ID to the dict and marks the article as new.
    """

    _state : Dict[str,datetime] = dict()

    @classmethod
    def  updates_articles_seen_state(cls,state, news_item) : 

        """Checks if a new_items's ID has been seen before.
        Updates the seen_ids list  and adds and 'is_new' flag to the news_item refined_document.
        Args:
            state (dict[str,datetime]): dict of IDs that have been seen.
            news_item (RefinedDocument): The news item to check and update.
            """
        
        doc_id = news_item.doc_id
        current_time = datetime.now(timezone.utc)
        expiry_duration = timedelta(hours=24)
        
        if state is None:
            state = cls._state
        
        # Check if the news_item's doc_id is in the seen_ids list
        is_new = False
        if doc_id not in state:
            is_new = True
           # news_item_copied = news_item.model_copy(update = {'is_new': True}) 
            #seen_ids.add(news_item.doc_id)
            logger.info(f"New article detected: {doc_id}")
        else:
            #news_item_copied = news_item.model_copy(update = {'is_new': False}) # Update the is_new flag to False, basemodel are immutable
            logger.info(f"Article already seen: {doc_id}")

        state[doc_id] = current_time

        ids_to_remove = []
        for exisiting_doc_id,last_seen_time in state.items():
            if current_time - last_seen_time >  expiry_duration:
                ids_to_remove.append(exisiting_doc_id)

        for remove_id in ids_to_remove:
            del state[remove_id]
            logger.info(f"Removed expired ID: {remove_id}. Current state size: {len(state)}")
        
        updated_news_item = news_item.model_copy(update={'is_new': is_new})
        return state, updated_news_item
    
    @property
    def get_seen_ids(cls) -> Set[str]:
        """Returns the set of seen IDs."""
        return cls._seen_ids
    



def build(model_cache_dir: Optional[Path] = None
          ) -> Dataflow:
    
    """
    Build the ByteWax dataflow for the Qdrant db.
    Follows this dataflow:
        * 1. Tag: ['kafka_input']   = The input data is read from a KafkaSource
        * 2. Tag: ['map_kinp']      = Process message from KafkaSource to CommonDocument
        * 3. Tag: ['refine']        = Convert the message to a refined document format
        * 4. Tag: ['key_on']        = Add key(news id) to the refined document (id, refine)
        * 5. Tag: ['Deduplicate']   = Check if new article been seen before
        * 6. Tag: ['drop_key']      = Drop key
        * 7. Tag: ['filter_new_only'] = Filter out seen articles
        * 8. Tag: ['chunkenize']    = Split the refined document into smaller chunks
        * 9. Tag: ['embed']         = Generate embeddings for the chunks
        * 10. Tag: ['output']        = Write the embeddings to the Upstash vector database
    """
    
    #model = TextEmbedder(cache_dir=model_cache_dir)
    model = GoogleTextEmbedder()

    dataflow  = Dataflow(flow_id="news-to-qdrant")
    stream = op.input(
        step_id="kafka_input",
        flow=dataflow,
        source= _build_input()
    )

    stream = op.flat_map('map_kinp' , stream, process_messages)
    #_ = op.inspect("dbg_map_kinp", stream)


    stream = op.map('refine', stream, RefinedDocument.from_base)
    #_ = op.inspect("dbg_refine", stream)

    stream = op.key_on(
        'key_on',
        stream, 
        lambda doc : doc.doc_id)
    #_ = op.inspect("dgb_key_on", stream)
    
    
    stream = op.stateful_map('deduplicates',
                              stream, # empty initail list  to store seen ids\
                            deduplicates_check.updates_articles_seen_state)
    #_ = op.inspect("dbg_deduplicates", stream)

    

    stream = op.map(
            "drop_key",
            stream,
            lambda key_doc: key_doc[1]  # extract the document
        )
    _ = op.inspect("dbg_dop_key", stream)

    # 2. Keep only the new ones
    stream = op.filter(                              
        step_id="/filter_new_only",
        up=stream,
        predicate=lambda item: getattr(item, "is_new", False)
        )
    #_ = op.inspect("dbg_filter", stream)


    
    stream = op.flat_map('chunkenize',
                         stream,
                         lambda refined_doc : ChuckedDocument.from_refined(refined_doc, model))
    _ = op.inspect("dbg_chunk", stream)
    
    
    stream = op.map(
        'embed',
        stream,
        lambda chunked_doc: EmbedDocument.from_chunked(chunked_doc, model)
    )
    
    _ = op.inspect("dbg_embed", stream)
    stream = op.output("output", stream, _build_output())
    logger.info("Successfully created bytewax dataflow.")
    logger.info(
        "\tStages: Kafka Input -> Map -> Refine -> Key-on -> Deduplicate -> Drop-key -> Chunkenize -> Embed -> Upsert"
    )
    return dataflow


def _build_input() -> KafkaSource:
    return build_kafka_source()

def _build_output() -> DynamicSink:
    return QdrantVectorOutput()

    