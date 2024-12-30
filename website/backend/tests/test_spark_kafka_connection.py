import unittest
from pyspark.sql import SparkSession
import os
from dotenv import load_dotenv
import tempfile

load_dotenv()

class TestPysparkKafkaConnectivity(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.spark = SparkSession.builder \
            .appName('PysparkKafkaTest') \
            .master("local[*]") \
            .config('spark.jars.packages', 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,org.apache.kafka:kafka-clients:2.8.0') \
            .getOrCreate()
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_kafka_stream(self):
        kafka_bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
        kafka_username = os.getenv('KAFKA_USERNAME')
        kafka_password = os.getenv('KAFKA_PASSWORD')
        topic_name = "backend-logs"

        try:
            kafka_df_stream = self.spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
                .option("subscribe", topic_name) \
                .option("kafka.security.protocol", "SASL_SSL") \
                .option("kafka.sasl.mechanism", "PLAIN") \
                .option("kafka.sasl.jaas.config", f'org.apache.kafka.common.security.plain.PlainLoginModule required username="{kafka_username}" password="{kafka_password}";') \
                .option("kafka.ssl.truststore.location", "/root/pyspark/truststore.jks") \
                .option("kafka.ssl.truststore.password", os.getenv("TRUSTSTORE_PASS")) \
                .load()
            
            with tempfile.TemporaryDirectory() as d:
                query = kafka_df_stream \
                    .writeStream \
                    .outputMode("append") \
                    .format("json") \
                    .option("path", d) \
                    .option("checkpointLocation", f"{d}/checkpoint") \
                    .start()

                query.processAllAvailable()  # Process all available data
                query.stop()

                # Validate files are written to the directory
                output_files = os.listdir(d)
                if not output_files:
                    raise AssertionError("No files written to the output directory!")
        
        except Exception as e:
            self.fail(f"Kafka connectivity test failed: {e}")
