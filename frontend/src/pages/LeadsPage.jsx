import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiGet, apiPost } from "../api.js";

const STATUS_LABELS = {
  new: "Новый",
  in_progress: "В работе",
  closed: "Закрыт",
  auto_closed: "Авто‑закрыт",
};

const ACTIVE_STATUSES = ["new", "in_progress"];
const CLOSED_STATUSES = ["closed", "auto_closed"];

export default function LeadsPage() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState("active"); // active | closed | all
  const [selectedStatuses, setSelectedStatuses] = useState(ACTIVE_STATUSES);
  const [selectedPriorities, setSelectedPriorities] = useState([]);
  const [channelFilter, setChannelFilter] = useState("all"); // all | telegram | email | portal
  const [search, setSearch] = useState("");
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadTickets({ silent: false });
  }, []);

  useEffect(() => {
    const id = setInterval(() => {
      loadTickets({ silent: true });
    }, 5000);
    return () => clearInterval(id);
  }, []);

  async function loadTickets({ silent } = { silent: false }) {
    if (!silent) {
      setLoading(true);
    }
    try {
      const data = await apiGet(`/tickets`);
      setTickets(data);
    } catch (e) {
      console.error(e);
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }

  function applyView(mode) {
    setViewMode(mode);
    if (mode === "active") {
      setSelectedStatuses(ACTIVE_STATUSES);
    } else if (mode === "closed") {
      setSelectedStatuses(CLOSED_STATUSES);
    } else {
      setSelectedStatuses([...ACTIVE_STATUSES, ...CLOSED_STATUSES]);
    }
  }

  function toggleStatus(status) {
    setSelectedStatuses((prev) =>
      prev.includes(status) ? prev.filter((s) => s !== status) : [...prev, status],
    );
  }

  function togglePriority(priority) {
    setSelectedPriorities((prev) =>
      prev.includes(priority) ? prev.filter((p) => p !== priority) : [...prev, priority],
    );
  }

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return tickets.filter((t) => {
      if (selectedStatuses.length && !selectedStatuses.includes(t.status)) return false;
      if (selectedPriorities.length && !selectedPriorities.includes(t.priority)) return false;
      if (channelFilter !== "all" && t.channel !== channelFilter) return false;
      if (!q) return true;
      const haystack = `${t.subject || ""} ${t.customer_email || ""} ${
        t.customer_username || ""
      }`.toLowerCase();
      return haystack.includes(q);
    });
  }, [tickets, search, selectedStatuses, selectedPriorities, channelFilter]);

  async function handleCreate(e) {
    e.preventDefault();
    if (creating) return;
    const form = e.currentTarget;
    const formData = new FormData(form);
    const payload = {
      subject: formData.get("subject"),
      description: formData.get("description"),
      channel: "portal",
      language: formData.get("language"),
      customer_email: formData.get("customer_email") || null,
      customer_username: formData.get("customer_username") || null,
    };
    setCreating(true);
    try {
      await apiPost("/tickets", payload);
      form.reset();
      await loadTickets();
    } catch (err) {
      console.error(err);
      alert("Ошибка при создании лида");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Обращения</h1>
          <p className="page-header__subtitle">
            Управление входящими обращениями из Telegram, почты и портала.
          </p>
        </div>
        <button
          className="btn btn--primary"
          onClick={() => {
            const el = document.getElementById("leadForm");
            if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
          }}
        >
          Создать лида
        </button>
      </div>

      <section className="panel">
        <div className="filters-tabs">
          <button
            type="button"
            className={`btn btn--ghost filters-tab${
              viewMode === "active" ? " filters-tab--active" : ""
            }`}
            onClick={() => applyView("active")}
          >
            Активные
          </button>
          <button
            type="button"
            className={`btn btn--ghost filters-tab${
              viewMode === "closed" ? " filters-tab--active" : ""
            }`}
            onClick={() => applyView("closed")}
          >
            Закрытые
          </button>
          <button
            type="button"
            className={`btn btn--ghost filters-tab${
              viewMode === "all" ? " filters-tab--active" : ""
            }`}
            onClick={() => applyView("all")}
          >
            Все
          </button>
        </div>
        <div className="filters">
          <div className="filters__item">
            <label className="label">
              Поиск (email / тема)
              <input
                type="text"
                placeholder="example@company.com"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </label>
          </div>
          <div className="filters__item">
            <div className="label">
              Статусы
              <div className="filters__checkbox-row">
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={selectedStatuses.includes("new")}
                    onChange={() => toggleStatus("new")}
                  />
                  Новый
                </label>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={selectedStatuses.includes("in_progress")}
                    onChange={() => toggleStatus("in_progress")}
                  />
                  В работе
                </label>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={selectedStatuses.includes("closed")}
                    onChange={() => toggleStatus("closed")}
                  />
                  Закрыт
                </label>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={selectedStatuses.includes("auto_closed")}
                    onChange={() => toggleStatus("auto_closed")}
                  />
                  Авто‑закрыт
                </label>
              </div>
            </div>
          </div>
          <div className="filters__item">
            <div className="label">
              Приоритеты
              <div className="filters__checkbox-row">
                {["P1", "P2", "P3", "P4"].map((p) => (
                  <label key={p} className="checkbox">
                    <input
                      type="checkbox"
                      checked={selectedPriorities.includes(p)}
                      onChange={() => togglePriority(p)}
                    />
                    {p}
                  </label>
                ))}
              </div>
            </div>
          </div>
          <div className="filters__item">
            <label className="label">
              Источник
              <select
                value={channelFilter}
                onChange={(e) => setChannelFilter(e.target.value)}
              >
                <option value="all">Все</option>
                <option value="telegram">Telegram</option>
                <option value="email">Email</option>
                <option value="portal">Портал</option>
              </select>
            </label>
          </div>
        </div>
      </section>

      <section className="panel">
        <h2 className="panel__title">Список лидов</h2>
        <div className="table-wrapper">
          <table className="table leads-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Email</th>
                <th>Username</th>
                <th>Тема</th>
                <th>Источник</th>
                <th>Приоритет</th>
                <th>Статус</th>
                <th>Создан</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9}>
                    <div className="table__empty">Загрузка...</div>
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={9}>
                    <div className="table__empty">Лидов пока нет</div>
                  </td>
                </tr>
              ) : (
                filtered.map((t) => (
                  <tr key={t.id} className="table__row">
                    <td>{t.id}</td>
                    <td>{t.customer_email || "—"}</td>
                    <td>{t.customer_username || "—"}</td>
                    <td className="table__cell--main">{t.subject}</td>
                    <td>{t.channel}</td>
                    <td>
                      <span className={`tag tag--priority-${t.priority.toLowerCase()}`}>
                        {t.priority}
                      </span>
                    </td>
                    <td>
                      <span className={`tag tag--status-${t.status}`}>
                        {STATUS_LABELS[t.status] || t.status}
                      </span>
                    </td>
                    <td>{new Date(t.created_at).toLocaleString()}</td>
                    <td>
                      <button
                        className="btn btn--ghost"
                        onClick={() => navigate(`/tickets/${t.id}`)}
                      >
                        Открыть
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel" id="leadForm">
        <h2 className="panel__title">Создать лида вручную</h2>
        <form className="form" onSubmit={handleCreate}>
          <label className="label">
            Тема
            <input type="text" name="subject" required />
          </label>
          <label className="label">
            Email
            <input type="email" name="customer_email" placeholder="user@example.com" />
          </label>
          <label className="label">
            Username (Telegram)
            <input type="text" name="customer_username" placeholder="@username" />
          </label>
          <label className="label">
            Описание
            <textarea name="description" rows={3} required />
          </label>
          <label className="label">
            Язык
            <select name="language" defaultValue="ru">
              <option value="ru">Русский</option>
              <option value="kk">Казахский</option>
            </select>
          </label>
          <button className="btn btn--primary" type="submit" disabled={creating}>
            {creating ? "Создание..." : "Создать"}
          </button>
        </form>
      </section>
    </div>
  );
}
