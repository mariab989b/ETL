#!/usr/bin/env python3
import os
import logging
import sys
import confluent_kafka
from kafka.admin import KafkaAdminClient, NewTopic
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

kafka_brokers = os.getenv("REDPANDA_BROKERS", "127.0.0.1:19092")
topic_name = os.getenv("KAFKA_TOPIC", "perfume_orders")

def create_topic():
    try:
        admin = KafkaAdminClient(bootstrap_servers=kafka_brokers)
        topics = admin.list_topics()
        if topic_name not in topics:
            logging.info(f"📝 Creating topic: {topic_name}")
            topic = NewTopic(name=topic_name, num_partitions=10, replication_factor=1)
            admin.create_topics([topic])
            logging.info(f"✅ Topic '{topic_name}' created")
        else:
            logging.info(f"✅ Topic '{topic_name}' exists")
    except Exception as e:
        logging.error(f"❌ Error: {e}")

def get_producer():
    return confluent_kafka.Producer({
        'bootstrap.servers': kafka_brokers,
        'client.id': 'perfume_producer',
        'acks': 'all',
        'compression.type': 'none'  # PAS DE COMPRESSION
    })

def main():
    print(f"🚀 Kafka Publisher - Perfume Orders")
    print(f"📊 Topic: {topic_name}")
    print(f"🔌 Brokers: {kafka_brokers}")
    print("=" * 60)
    
    create_topic()
    producer = get_producer()
    published = 0
    
    print("📡 Publishing messages...")
    
    for line in sys.stdin:
        line = line.strip()
        if line:
            producer.produce(topic_name, value=line.encode('utf8'))
            published += 1
            if published % 10 == 0:
                print(f"📊 Published {published} orders...")
    
    producer.flush()
    print(f"\n✅ Successfully published {published} orders!")

if __name__ == "__main__":
    main()