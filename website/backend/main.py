from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://0.0.0.0:8080", "http://localhost:8080"],  # Add frontend's origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Database setup
def initialize_database():
    with open("sql/create_tables.sql", "r") as sql_file:
        schema = sql_file.read()
    cursor.executescript(schema)
    conn.commit()

conn = sqlite3.connect("polls.db", check_same_thread=False)
cursor = conn.cursor()
initialize_database()

# Pydantic Models
class PollCreate(BaseModel):
    question: str
    options: List[str]  # Add a list of options

class Vote(BaseModel):
    option: str

# Routes
@app.post("/create")
def create_poll(poll: PollCreate):
    # Insert the poll question
    cursor.execute("INSERT INTO polls (question) VALUES (?)", (poll.question,))
    poll_id = cursor.lastrowid

    # Insert each option into poll_options
    for option in poll.options:
        cursor.execute("INSERT INTO poll_options (poll_id, option) VALUES (?, ?)", (poll_id, option))
    conn.commit()

    return {"message": "Poll created successfully", "poll_id": poll_id}

@app.get("/poll")
def list_polls():
    cursor.execute("SELECT id, question FROM polls")
    polls = cursor.fetchall()
    return [{"id": p[0], "question": p[1]} for p in polls]

@app.get("/vote/{poll_id}")
def get_poll(poll_id: int):
    cursor.execute("SELECT question FROM polls WHERE id=?", (poll_id,))
    poll = cursor.fetchone()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    cursor.execute("SELECT id, option FROM poll_options WHERE poll_id=?", (poll_id,))
    options = cursor.fetchall()

    return {
        "poll_id": poll_id,
        "question": poll[0],
        "options": [{"id": opt[0], "option": opt[1]} for opt in options]
    }

@app.post("/vote/{poll_id}")
def cast_vote(poll_id: int, vote: Vote):
    cursor.execute("SELECT id FROM polls WHERE id=?", (poll_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Poll not found")
    cursor.execute("INSERT INTO votes (poll_id, option) VALUES (?, ?)", (poll_id, vote.option))
    conn.commit()
    return {"message": "Vote cast successfully"}

@app.get("/result/{poll_id}")
def get_result(poll_id: int):
    cursor.execute("SELECT question FROM polls WHERE id=?", (poll_id,))
    poll = cursor.fetchone()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    cursor.execute("SELECT option, COUNT(option) FROM votes WHERE poll_id=? GROUP BY option", (poll_id,))
    results = cursor.fetchall()
    return {
        "poll_id": poll_id,
        "question": poll[0],
        "results": {r[0]: r[1] for r in results}
    }

@app.get("/results")
def get_all_results():
    # Fetch all polls
    cursor.execute("SELECT id, question FROM polls")
    polls = cursor.fetchall()

    # Prepare a list of results for each poll
    all_results = []
    for poll in polls:
        poll_id, question = poll
        cursor.execute("SELECT option, COUNT(option) FROM votes WHERE poll_id=? GROUP BY option", (poll_id,))
        results = cursor.fetchall()

        # Include all options, even if no votes
        cursor.execute("SELECT option FROM poll_options WHERE poll_id=?", (poll_id,))
        options = [opt[0] for opt in cursor.fetchall()]
        result_dict = {option: 0 for option in options}
        for option, count in results:
            result_dict[option] = count

        all_results.append({
            "poll_id": poll_id,
            "question": question,
            "results": result_dict
        })

    return all_results
