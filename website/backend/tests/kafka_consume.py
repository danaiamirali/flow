from kafka import KafkaConsumer
from dotenv import load_dotenv

import os
import json

load_dotenv()

def main():
    topic_name = "backend-logs"

    consumer = KafkaConsumer(
        topic_name,
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "").split(","),
        api_version=(3,7,0),
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-512",
        sasl_plain_username=os.getenv("KAFKA_USERNAME", "doadmin"),
        sasl_plain_password=os.getenv("KAFKA_PASSWORD"),
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
        auto_offset_reset="earliest",  # 'earliest' or 'latest'
        enable_auto_commit=True,       # automatically mark messages as consumed
        group_id="simple-consumer",    # give your consumer group a unique name
        ssl_cafile="../ca-certificate.crt"
    )
    
    print(f"Subscribed to topic: {topic_name}")
    try:
        for message in consumer:
            # message value is raw bytes; decode if needed
            msg_value = message.value
            print(
                f"Received message: {msg_value} | "
                f"Topic: {message.topic} | "
                f"Partition: {message.partition} | "
                f"Offset: {message.offset}"
            )
    except KeyboardInterrupt:
        print("Shutting down consumer...")
    finally:
        consumer.close()

if __name__ == "__main__":
    main()

