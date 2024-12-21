import requests

# API base URL
API_BASE_URL = "http://127.0.0.1:8000"

# Poll data to create
poll_data = {
    "question": "What is your favorite programming language?",
    "options": ["Python", "JavaScript", "Java", "C++"]
}

def create_poll():
    """Simulate creating a poll."""
    try:
        response = requests.post(f"{API_BASE_URL}/create", json=poll_data)
        response.raise_for_status()  # Raise an error for HTTP error responses
        poll = response.json()
        print("Poll created successfully!")
        print(f"Poll ID: {poll['poll_id']}")
        return poll['poll_id']
    except requests.exceptions.RequestException as e:
        print("Error creating poll:", e)

if __name__ == "__main__":
    create_poll()

