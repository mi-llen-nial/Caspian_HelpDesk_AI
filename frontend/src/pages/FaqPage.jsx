import React, { useEffect, useState } from "react";
import { apiDelete, apiGet, apiPost, apiPut } from "../api.js";

export default function FaqPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
   const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({
    question: "",
    answer: "",
    language: "ru",
    category_code: "",
    auto_resolvable: false,
  });

  useEffect(() => {
    loadFaq();
  }, []);

  async function loadFaq() {
    setLoading(true);
    try {
      const data = await apiGet("/faq");
      setItems(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  function startEdit(item) {
    setEditingId(item.id);
    setForm({
      question: item.question,
      answer: item.answer,
      language: item.language,
      category_code: item.category_code || "",
      auto_resolvable: item.auto_resolvable,
    });
  }

  function resetForm() {
    setEditingId(null);
    setForm({
      question: "",
      answer: "",
      language: "ru",
      category_code: "",
      auto_resolvable: false,
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (creating) return;
    const payload = {
      question: form.question,
      answer: form.answer,
      language: form.language,
      category_code: form.category_code || null,
      auto_resolvable: form.auto_resolvable,
    };
    setCreating(true);
    try {
      if (editingId != null) {
        await apiPut(`/faq/${editingId}`, payload);
      } else {
        await apiPost("/faq", payload);
      }
      resetForm();
      await loadFaq();
    } catch (e) {
      console.error(e);
      alert("Ошибка при сохранении статьи");
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm("Удалить статью базы знаний?")) return;
    try {
      await apiDelete(`/faq/${id}`);
      if (editingId === id) {
        resetForm();
      }
      await loadFaq();
    } catch (e) {
      console.error(e);
      alert("Ошибка при удалении статьи");
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>База знаний</h1>
          <p className="page-header__subtitle">
            Статьи и ответы, которые использует ИИ для авто‑решения обращений.
          </p>
        </div>
      </div>

      <section className="panel">
        <h2 className="panel__title">
          {editingId != null ? `Редактирование статьи #${editingId}` : "Новая статья"}
        </h2>
        <form className="form" onSubmit={handleSubmit}>
          <label className="label">
            Вопрос
            <input
              type="text"
              name="question"
              required
              value={form.question}
              onChange={(e) => setForm((f) => ({ ...f, question: e.target.value }))}
            />
          </label>
          <label className="label">
            Ответ
            <textarea
              name="answer"
              rows={3}
              required
              value={form.answer}
              onChange={(e) => setForm((f) => ({ ...f, answer: e.target.value }))}
            />
          </label>
          <label className="label">
            Язык
            <select
              name="language"
              value={form.language}
              onChange={(e) => setForm((f) => ({ ...f, language: e.target.value }))}
            >
              <option value="ru">Русский</option>
              <option value="kk">Казахский</option>
            </select>
          </label>
          <label className="label">
            Код категории
            <input
              type="text"
              name="category_code"
              placeholder="Например ACCESS_VPN"
              value={form.category_code}
              onChange={(e) => setForm((f) => ({ ...f, category_code: e.target.value }))}
            />
          </label>
          <label className="checkbox">
            <input
              type="checkbox"
              name="auto_resolvable"
              checked={form.auto_resolvable}
              onChange={(e) =>
                setForm((f) => ({ ...f, auto_resolvable: e.target.checked }))
              }
            />{" "}
            Можно использовать для авто‑закрытия
          </label>
          <button className="btn btn--primary" type="submit" disabled={creating}>
            {creating
              ? "Сохранение..."
              : editingId != null
              ? "Обновить статью"
              : "Сохранить"}
          </button>
          {editingId != null && (
            <button
              type="button"
              className="btn btn--ghost"
              onClick={resetForm}
              style={{ marginLeft: "0.5rem" }}
            >
              Отменить редактирование
            </button>
          )}
        </form>
      </section>

      <section className="panel">
        <h2 className="panel__title">Статьи</h2>
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Вопрос</th>
                <th>Язык</th>
                <th>Категория</th>
                <th>Авто‑решение</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5}>
                    <div className="table__empty">Загрузка...</div>
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={5}>
                    <div className="table__empty">Статей пока нет</div>
                  </td>
                </tr>
              ) : (
                items.map((f) => (
                  <tr key={f.id}>
                    <td>{f.id}</td>
                    <td className="table__cell--main">{f.question}</td>
                    <td>{f.language}</td>
                    <td>{f.category_code || "—"}</td>
                    <td>{f.auto_resolvable ? "Да" : "Нет"}</td>
                    <td>
                      <button
                        type="button"
                        className="btn btn--ghost"
                        onClick={() => startEdit(f)}
                      >
                        Редактировать
                      </button>
                      <button
                        type="button"
                        className="btn btn--danger"
                        onClick={() => handleDelete(f.id)}
                      >
                        Удалить
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
