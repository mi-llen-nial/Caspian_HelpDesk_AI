async function loadFaq() {
  const tbody = document.querySelector("#faqTable tbody");
  tbody.innerHTML = "";
  try {
    const items = await apiGet("/faq");
    for (const f of items) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${f.id}</td>
        <td>${f.question}</td>
        <td>${f.language}</td>
        <td>${f.category_code || "—"}</td>
        <td>${f.auto_resolvable ? "Да" : "Нет"}</td>
      `;
      tbody.appendChild(tr);
    }
  } catch (err) {
    console.error(err);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadFaq();

  const form = document.getElementById("faqForm");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const payload = {
      question: formData.get("question"),
      answer: formData.get("answer"),
      language: formData.get("language"),
      category_code: formData.get("category_code") || null,
      auto_resolvable: formData.get("auto_resolvable") === "on",
    };
    try {
      await apiPost("/faq", payload);
      form.reset();
      loadFaq();
    } catch (err) {
      console.error(err);
      alert("Ошибка при сохранении статьи");
    }
  });
});

