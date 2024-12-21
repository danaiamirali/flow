const params = new URLSearchParams(window.location.search);
const pollId = params.get("poll_id");

async function fetchResults() {
    const response = await fetch(`${API_BASE_URL}/result/${pollId}`);
    const result = await response.json();

    document.getElementById("poll-question").textContent = result.question;

    const resultsDiv = document.getElementById("results");
    for (const [option, count] of Object.entries(result.results)) {
        const p = document.createElement("p");
        p.textContent = `${option}: ${count} votes`;
        resultsDiv.appendChild(p);
    }
}
fetchResults();

