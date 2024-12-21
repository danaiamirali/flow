const API_BASE_URL = process.env.API_BASE_URL;

const params = new URLSearchParams(window.location.search);
const pollId = params.get("poll_id");

async function fetchPoll() {
    const response = await fetch(`${API_BASE_URL}/vote/${pollId}`);
    const poll = await response.json();

    document.getElementById("poll-question").textContent = poll.question;

    const optionsDiv = document.getElementById("options");
    poll.options.forEach(option => {
        const button = document.createElement("button");
        button.textContent = option.option;
        button.onclick = async () => {
            await fetch(`${API_BASE_URL}/vote/${pollId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ option: option.option })
            });
            alert("Vote cast!");
            window.location.href = `result.html?poll_id=${pollId}`;
        };
        optionsDiv.appendChild(button);
    });
}
fetchPoll();
