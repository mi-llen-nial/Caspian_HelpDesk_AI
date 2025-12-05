import React, { useEffect, useState } from "react";
import { apiDelete, apiGet, apiPost, apiPut } from "../api.js";

const MAIN_CATEGORY_LABELS = {
  problem: "Что‑то не работает",
  question: "Есть вопрос",
  feedback: "Предложение или отзыв",
  career: "Работа и стажировки",
  partner: "Партнёрство и сотрудничество",
  other: "Другое",
};

function splitCategoryCode(code) {
  if (!code) return { main: "", sub: "" };
  const [maybeMain, maybeSub] = code.split(":", 2);
  if (maybeSub) {
    return { main: maybeMain, sub: maybeSub };
  }
  return { main: "", sub: maybeMain };
}

export default function FaqPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({
    question: "",
    answer: "",
    language: "ru",
    auto_resolvable: false,
  });
  const [mainCategory, setMainCategory] = useState("");
  const [subCategory, setSubCategory] = useState("");

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
    const { main, sub } = splitCategoryCode(item.category_code || "");
    setForm({
      question: item.question,
      answer: item.answer,
      language: item.language,
      auto_resolvable: item.auto_resolvable,
    });
    setMainCategory(main);
    setSubCategory(sub);
  }

  function resetForm() {
    setEditingId(null);
    setForm({
      question: "",
      answer: "",
      language: "ru",
      auto_resolvable: false,
    });
    setMainCategory("");
    setSubCategory("");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (creating) return;
    let category_code = null;
    if (subCategory.trim()) {
      category_code = mainCategory ? `${mainCategory}:${subCategory.trim()}` : subCategory.trim();
    }

    const payload = {
      question: form.question,
      answer: form.answer,
      language: form.language,
      category_code,
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
          <h1>Шаблоны ответов</h1>
          <p className="page-header__subtitle">
            Готовые ответы по категориям, которые бот использует вместо генерации, когда есть подходящий шаблон.
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
            Язык ответа
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
            Основная категория
            <select
              value={mainCategory}
              onChange={(e) => setMainCategory(e.target.value)}
            >
              <option value="">Не указана</option>
              {Object.entries(MAIN_CATEGORY_LABELS).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label className="label">
            Код подкатегории
            <input
              type="text"
              name="subcategory_code"
              placeholder="Например CONNECTION_WIFI, INTERNET_HOME"
              value={subCategory}
              onChange={(e) => setSubCategory(e.target.value)}
            />
            <span style={{ fontSize: "0.75rem", color: "#6b7280" }}>
              Используйте машиночитаемые коды: CONNECTION_WIFI, CONNECTION_TV, BILLING_TARIFF и т.п.
            </span>
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
        <h2 className="panel__title">Шаблоны</h2>
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Вопрос</th>
                <th>Язык</th>
                <th>Категория</th>
                <th>Подкатегория</th>
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
                    <td>{splitCategoryCode(f.category_code || "").main ? MAIN_CATEGORY_LABELS[splitCategoryCode(f.category_code || "").main] || splitCategoryCode(f.category_code || "").main : "—"}</td>
                    <td>{splitCategoryCode(f.category_code || "").sub || "—"}</td>
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
