import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiGet, apiPost, apiPut } from "../api.js";

const STATUS_OPTIONS = [
  { value: "new", label: "Новый" },
  { value: "in_progress", label: "В работе" },
  { value: "closed", label: "Закрыт" },
  { value: "auto_closed", label: "Авто‑закрыт" },
];

export default function TicketDetailsPage() {
  const { id } = useParams();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);
  const [statusUpdating, setStatusUpdating] = useState(false);
  const [summary, setSummary] = useState("");
  const [summaryLoading, setSummaryLoading] = useState(false);

  useEffect(() => {
    loadTicket({ silent: false });
    loadSummary();
  }, [id]);

  useEffect(() => {
    const intervalId = setInterval(() => {
      loadTicket({ silent: true });
    }, 4000);
    return () => clearInterval(intervalId);
  }, [id]);

  async function loadTicket({ silent } = { silent: false }) {
    if (!silent) {
      setLoading(true);
    }
    try {
      const data = await apiGet(`/tickets/${id}`);
      setTicket(data);
    } catch (e) {
      console.error(e);
    } finally {
      if (!silent) {
        setLoading(false);
      }
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

  async function loadSummary() {
    setSummaryLoading(true);
    try {
      const data = await apiGet(`/tickets/${id}/summary`);
      setSummary(data.summary);
    } catch (e) {
      console.error(e);
    } finally {
      setSummaryLoading(false);
    }
  }

  async function handleStatusChange(e) {
    const next = e.target.value;
    if (!ticket || next === ticket.status) return;
    setStatusUpdating(true);
    try {
      const updated = await apiPut(`/tickets/${id}/status`, { status: next });
      setTicket((prev) => ({ ...prev, ...updated }));
    } catch (err) {
      console.error(err);
      alert("Не удалось изменить статус");
    } finally {
      setStatusUpdating(false);
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
          Статус:{" "}
          <select
            value={ticket.status}
            onChange={handleStatusChange}
            disabled={statusUpdating}
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>{" "}
          • Приоритет: <strong>{ticket.priority}</strong> • Источник:{" "}
          <strong>{ticket.channel}</strong> • Email:{" "}
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
          {summaryLoading ? (
            <p className="placeholder">Генерируем резюме обращения...</p>
          ) : summary ? (
            <p>{summary}</p>
          ) : (
            <p className="placeholder">
              Нажмите «Обновить резюме», чтобы получить краткое описание проблемы пользователя.
            </p>
          )}
          <button
            type="button"
            className="btn btn--ghost"
            style={{ marginTop: "0.5rem" }}
            onClick={loadSummary}
            disabled={summaryLoading}
          >
            {summaryLoading ? "Обновление..." : "Обновить резюме"}
          </button>
        </div>
      </aside>
    </div>
  );
}
