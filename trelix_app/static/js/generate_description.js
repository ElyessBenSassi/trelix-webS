document.addEventListener("DOMContentLoaded", function () {
    const titleField = document.querySelector("#id_titre");
    const descriptionField = document.querySelector("#id_description");

    if (!titleField || !descriptionField) return;

    const btn = document.createElement("button");
    btn.type = "button";
    btn.innerText = "✨ Générer Description IA";
    btn.style = "margin-top:8px; margin-left:10px;";

    titleField.parentNode.appendChild(btn);

    btn.addEventListener("click", async () => {
        const title = titleField.value;

        if (!title.trim()) {
            alert("Veuillez entrer un titre d'abord.");
            return;
        }

       const response = await fetch("/evenements/generate-description/", {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
    },
    body: JSON.stringify({ title })
});

        const data = await response.json();
        descriptionField.value = data.description;
    });
});
