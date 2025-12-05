import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiGet, apiPost } from "../api.js";

export default function TicketDetailsPage() {
  const { id } = useParams();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    loadTicket();
  }, [id]);

  useEffect(() => {
    const intervalId = setInterval(() => {
      loadTicket();
    }, 4000);
    return () => clearInterval(intervalId);
  }, [id]);

  async function loadTicket() {
    setLoading(true);
    try {
      const data = await apiGet(`/tickets/${id}`);
      setTicket(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleReply(e) {
    e.preventDefault();
    if (!reply.trim()) return;
    setSending(true);
    try {
      await apiPost(`/tickets/${id}/messages`, {
        body: reply,
        author_type: "agent",
        language: ticket?.language || "ru",
      });
      setReply("");
      await loadTicket();
    } catch (e) {
      console.error(e);
      alert("Ошибка при отправке ответа");
    } finally {
      setSending(false);
    }
  }

  if (loading || !ticket) {
    return (
      <div>
        <h1>Тикет #{id}</h1>
        <div className="panel">Загрузка...</div>
      </div>
    );
  }

  return (
    <div className="ticket-layout">
      <section className="panel panel--main">
        <h1>
          Тикет #{ticket.id} · <span className="ticket__subject">{ticket.subject}</span>
        </h1>
        <div className="ticket-meta">
          Статус: <strong>{ticket.status}</strong> • Приоритет:{" "}
          <strong>{ticket.priority}</strong> • Источник: <strong>{ticket.channel}</strong> • Email:{" "}
          <strong>{ticket.customer_email || "—"}</strong> • Username:{" "}
          <strong>{ticket.customer_username || "—"}</strong>
        </div>

        <div className="messages">
          {ticket.messages.map((m) => (
            <div
              key={m.id}
              className={`message message--${m.author_type === "customer" ? "customer" : m.author_type === "ai" ? "ai" : "agent"}`}
            >
              <div className="message__meta">
                {m.author_type} • {new Date(m.created_at).toLocaleString()}
              </div>
              <div>{m.body}</div>
            </div>
          ))}
        </div>

        <form className="form form--inline" onSubmit={handleReply}>
          <textarea
            rows={3}
            placeholder="Напишите ответ пользователю..."
            value={reply}
            onChange={(e) => setReply(e.target.value)}
          />
          <button className="btn btn--primary" type="submit" disabled={sending}>
            {sending ? "Отправка..." : "Отправить"}
          </button>
        </form>
      </section>

      <aside className="panel panel--sidebar">
        <h2>AI‑панель</h2>
        <div className="ai-block">
          <h3>Классификация</h3>
          <p>Категория: {ticket.category_code || "—"}</p>
          <p>Департамент: {ticket.department_name || "—"}</p>
          <p>Приоритет: {ticket.priority}</p>
          <p>Статус: {ticket.status}</p>
        </div>
        <div className="ai-block">
          <h3>Резюме</h3>
          <p className="placeholder">
            Здесь можно вывести краткое резюме обращения (эндпоинт ещё не реализован).
          </p>
        </div>
      </aside>
    </div>
  );
}
