function getTicketIdFromQuery() {
  const params = new URLSearchParams(window.location.search);
  return params.get("id");
}

function renderMessages(messages) {
  const container = document.getElementById("messages");
  container.innerHTML = "";
  for (const m of messages) {
    const div = document.createElement("div");
    const cls =
      m.author_type === "customer"
        ? "message--customer"
        : m.author_type === "ai"
        ? "message--ai"
        : "message--agent";
    div.className = `message ${cls}`;
    const meta = document.createElement("div");
    meta.className = "message__meta";
    meta.textContent = `${m.author_type} • ${new Date(m.created_at).toLocaleString()}`;
    const body = document.createElement("div");
    body.textContent = m.body;
    div.appendChild(meta);
    div.appendChild(body);
    container.appendChild(div);
  }
}

async function loadTicket() {
  const id = getTicketIdFromQuery();
  if (!id) return;
  try {
    const ticket = await apiGet(`/tickets/${id}`);
    document.getElementById("ticketSubject").textContent = `#${ticket.id} · ${ticket.subject}`;
    document.getElementById(
      "ticketMeta",
    ).textContent = `Статус: ${ticket.status} • Приоритет: ${ticket.priority} • Источник: ${
      ticket.channel
    } • Email: ${ticket.customer_email || "—"} • Username: ${
      ticket.customer_username || "—"
    } • Департамент: ${ticket.department_name || "—"} • Категория: ${ticket.category_code || "—"}`;

    renderMessages(ticket.messages);

    document.getElementById("aiCategory").textContent = `Категория: ${ticket.category_code || "—"}`;
    document.getElementById("aiDepartment").textContent = `Департамент: ${
      ticket.department_name || "—"
    }`;
    document.getElementById("aiPriority").textContent = `Приоритет: ${ticket.priority}`;
    document.getElementById("aiStatus").textContent = `Статус: ${ticket.status}`;
  } catch (err) {
    console.error(err);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const ticketId = getTicketIdFromQuery();
  if (!ticketId) {
    alert("Не указан id тикета в параметрах URL");
    return;
  }
  loadTicket();

  const form = document.getElementById("replyForm");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const payload = {
      body: formData.get("body"),
      author_type: "agent",
      language: "ru",
    };
    try {
      await apiPost(`/tickets/${ticketId}/messages`, payload);
      form.reset();
      loadTicket();
    } catch (err) {
      console.error(err);
      alert("Ошибка при отправке ответа");
    }
  });
});
