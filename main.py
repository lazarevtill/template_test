import requests
from confluent_kafka import Producer
# from kafka import KafkaProducer
import os
import redis
# import threading
from urllib.parse import urlparse

# import boto3

# Kafka configuration
bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
topic_name = os.getenv('KAFKA_TOPIC', 'upload')

# Redis configuration
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_db = int(os.getenv('REDIS_DB', 0))
file_key = os.getenv('FILE_PATH', 'file_path')

web_link = 'https://cdn2.thecatapi.com/images/0XYvRd7oD.jpg'


# AWS S3 configuration
# S3_access_key_id = os.getenv('S3_ACCESS_KEY_ID', 'your_access_key_id')
# S3_secret_access_key = os.getenv('S3_SECRET_ACCESS_KEY', 'your_secret_access_key')
# S3_region = os.getenv('S3_REGION', 'us-east-1')
# s3_bucket_name = os.getenv('S3_REGION', 'us-east-1')

# Connect to Redis
# redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db)

# Get the upload type from Redis
# upload_type_from_redis = redis_client.get('upload_type')

# Get file path from Redis
# file_path = redis_client.get(file_key)


def listen_for_new_items():
    # Connect to Redis
    r = redis.Redis(host=redis_host, port=redis_port, db=redis_db)

    # Create a pub/sub object
    pubsub = r.pubsub()

    # Subscribe to a channel
    pubsub.subscribe('upload')

    # Process incoming messages
    for message in pubsub.listen():
        if message['type'] == 'message':
            # New item added, print the message
            print("\nNew item:", message['data'].decode())
            return message['data']

# Function to upload file to Kafka topic
# def upload_to_kafka(file_from_redis):
#     # Create Kafka producer
#     producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
#
#     # Open file in binary mode
#     with open(file_from_redis, 'rb') as file:
#         # Read file content
#         content = file.read()
#
#         # Publish file content to Kafka topic
#         producer.send(topic_name, content)
#
#     # Close Kafka producer
#     producer.close()


# def upload_s3_object(object_key):
#     # Create S3 client
#     s3_client = boto3.client('s3', S3_access_key_id=S3_access_key_id,
#                              S3_secret_access_key=S3_secret_access_key,
#                              region_name=S3_region)
#
#     # Download the object from S3
#     response = s3_client.get_object(Bucket=s3_bucket_name, Key=object_key)
#     content = response['Body'].read()
#     upload_to_kafka(content)

# Check text to URL
def is_url(string):
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def upload_web_content_to_kafka(bootstrap_servers, topic, web_link):
    # Create Kafka producer configuration
    producer_config = {
        'bootstrap.servers': bootstrap_servers
    }

    # Create Kafka producer instance
    producer = Producer(producer_config)

    # Fetch the content from the web link
    response = requests.get(web_link)

    # Check if the request was successful
    if response.status_code == 200:
        # Get the content type
        content_type = response.headers.get('content-type')

        # Get the content data
        content_data = response.content

        # Produce the content to Kafka topic
        producer.produce(topic, key=web_link, value=content_data, headers={'Content-Type': content_type})

        # Flush the producer to ensure the message is sent
        producer.flush()

        # Wait for the message to be delivered (optional)
        producer.poll(1)

        print(f"Content from {web_link} uploaded to Kafka topic '{topic}'")
    else:
        print(f"Failed to fetch content from '{web_link}': {response.status_code}")

    # Gracefully close the producer
    producer.flush(timeout=5)
    producer.poll(10)
    producer.flush()


# # Start listening for new items in a separate thread
# thread = threading.Thread(target=listen_for_new_items)
# thread.start()

# Usage
while True:
    new_text_from_redis = listen_for_new_items()
    if is_url(new_text_from_redis):
        upload_web_content_to_kafka(bootstrap_servers, topic_name, new_text_from_redis)
    else:
        print("Error, not url or path to webfile:", new_text_from_redis)