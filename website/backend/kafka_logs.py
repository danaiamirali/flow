from kafka import KafkaProducer
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv
from pydantic import BaseModel
import traceback
import os
import json

load_dotenv()

certificate = os.getenv("CA_CERTIFICATE")
with open("ca-certificate.crt", 'w') as f:
    f.write(certificate)

def to_serializable(value):
    if isinstance(value, BaseModel):
        return value.dict()
    elif isinstance(value, (list, tuple)):
        return [to_serializable(v) for v in value]
    elif isinstance(value, dict):
        return {k: to_serializable(v) for k, v in value.items()}
    return value

class KafkaLogger:
    def __init__(self):
        # Kafka Configuration
        print("Setting up Kafka producer...")
        print("bootstrap_servers", os.getenv("KAFKA_BOOTSTRAP_SERVERS", "").split(","))
        print("username", os.getenv("KAFKA_USERNAME", "doadmin"))
        print("password", os.getenv("KAFKA_PASSWORD"))

        self.producer = KafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "").split(","),
            api_version=(3,7,0),
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-512",
            sasl_plain_username=os.getenv("KAFKA_USERNAME", "doadmin"),
            sasl_plain_password=os.getenv("KAFKA_PASSWORD"),
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            ssl_cafile="ca-certificate.crt"
        )

        print("Set up Kafka producer.")

    def log(self, topic: str, event: str, data: dict):
        """
        Logs a structured message to Kafka.

        Args:
            topic (str): Kafka topic to send the message.
            event (str): Event type (e.g., "POLL_CREATED", "VOTE_CAST").
            data (dict): Additional data related to the event.
        """
        message = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "data": data,
        }

        self.producer.send(topic, value=message)
        self.producer.flush()

kafka_logger = KafkaLogger()

def log_event(event_type):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                log_data = {
                    "function": func.__name__,
                    "args": [to_serializable(a) for a in args],
                    "kwargs": {k: to_serializable(v) for k, v in kwargs.items()}
                }

                kafka_logger.log(
                    topic="backend-logs",
                    event=f"{event_type}_STARTED",
                    data=log_data,
                )

                result = await func(*args, **kwargs)
                
                kafka_logger.log(
                    topic="backend-logs",
                    event=f"{event_type}_COMPLETED",
                    data={"function": func.__name__, "result": result},
                )
                
                return result
            except Exception as e:
                kafka_logger.log(
                    topic="backend-logs",
                    event=f"{event_type}_ERROR",
                    data={
                        "function": func.__name__,
                        "error": str(e),
                        "trace": traceback.format_exc(),
                    },
                )
                raise
        return wrapper
    return decorator
