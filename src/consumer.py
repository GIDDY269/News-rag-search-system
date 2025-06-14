import json
from typing import List


from bytewax.connectors.kafka import KafkaSinkMessage, KafkaSource 



from utils.logger import setup_logger
from config.setting import Settings
from config.pydantic_models import BaseDocument


logger = setup_logger()
settings = Settings()


def build_kafka_source() -> KafkaSource:
    """Builds a Kafka source for consuming messages."""
    
    kafka_config = {
        "bootstrap.servers" : settings.KAFKA_BOOTSTRAP_SERVERS,
        "auto.offset.reset" : "earliest",  # Start consuming from the earliest message
        "security.protocol" : settings.KAFKA_SECURITY_PROTOCOL,
        "sasl.mechanism" : settings.KAFKA_SASL_MECHANISM,
        "sasl.username" : settings.KAFKA_USERNAME,
        "sasl.password" : settings.KAFKA_PASSWORD,
    }

    kafka_input = KafkaSource(
        topics= [settings.KAFKA_TOPIC],
        brokers = [settings.KAFKA_BOOTSTRAP_SERVERS],
        add_config=kafka_config
    )

    logger.info(f"Kafka source created for topic: {settings.KAFKA_TOPIC} with brokers: {settings.KAFKA_BOOTSTRAP_SERVERS} successfully.")

    return kafka_input

def process_messages(messages: KafkaSinkMessage) -> List[BaseDocument]:
    """Processes incoming Kafka messages and converts them to list of BaseDocument objects."""

    documents: List[BaseDocument] = []
    try:

        json_str  = messages.value.decode("utf-8")
        logger.info(f"Received message from Kafka: {type(json_str)}")
        data = json.loads(json_str)
        
        doc = BaseDocument.from_json(data) # convert to basedocument
        documents.append(doc)
        logger.info(f"Processed {len(documents)} messages from Kafka.")
        return documents
    
    except StopIteration:
        logger.info("No more messages to process.")
    except KeyError as e:
        logger.error(f"KeyError while processing messages: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError while processing messages: {e}")
        raise 
    except Exception as e:
        logger.error(f"Unexpected error while processing messages: {e}")
