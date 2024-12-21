from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from database import Database, execute_sql_file

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://0.0.0.0:8080", "http://localhost:8080", 
                   "https://flow-gamma-kohl.vercel.app",
                   "https://flow-f2pe4skl5-danaiamiralis-projects.vercel.app"
                   ],  # Add frontend's origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize the connection pool
@app.on_event("startup")
async def startup():
    await Database.init_pool()
    await execute_sql_file("sql/initialize_tables.sql")

# Pydantic Models
class PollCreate(BaseModel):
    question: str
    options: List[str]  # Add a list of options

class Vote(BaseModel):
    option: str

# Routes
@app.post("/create")
async def create_poll(poll: PollCreate):
    async with Database.get_connection() as conn:
        # Insert the poll question
        poll_id = await conn.fetchval(
            "INSERT INTO polls (question) VALUES ($1) RETURNING id", poll.question
        )

        # Insert each option into poll_options
        for option in poll.options:
            await conn.execute(
                "INSERT INTO poll_options (poll_id, option) VALUES ($1, $2)", poll_id, option
            )

        return {"message": "Poll created successfully", "poll_id": poll_id}

@app.get("/poll")
async def list_polls():
    async with Database.get_connection() as conn:
        polls = await conn.fetch("SELECT id, question FROM polls")
        return [{"id": p["id"], "question": p["question"]} for p in polls]

@app.get("/vote/{poll_id}")
async def get_poll(poll_id: int):
    async with Database.get_connection() as conn:
        poll = await conn.fetchrow("SELECT id, question FROM polls WHERE id = $1", poll_id)
        if not poll:
            raise HTTPException(status_code=404, detail="Poll not found")

        options = await conn.fetch(
            "SELECT id, option FROM poll_options WHERE poll_id = $1", poll_id
        )
        return {
            "poll_id": poll["id"],
            "question": poll["question"],
            "options": [{"id": opt["id"], "option": opt["option"]} for opt in options],
        }

@app.post("/vote/{poll_id}")
async def cast_vote(poll_id: int, vote: Vote):
    async with Database.get_connection() as conn:
        poll = await conn.fetchrow("SELECT id FROM polls WHERE id = $1", poll_id)
        if not poll:
            raise HTTPException(status_code=404, detail="Poll not found")

        await conn.execute(
            "INSERT INTO votes (poll_id, option) VALUES ($1, $2)", poll_id, vote.option
        )
        return {"message": "Vote cast successfully"}

@app.get("/result/{poll_id}")
async def get_result(poll_id: int):
    async with Database.get_connection() as conn:
        poll = await conn.fetchrow("SELECT id, question FROM polls WHERE id = $1", poll_id)
        if not poll:
            raise HTTPException(status_code=404, detail="Poll not found")

        options = await conn.fetch(
            "SELECT option FROM poll_options WHERE poll_id = $1", poll_id
        )
        vote_counts = {opt["option"]: 0 for opt in options}

        votes = await conn.fetch(
            "SELECT option, COUNT(option) as count FROM votes WHERE poll_id = $1 GROUP BY option",
            poll_id,
        )
        for vote in votes:
            vote_counts[vote["option"]] = vote["count"]

        return {"poll_id": poll["id"], "question": poll["question"], "results": vote_counts}

@app.get("/results")
async def get_all_results():
    async with Database.get_connection() as conn:
        polls = await conn.fetch("SELECT id, question FROM polls")
        all_results = []

        for poll in polls:
            options = await conn.fetch(
                "SELECT option FROM poll_options WHERE poll_id = $1", poll["id"]
            )
            vote_counts = {opt["option"]: 0 for opt in options}

            votes = await conn.fetch(
                "SELECT option, COUNT(option) as count FROM votes WHERE poll_id = $1 GROUP BY option",
                poll["id"],
            )
            for vote in votes:
                vote_counts[vote["option"]] = vote["count"]

            all_results.append(
                {
                    "poll_id": poll["id"],
                    "question": poll["question"],
                    "results": vote_counts,
                }
            )

        return all_results
