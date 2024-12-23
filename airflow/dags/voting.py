"""
DAG Workflow, voting on polls about every minute
"""
import random
import requests
import os

from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL: str = os.getenv("API_BASE_URL")

colors_distribution = [
        ("Red", 0.8),
        ("Blue", 0.2)
]

seasons_distribution = [
        ("Winter", 0.2),
        ("Spring", 0.1),
        ("Summer", 0.3),
        ("Fall", 0.4)
]

def pick_choice(distribution):
    r = random.random()
    cumulative = 0
    for choice, prob in distribution:
        cumulative += prob
        if r < cumulative:
            return choice

def cast_vote(poll_id):
    choice = pick_choice(colors_distribution if poll_id == 24 else seasons_distribution)
    # Adjust URL/endpoint as needed
    requests.post(
        f"{API_BASE_URL}/vote/{poll_id}",
        json={"option": choice}
    )

with DAG(
    "cast_votes_randomly",
    start_date=datetime(2024, 1, 1),
    schedule_interval="*/1 * * * *",  # every minute
    catchup=False
) as dag:

    vote_for_poll_24 = PythonOperator(
        task_id="vote_for_poll_24",
        python_callable=lambda: cast_vote(24)
    )

    vote_for_poll_25 = PythonOperator(
        task_id="vote_for_poll_25",
        python_callable=lambda: cast_vote(25)
    )

    vote_for_poll_24 >> vote_for_poll_25

