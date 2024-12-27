import random
import requests
import os
import instructor

from datetime import datetime, timedelta
from wonderwords import RandomWord
from pydantic import BaseModel
from openai import OpenAI
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from dotenv import load_dotenv


load_dotenv()

client = instructor.from_openai(OpenAI())
API_BASE_URL = os.getenv("API_BASE_URL")
VERBOSE = True

class Poll(BaseModel):
    question: str
    choices: list[str]

def vprint(*args, **kwargs):
    if VERBOSE:
        print(args, kwargs)

def create_poll() -> int:
    # Logic for creating a poll (e.g., POST to /polls)
    vprint("create_poll")

    topic = RandomWord().word(
        include_parts_of_speech = ["nouns"],
        word_min_length = 4,
        word_max_length = 8
    )

    poll   = client.chat.completions.create(
        model = "gpt-4o-mini",
        response_model = Poll,
        messages = [{"role" : "user", "content" : f"Generate a random poll related to {topic}"}],
        temperature = 0.8,
        top_p = 0.8
    )

    poll_data = {
        "question" : poll.question,
        "options"   : poll.choices
    }

    vprint(poll_data)

    try:
        response = requests.post(f"{API_BASE_URL}/create", json=poll_data)
        response.raise_for_status()  # Raise an error for HTTP error responses
        poll = response.json()
        vprint("Poll created successfully!")
        vprint(f"Poll ID: {poll['poll_id']}")
        return poll['poll_id']
    except requests.exceptions.RequestException as e:
        vprint("Error creating poll:", e)

def cast_votes() -> None:
    # Logic for voting on existing polls, possibly with random poll IDs
    vprint("cast_votes")
    polls = view_all_polls()

    poll_ids = [p["poll_id"] for p in polls]

    poll_id = random.choice(poll_ids)

    vprint("cast_votes", poll_id)
    
    response = requests.get(
            f"{API_BASE_URL}/result/{poll_id}"
    )

    if response.status_code == 200:
        data = response.json()
        vprint(data)
        result = data["results"]
    else:
        return
   
    if result is None:
        vprint("result was none")
        return

    vprint(result) 
    
    choices = list(result.keys())
    choice  = random.choice(choices)

    requests.post(
            f"{API_BASE_URL}/vote/{poll_id}",
            json={"option":choice}
    )

def view_poll_result() -> list:
    # Logic for viewing a single poll’s result (GET to /polls/<id>)
    vprint("view_poll_result")
    polls = view_all_polls()

    poll_ids = [p["poll_id"] for p in polls]

    poll_id = random.choice(poll_ids)
    vprint("view_poll_result", poll_id)
    response = requests.get(
            f"{API_BASE_URL}/result/{poll_id}"
    )

    if response.status_code == 200:
        data = response.json()
        vprint(data)
        return data["results"]
    vprint(response.status_code)
    return None


def view_all_polls() -> list:
    # Logic for viewing all polls’ results (GET to /polls)
    vprint("view_all_polls")
    response = requests.get(
        f"{API_BASE_URL}/results"
    )
    
    if response.status_code == 200:
        data = response.json()
        vprint(data)
        return data
    vprint(response.status_code)
    return None


# Create Polls DAG (weekday spikes at 9 AM, 12 PM, and 6 PM)
with DAG(
    dag_id="create_polls_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval="0 9,12,18 * * 1-5",
    catchup=False
) as create_polls_dag:
    create_poll_task = PythonOperator(
        task_id="create_poll_task",
        python_callable=create_poll
    )

# Create Polls DAG super frequently 
with DAG(
    dag_id="create_polls_dag_frequent",
    start_date=datetime(2024, 1, 1),
    schedule_interval=timedelta(minutes=30),
    catchup=False
) as create_polls_dag:
    create_poll_task = PythonOperator(
        task_id="create_poll_task",
        python_callable=create_poll
    )

# Cast Votes DAG 
with DAG(
    dag_id="cast_votes_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval=timedelta(seconds=10),
    catchup=False
) as cast_votes_dag:
    cast_votes_task = PythonOperator(
        task_id="cast_votes_task_frequent",
        python_callable=cast_votes
    )
    
with DAG(
    dag_id="cast_votes_dag_weekend",
    start_date=datetime(2024, 1, 1),
    schedule_interval="*/1 * * * 6,0",  # Sat & Sun
    catchup=False
) as cast_votes_dag_weekend:
    cast_votes_task = PythonOperator(
        task_id="cast_votes_task",
        python_callable=cast_votes
    )

# View Specific Poll Result DAG (every 5 minutes)
with DAG(
    dag_id="view_poll_result_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval=timedelta(seconds=10),
    catchup=False
) as view_poll_result_dag:
    view_poll_result_task = PythonOperator(
        task_id="view_poll_result_task",
        python_callable=view_poll_result
    )

with DAG(
    dag_id="view_poll_result_dag_weekend",
    start_date=datetime(2024, 1, 1),
    schedule_interval="*/1 * * * 6,0",  # Sat & Sun
    catchup=False
) as view_poll_result_dag:
    view_poll_result_task = PythonOperator(
        task_id="view_poll_result_task_weekend",
        python_callable=view_poll_result
    )

# View All Polls DAG (every 30 seconds)
with DAG(
    dag_id="view_all_polls_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval=timedelta(seconds=30),
    catchup=False
) as view_all_polls_dag:
    view_all_polls_task = PythonOperator(
        task_id="view_all_polls_task",
        python_callable=view_all_polls
    )

with DAG(
    dag_id="view_all_polls_dag_weekend",
    start_date=datetime(2024, 1, 1),
    schedule_interval="*/1 * * * 6,0",  # Sat & Sun
    catchup=False
) as view_all_polls_dag:
    view_all_polls_task = PythonOperator(
        task_id="view_all_polls_task_weekend",
        python_callable=view_all_polls
    )
