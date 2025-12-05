let ALL_TICKETS = [];

function renderTickets() {
  const tbody = document.querySelector("#ticketsTable tbody");
  const searchValue = document.getElementById("searchInput").value.trim().toLowerCase();

  tbody.innerHTML = "";

  for (const t of ALL_TICKETS) {
    if (searchValue) {
      const haystack = `${t.subject || ""} ${t.customer_email || ""} ${
        t.customer_username || ""
      }`.toLowerCase();
      if (!haystack.includes(searchValue)) {
        continue;
      }
    }

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${t.id}</td>
      <td>${t.customer_email || "—"}</td>
      <td>${t.customer_username || "—"}</td>
      <td>${t.subject}</td>
      <td>${t.channel}</td>
      <td>${t.priority}</td>
      <td>${t.status}</td>
      <td>${new Date(t.created_at).toLocaleString()}</td>
      <td><a href="/ticket.html?id=${t.id}">Открыть</a></td>
    `;
    tbody.appendChild(tr);
  }
}

async function loadTickets() {
  const status = document.getElementById("statusFilter").value;
  const params = [];
  if (status) params.push(`status=${encodeURIComponent(status)}`);
  const query = params.length ? `?${params.join("&")}` : "";

  try {
    ALL_TICKETS = await apiGet(`/tickets${query}`);
    renderTickets();
  } catch (err) {
    console.error(err);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadTickets();

  const form = document.getElementById("newTicketForm");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const payload = {
      subject: formData.get("subject"),
      description: formData.get("description"),
      channel: "portal",
      language: formData.get("language"),
      customer_email: formData.get("customer_email") || null,
      customer_username: formData.get("customer_username") || null,
    };
    try {
      await apiPost("/tickets", payload);
      form.reset();
      loadTickets();
    } catch (err) {
      console.error(err);
      alert("Ошибка при создании тикета");
    }
  });

  const searchInput = document.getElementById("searchInput");
  searchInput.addEventListener("input", () => {
    renderTickets();
  });

  const statusFilter = document.getElementById("statusFilter");
  statusFilter.addEventListener("change", () => {
    loadTickets();
  });
});
