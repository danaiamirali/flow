import os
from kafka.admin import KafkaAdminClient
from dotenv import load_dotenv

load_dotenv()

def main():
    # Environment variables or default values
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS").split(",")
    username = os.getenv("KAFKA_USERNAME", "doadmin")
    password = os.getenv("KAFKA_PASSWORD")

    print(bootstrap_servers)
    print(username)
    print(password)

    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            security_protocol="SASL_SSL",       # or "SSL" or "PLAINTEXT", depending on your config
            sasl_mechanism="SCRAM-SHA-512",    # only needed for SASL_SSL
            sasl_plain_username=username,
            sasl_plain_password=password,
            ssl_cafile="ca-certificate.crt"
        )
        topics = admin_client.list_topics()
        print("Connected successfully!")
        print("Available topics:", topics)
    except Exception as e:
        print("Error connecting to Kafka:", e)

if __name__ == "__main__":
    main()

