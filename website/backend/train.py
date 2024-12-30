import os
from dotenv import load_dotenv
load_dotenv()

import boto3
import pandas as pd
import pickle

import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA

def main():
    s3_url = os.getenv("AWS_S3_URL")  
    if not s3_url:
        raise ValueError("AWS_S3_URL environment variable not set.")

    # Strip off the "s3a://" prefix for native Boto3 usage:
    if s3_url.startswith("s3a://"):
        s3_url_clean = s3_url[5:]  # remove 's3a://'
    else:
        s3_url_clean = s3_url

    # Split into bucket and prefix; we only want the bucket name
    parts = s3_url_clean.split("/", 1)
    bucket = parts[1]                # e.g. "backendlogs-kafka"

    # Initialize Boto3 S3 client
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_KEY")
    )

    # List all objects under the prefix
    response = s3.list_objects_v2(Bucket=bucket) 
    if "Contents" not in response:
        print("No objects found at that S3 location. Exiting.")
        return

    # Read and combine all CSVs
    dfs = []
    for obj in response["Contents"]:
        key = obj["Key"]
        if key.endswith(".csv"):
            print(f"Reading CSV: s3://{bucket}/{key}")
            csv_obj = s3.get_object(Bucket=bucket, Key=key)
            # Each line: "2024-12-30T19:00:36.483088,GET_ALL_RESULTS_STARTED"
            # We'll assume no header row, so specify columns:
            df_temp = pd.read_csv(csv_obj["Body"], names=["timestamp", "event"], header=None)
            dfs.append(df_temp)

    if not dfs:
        print("No CSV files found under that prefix. Exiting.")
        return

    df = pd.concat(dfs, ignore_index=True)
    print(f"Combined dataframe shape: {df.shape}")

    # Convert timestamps
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)

    # If you want to group by hour/minute instead, adjust 'freq' below.
    daily_counts = df.resample("D").size()

    # Train ARIMA model
    # (order=(1, 1, 1) is just an example)
    model = ARIMA(daily_counts, order=(1, 1, 1))
    results = model.fit()
    print(results.summary())

    # Save the fitted ARIMA model locally
    with open("arima_model.pickle", "wb") as f:
        pickle.dump(results, f)

    print("Trained ARIMA model has been saved as 'arima_model.pickle'.")

if __name__ == "__main__":
    main()
