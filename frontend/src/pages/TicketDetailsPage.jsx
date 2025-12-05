import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiGet, apiPost, apiPut } from "../api.js";

const STATUS_OPTIONS = [
  { value: "new", label: "Новый" },
  { value: "in_progress", label: "В работе" },
  { value: "closed", label: "Закрыт" },
  { value: "auto_closed", label: "Авто‑закрыт" },
];

const PRIORITY_OPTIONS = [
  { value: "P1", label: "P1" },
  { value: "P2", label: "P2" },
  { value: "P3", label: "P3" },
  { value: "P4", label: "P4" },
];

const REQUEST_TYPE_OPTIONS = [
  { value: "", label: "Не указана" },
  { value: "problem", label: "Что‑то не работает" },
  { value: "question", label: "Есть вопрос" },
  { value: "feedback", label: "Предложение или отзыв" },
  { value: "career", label: "Работа и стажировки" },
  { value: "partner", label: "Партнёрство и сотрудничество" },
  { value: "other", label: "Другое" },
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
  const [replySuggestions, setReplySuggestions] = useState([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);

  useEffect(() => {
    loadTicket({ silent: false });
    loadSummary();
    loadReplySuggestions();
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

  async function loadReplySuggestions() {
    setSuggestionsLoading(true);
    try {
      const data = await apiGet(`/tickets/${id}/reply_suggestions`);
      setReplySuggestions(data.suggestions || []);
    } catch (e) {
      console.error(e);
    } finally {
      setSuggestionsLoading(false);
    }
  }

  async function updateTicketMeta(patch) {
    if (!ticket) return;
    setStatusUpdating(true);
    try {
      const payload = {
        status: patch.status ?? ticket.status,
        priority: patch.priority ?? ticket.priority,
        request_type:
          patch.request_type !== undefined ? patch.request_type : ticket.request_type,
        ai_disabled:
          patch.ai_disabled !== undefined ? patch.ai_disabled : ticket.ai_disabled,
      };
      const updated = await apiPut(`/tickets/${id}/status`, payload);
      setTicket((prev) => ({ ...prev, ...updated }));
    } catch (err) {
      console.error(err);
      alert("Не удалось обновить параметры тикета");
    } finally {
      setStatusUpdating(false);
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
    await updateTicketMeta({ status: next });
  }

  async function handlePriorityChange(e) {
    const next = e.target.value;
    if (!ticket || next === ticket.priority) return;
    await updateTicketMeta({ priority: next });
  }

  async function handleRequestTypeChange(e) {
    const next = e.target.value || null;
    if (!ticket || next === (ticket.request_type || null)) return;
    await updateTicketMeta({ request_type: next });
  }

  async function handleToggleAi(e) {
    const next = e.target.checked;
    if (!ticket || next === ticket.ai_disabled) return;
    await updateTicketMeta({ ai_disabled: next });
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
          <div className="ticket-meta__row ticket-meta__row--controls">
            <div className="ticket-meta__group">
              <span className="ticket-meta__label">Статус</span>
              <select
                value={ticket.status}
                onChange={handleStatusChange}
                disabled={statusUpdating}
                className="ticket-meta__select"
              >
                {STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="ticket-meta__group">
              <span className="ticket-meta__label">Приоритет</span>
              <select
                value={ticket.priority}
                onChange={handlePriorityChange}
                disabled={statusUpdating}
                className="ticket-meta__select"
              >
                {PRIORITY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="ticket-meta__group ticket-meta__group--wide">
              <span className="ticket-meta__label">Категория</span>
              <select
                value={ticket.request_type || ""}
                onChange={handleRequestTypeChange}
                disabled={statusUpdating}
                className="ticket-meta__select"
              >
                {REQUEST_TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="ticket-meta__row">
            <span>
              Источник: <strong>{ticket.channel}</strong>
            </span>
            <span>
              Email: <strong>{ticket.customer_email || "—"}</strong>
            </span>
            <span>
              Username: <strong>{ticket.customer_username || "—"}</strong>
            </span>
          </div>
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

        <div className="quick-replies">
          <div className="quick-replies__header">
            <span className="quick-replies__title">Готовые ответы</span>
            <button
              type="button"
              className="btn btn--ghost quick-replies__refresh"
              onClick={loadReplySuggestions}
              disabled={suggestionsLoading}
            >
              {suggestionsLoading ? "Обновление..." : "Обновить варианты"}
            </button>
          </div>
          {suggestionsLoading && !replySuggestions.length ? (
            <div className="quick-replies__empty">
              <span className="skeleton skeleton--text" />
            </div>
          ) : replySuggestions.length === 0 ? (
            <div className="quick-replies__empty">
              Нет готовых вариантов, обновите позже.
            </div>
          ) : (
            <div className="quick-replies__chips">
              {replySuggestions.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="quick-replies__chip"
                  onClick={() => setReply(s)}
                >
                  Вариант {idx + 1}
                </button>
              ))}
            </div>
          )}
        </div>
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
          <h3>Управление ИИ</h3>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={ticket.ai_disabled}
              onChange={handleToggleAi}
              disabled={statusUpdating}
            />{" "}
            Не использовать авто‑ответы ИИ в этом тикете
          </label>
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
