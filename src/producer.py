import threading
import json
import time
import fire
from typing import Callable,List,NoReturn
from confluent_kafka import Producer
from utils.logger import setup_logger
from fetch_news import NewsFetcher
from config.pydantic_models import BaseDocument
from config.setting import Settings
from dotenv import load_dotenv
load_dotenv()


settings = Settings()


logger = setup_logger()

class KafkaProducerThread(threading.Thread):
    '''
    A thread to produce messages tp Kafka topic.

    Attributes:
        producer_id (int): Identifier for the producer instance.
        topic (str): The Kafka topic to which messages will be produced.
        fetch_function (Callable): Function to fetch data to be sent to Kafka.
        producer (KafkaProducer): Kafka producer instance.
        wait_window_sec (int): Time to wait between message production in seconds.
        running (bool): Control flag for the running state of the thread.
    '''

    def __init__(self, 
                 producer_id: int, 
                 producer: Producer,
                 topic:str, 
                 fetch_function: Callable
                 ) -> None:
        super().__init__(daemon=True) # lets threading setup before the main thread
        self.producer_id = f'KafkaProducerThread # {producer_id}'
        self.producer = producer # use the shared producer instance
        self.topic = topic
        self.fetch_function = fetch_function
        self.wait_window_sec = settings.FETCH_WAIT_WINDOW # adjust the wait time as needed
        self.running = threading.Event()
        self.running.set()

    # failed delivery (after retries).
    @staticmethod
    def delivery_callback(err, msg):
        if err:
            logger.info(f'ERROR: Message failed delivery: {err}')
        else:
            key = msg.key().decode('utf-8') if msg.key() else 'No Key'
            value = msg.value().decode('utf-8') if msg.value() else 'No Value'
            logger.info(f"Produced event to topic {msg.topic()}: key = {key:12} value = {value:12}")

    def run(self) -> NoReturn:
        '''Continuously fetch data and produce messages to Kafka topic.'''
        logger.info(f'{self.producer_id} started.')
        while self.running.is_set():
            try:
                messages: List[BaseDocument] = self.fetch_function()
                logger.info(f'{self.producer_id} fetched {len(messages)} messages.')
                if messages:
                    messages_payload = [msg.to_kafka_payload() for msg in messages]
                    for message in messages_payload:
                        message = json.dumps(message).encode('utf-8')
                        self.producer.produce(self.topic,value=message,callback=self.delivery_callback)
                        
                    self.producer.poll(0)
                    self.producer.flush()
                    
                logger.info(
                    f'producer : {self.producer_id} sent : {len(messages)} msgs.'
                )

                logger.info(f'{self.producer_id} sleeping for {self.wait_window_sec / 60} minutes.')
                time.sleep(self.wait_window_sec) # wait for the next fetch
                
            except Exception as e:
                logger.error(f'Error in producer worker {self.producer_id}: {e}')
                self.running.clear() # stop the thread error

    def stop(self) -> None:
        '''Signals the thread to stop running and cloases the kafka Producer'''

        self.running.clear()
        self.producer.close()
        self.join()

class KafkaProducerSwarm:
    '''Manages the swarm of KafkaProducerThread instances for concurrent data 
    fetching and kafka message production.'''

    def __init__(self,
                 producer : Producer,
                 topic:str,
                 fetch_function: list[Callable]):
        self.producer_threads = [
            KafkaProducerThread(i,producer,topic , fetch_function)
            for i , fetch_function in enumerate(fetch_function)
        ] # use same producer instance for all threads for each fetch functions.
        
    def start(self) -> None:
        '''Starts all producer threads.'''

        for thread in self.producer_threads:
            thread.start()
           # logger.info(f'{thread.producer_id} started.')
        logger.info('All producer threads started.')

    def stop(self) -> None:
        '''Stops all producer threads.'''

        for thread in self.producer_threads:
            thread.stop()
            logger.info(f'{thread.producer_id} stopped.')
        for thread in self.producer_threads:
            thread.join()
            logger.info(f'{thread.producer_id} joined.')
        logger.info('All producer threads stopped.')



def create_producer() -> Producer:
    '''Creates a Kafka producer instance with the specified configuration.'''

    logger.info('Creating Kafka producer...')
    conf = {
    'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
    'security.protocol': settings.KAFKA_SECURITY_PROTOCOL,
    'sasl.mechanisms': settings.KAFKA_SASL_MECHANISM,
    'sasl.username': settings.KAFKA_USERNAME,
    'sasl.password': settings.KAFKA_PASSWORD
        }
    
    return Producer(**conf)

def main():
    '''main function to run the kafka producer swarm '''

    producer = create_producer()
    fetcher = NewsFetcher()

    multi_producer = KafkaProducerSwarm(
        producer = producer,
        topic=settings.KAFKA_TOPIC,
        fetch_function= fetcher.sources,
    )

    try:
        multi_producer.start()
        while True:
            time.sleep(1)
    finally:
        multi_producer.stop()
        producer.close()

if __name__ == "__main__":
    fire.Fire(main)
