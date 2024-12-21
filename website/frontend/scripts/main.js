async function fetchPolls() {
    const response = await fetch(`${API_BASE_URL}/poll`);
    const polls = await response.json();
    const pollList = document.getElementById("poll-list");
    polls.forEach(poll => {
        const li = document.createElement("li");
        li.innerHTML = `<a href="vote.html?poll_id=${poll.id}">${poll.question}</a>`;
        pollList.appendChild(li);
    });
}
fetchPolls();

