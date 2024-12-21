const API_BASE_URL = process.env.API_BASE_URL;

async function fetchAllResults() {
    const response = await fetch(`${API_BASE_URL}/results`);
    const allResults = await response.json();

    const resultsContainer = document.getElementById("results-container");
    resultsContainer.innerHTML = ""; // Clear any existing content

    allResults.forEach(poll => {
        const pollDiv = document.createElement("div");
        pollDiv.className = "poll-result";

        const question = document.createElement("h3");
        question.textContent = poll.question;

        const resultsList = document.createElement("ul");
        for (const [option, count] of Object.entries(poll.results)) {
            const resultItem = document.createElement("li");
            resultItem.textContent = `${option}: ${count} votes`;
            resultsList.appendChild(resultItem);
        }

        pollDiv.appendChild(question);
        pollDiv.appendChild(resultsList);
        resultsContainer.appendChild(pollDiv);
    });
}

fetchAllResults();

