import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from kafka_logs import log_event
from database import Database, execute_sql_file
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Change to DEBUG, WARNING, ERROR, or disable as needed

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://0.0.0.0:8080",
        "http://localhost:8080",
        "https://flow-gamma-kohl.vercel.app",
        "https://flow-f2pe4skl5-danaiamiralis-projects.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    logger.info("Initializing database pool and executing SQL file.")
    await Database.init_pool()
    await execute_sql_file("sql/initialize_tables.sql")
    logger.info("Creating certificate.")
    certificate = os.getenv("CA_CERTIFICATE")
    with open("ca-certificate.crt", 'w') as f:
        f.write(certificate)

# Pydantic Models
class PollCreate(BaseModel):
    question: str
    options: List[str]

class Vote(BaseModel):
    option: str

@app.post("/create")
@log_event("POLL_CREATION")
async def create_poll(poll: PollCreate):
    logger.info("Received request to create a new poll.")
    async with Database.get_connection() as conn:
        poll_id = await conn.fetchval(
            "INSERT INTO polls (question) VALUES ($1) RETURNING id", poll.question
        )
        logger.debug(f"Created poll with ID: {poll_id}")
        for option in poll.options:
            await conn.execute(
                "INSERT INTO poll_options (poll_id, option) VALUES ($1, $2)",
                poll_id, option
            )
            logger.debug(f"Inserted poll option: {option}")
    logger.info("Poll creation successful.")
    return {"message": "Poll created successfully", "poll_id": poll_id}

@app.get("/poll")
@log_event("LIST_POLLS")
async def list_polls():
    logger.info("Listing all polls.")
    async with Database.get_connection() as conn:
        polls = await conn.fetch("SELECT id, question FROM polls")
    logger.debug(f"Retrieved {len(polls)} polls from database.")
    return [{"id": p["id"], "question": p["question"]} for p in polls]

@app.get("/vote/{poll_id}")
@log_event("GET_POLL")
async def get_poll(poll_id: int):
    logger.info(f"Fetching poll with ID: {poll_id}")
    async with Database.get_connection() as conn:
        poll = await conn.fetchrow("SELECT id, question FROM polls WHERE id = $1", poll_id)
        if not poll:
            logger.warning(f"Poll with ID {poll_id} not found.")
            raise HTTPException(status_code=404, detail="Poll not found")
        options = await conn.fetch(
            "SELECT id, option FROM poll_options WHERE poll_id = $1", poll_id
        )
    logger.debug(f"Poll {poll_id} has {len(options)} options.")
    return {
        "poll_id": poll["id"],
        "question": poll["question"],
        "options": [{"id": opt["id"], "option": opt["option"]} for opt in options],
    }

@app.post("/vote/{poll_id}")
@log_event("CAST_VOTE")
async def cast_vote(poll_id: int, vote: Vote):
    logger.info(f"Casting vote for poll {poll_id}.")
    async with Database.get_connection() as conn:
        poll = await conn.fetchrow("SELECT id FROM polls WHERE id = $1", poll_id)
        if not poll:
            logger.warning(f"Tried to vote on non-existent poll {poll_id}.")
            raise HTTPException(status_code=404, detail="Poll not found")
        await conn.execute(
            "INSERT INTO votes (poll_id, option) VALUES ($1, $2)", poll_id, vote.option
        )
    logger.info("Vote cast successfully.")
    return {"message": "Vote cast successfully"}

@app.get("/result/{poll_id}")
@log_event("GET_RESULTS")
async def get_result(poll_id: int):
    logger.info(f"Fetching results for poll {poll_id}.")
    async with Database.get_connection() as conn:
        poll = await conn.fetchrow("SELECT id, question FROM polls WHERE id = $1", poll_id)
        if not poll:
            logger.warning(f"Tried to get results for non-existent poll {poll_id}.")
            raise HTTPException(status_code=404, detail="Poll not found")
        options = await conn.fetch("SELECT option FROM poll_options WHERE poll_id = $1", poll_id)
        vote_counts = {opt["option"]: 0 for opt in options}
        votes = await conn.fetch(
            "SELECT option, COUNT(option) as count FROM votes WHERE poll_id = $1 GROUP BY option",
            poll_id
        )
        for v in votes:
            vote_counts[v["option"]] = v["count"]
    logger.debug(f"Results for poll {poll_id}: {vote_counts}")
    return {"poll_id": poll["id"], "question": poll["question"], "results": vote_counts}

@app.get("/results")
@log_event("GET_ALL_RESULTS")
async def get_all_results():
    logger.info("Fetching results for all polls.")
    async with Database.get_connection() as conn:
        polls = await conn.fetch("SELECT id, question FROM polls")
        all_results = []
        for poll in polls:
            options = await conn.fetch("SELECT option FROM poll_options WHERE poll_id = $1", poll["id"])
            vote_counts = {opt["option"]: 0 for opt in options}
            votes = await conn.fetch(
                "SELECT option, COUNT(option) as count FROM votes WHERE poll_id = $1 GROUP BY option",
                poll["id"]
            )
            for v in votes:
                vote_counts[v["option"]] = v["count"]
            all_results.append(
                {
                    "poll_id": poll["id"],
                    "question": poll["question"],
                    "results": vote_counts,
                }
            )
    logger.debug("All results fetched successfully.")
    return all_results
