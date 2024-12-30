from pyspark.sql import SparkSession
from pyspark import SparkConf
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
import os
from dotenv import load_dotenv

load_dotenv()

def create_spark_session():
    """Create and return a Spark session."""
    try:

        spark = (SparkSession.builder
                .appName("SparkStreamKafka")
                .config('spark.jars.packages', 'org.apache.hadoop:hadoop-aws:3.3.4,org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,org.apache.kafka:kafka-clients:2.8.0,org.apache.hadoop:hadoop-common:3.3.6')
                .getOrCreate()
             )

        sc = spark.sparkContext
        sc._jsc.hadoopConfiguration().set('fs.s3a.access.key', os.getenv('AWS_ACCESS_KEY')) 
        sc._jsc.hadoopConfiguration().set('fs.s3a.secret.key', os.getenv('AWS_SECRET_KEY'))

        print("BUILT SESSION COMPLETE!")
        return spark
    except Exception as e:
        print(f"Error creating spark session: {e}")
        return None

def create_kafka_stream(spark):
    """Create and return a Kafka stream DataFrame."""
    kafka_bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
    kafka_username = os.getenv('KAFKA_USERNAME')
    kafka_password = os.getenv('KAFKA_PASSWORD')
    topic_name = "backend-logs"

    try:
        df_kafka_raw = (spark.readStream
                        .format("kafka")
                        .option("kafka.bootstrap.servers", kafka_bootstrap_servers)
                        .option("subscribe", topic_name)
                        .option("kafka.security.protocol", "SASL_SSL")
                        .option("kafka.sasl.mechanism", "PLAIN")
                        .option("kafka.sasl.jaas.config", f'org.apache.kafka.common.security.plain.PlainLoginModule required username="{kafka_username}" password="{kafka_password}";')
                        .option("kafka.ssl.truststore.location", os.getcwd() + "/truststore.jks")
                        .option("kafka.ssl.truststore.password", os.getenv('TRUSTSTORE_PASS'))
                        .load())
        print("Kafka dataframe complete!")
        return df_kafka_raw
    except Exception as e:
        print(f"Error creating kafka dataframe: {e}")
        return None

def main():
    # Create spark session and define our Dataframe
    spark = create_spark_session()
    df_kafka_raw = create_kafka_stream(spark)

    # Define a json schema
    logs_schema = StructType([
        StructField("timestamp", StringType(), True),
        StructField("event", StringType(), True)
    ])

    # Select the 'value' column and cast it to string
    df_raw_string = df_kafka_raw.selectExpr("CAST(value AS STRING) AS json_str")

    # Parse json
    parsed_df = df_raw_string.select(
        from_json(col("json_str"), logs_schema).alias("parsed")
    ).select("parsed.*")
    
    s3_path = os.getenv('AWS_S3_URL')
    checkpoint_location = s3_path + "/checkpoints"

    query = (
        parsed_df.writeStream
        .outputMode("append")
        .format("csv")
        .option("path", s3_path)
        .foreachBatch(foreach_batch_function)
        .option("checkpointLocation", checkpoint_location)
        .start()
    )


    query.awaitTermination()

if __name__ == "__main__":
    main()