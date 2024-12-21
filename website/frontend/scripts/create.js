const API_BASE_URL = process.env.API_BASE_URL;

const form = document.getElementById("create-poll-form");
const optionsContainer = document.getElementById("options-container");
const addOptionButton = document.getElementById("add-option");

addOptionButton.addEventListener("click", () => {
    const input = document.createElement("input");
    input.type = "text";
    input.className = "option";
    input.placeholder = `Option ${optionsContainer.children.length + 1}`;
    input.required = true;
    optionsContainer.appendChild(input);
});

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const question = document.getElementById("question").value;
    const options = Array.from(document.querySelectorAll(".option")).map(input => input.value);

    await fetch(`${API_BASE_URL}/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, options })
    });

    alert("Poll created!");
    window.location.href = "index.html";
});
