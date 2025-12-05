import React, { useEffect, useState } from "react";
import { apiGet } from "../api.js";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await apiGet("/analytics/overview");
        if (!cancelled) setMetrics(data);
      } catch (e) {
        console.error(e);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const categoryData =
    metrics == null
      ? []
      : [
          { key: "problem", label: "Что‑то не работает", value: metrics.problem_tickets },
          { key: "question", label: "Есть вопрос", value: metrics.question_tickets },
          { key: "feedback", label: "Предложение или отзыв", value: metrics.feedback_tickets },
          { key: "career", label: "Работа и стажировки", value: metrics.career_tickets },
          {
            key: "partner",
            label: "Партнёрство и сотрудничество",
            value: metrics.partner_tickets,
          },
          { key: "other", label: "Другое", value: metrics.other_tickets },
        ];

  const priorityData =
    metrics == null
      ? []
      : [
          { key: "P1", label: "P1", value: metrics.p1_tickets },
          { key: "P2", label: "P2", value: metrics.p2_tickets },
          { key: "P3", label: "P3", value: metrics.p3_tickets },
          { key: "P4", label: "P4", value: metrics.p4_tickets },
        ];

  function formatMinutes(value) {
    if (value == null) return "—";
    const minutes = Math.round(value);
    if (minutes <= 0) return "<1 мин";
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours === 0) return `${minutes} мин`;
    const days = Math.floor(hours / 24);
    const remHours = hours % 24;
    if (days > 0) {
      if (remHours === 0) return `${days} дн`;
      return `${days} дн ${remHours} ч`;
    }
    return `${hours} ч ${mins.toString().padStart(2, "0")} мин`;
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Статистика</h1>
          <p className="page-header__subtitle">
            Обзор обращений, нагрузки и авто‑решений.
          </p>
        </div>
      </div>
      <section className="panel">
        <h2 className="panel__title">Общие показатели</h2>
        <div className="cards">
          <StatCard
            label="Всего заявок"
            value={metrics?.total_tickets}
            loading={loading}
          />
          <StatCard
            label="Новые сегодня"
            value={metrics?.new_today}
            loading={loading}
          />
          <StatCard
            label="В работе сейчас"
            value={metrics?.in_progress_tickets}
            loading={loading}
          />
          <StatCard
            label="Закрыто сегодня"
            value={metrics?.closed_today}
            loading={loading}
          />
        </div>
      </section>

      <section className="panel">
        <h2 className="panel__title">По категориям обращений</h2>
        <div className="cards">
          <StatCard
            label="Что‑то не работает"
            value={metrics?.problem_tickets}
            loading={loading}
          />
          <StatCard
            label="Есть вопрос"
            value={metrics?.question_tickets}
            loading={loading}
          />
          <StatCard
            label="Предложение или отзыв"
            value={metrics?.feedback_tickets}
            loading={loading}
          />
          <StatCard
            label="Работа и стажировки"
            value={metrics?.career_tickets}
            loading={loading}
          />
          <StatCard
            label="Партнёрство и сотрудничество"
            value={metrics?.partner_tickets}
            loading={loading}
          />
          <StatCard
            label="Другое"
            value={metrics?.other_tickets}
            loading={loading}
          />
        </div>
        <BarChart data={categoryData} loading={loading} kind="categories" />
      </section>

      <section className="panel">
        <h2 className="panel__title">По приоритетам</h2>
        <div className="cards">
          <StatCard label="P1" value={metrics?.p1_tickets} loading={loading} />
          <StatCard label="P2" value={metrics?.p2_tickets} loading={loading} />
          <StatCard label="P3" value={metrics?.p3_tickets} loading={loading} />
          <StatCard label="P4" value={metrics?.p4_tickets} loading={loading} />
        </div>
        <BarChart data={priorityData} loading={loading} kind="priorities" />
      </section>

      <section className="panel">
        <h2 className="panel__title">Качество и авто‑решения</h2>
        <div className="cards">
          <StatCard
            label="% авто‑закрытых (по модели)"
            value={metrics ? `${metrics.auto_closed_percent.toFixed(1)}%` : null}
            loading={loading}
          />
          <StatCard
            label="Открытые заявки в срок (SLA)"
            value={metrics?.open_sla_ok_tickets}
            loading={loading}
          />
          <StatCard
            label="Открытые с нарушением SLA"
            value={metrics?.open_sla_breached_tickets}
            loading={loading}
          />
          <StatCard
            label="Авто‑закрыто с ответом «Да, спасибо»"
            value={metrics?.user_auto_closed_tickets}
            loading={loading}
          />
          <StatCard
            label="Точность классификации"
            value={
              metrics && metrics.classification_accuracy != null
                ? `${metrics.classification_accuracy.toFixed(1)}%`
                : "—"
            }
            loading={loading}
          />
          <StatCard
            label="Среднее время до авто‑решения"
            value={metrics ? formatMinutes(metrics.avg_first_response_minutes) : null}
            loading={loading}
          />
        </div>
      </section>
    </div>
  );
}

function StatCard({ label, value, loading }) {
  return (
    <div className="card">
      <div className="card__label">{label}</div>
      <div className="card__value">
        {loading ? <span className="skeleton skeleton--text" /> : value ?? "—"}
      </div>
    </div>
  );
}

function BarChart({ data, loading, kind }) {
  const max = data.reduce((m, item) => (item.value > m ? item.value : m), 0);

  if (loading) {
    return (
      <div className="chart">
        <div className="chart__empty">
          <span className="skeleton skeleton--text" />
        </div>
      </div>
    );
  }

  if (!data.length || max === 0) {
    return (
      <div className="chart">
        <div className="chart__empty">Пока нет данных для визуализации.</div>
      </div>
    );
  }

  return (
    <div className="chart">
      {data.map((item) => {
        const width = max ? Math.round((item.value / max) * 100) : 0;
        return (
          <div key={item.key} className="chart__row">
            <div className="chart__label">{item.label}</div>
            <div className="chart__bar-wrapper">
              <div
                className={`chart__bar-fill chart__bar-fill--${kind}-${item.key.toLowerCase()}`}
                style={{ width: `${width}%` }}
              />
            </div>
            <div className="chart__value">{item.value}</div>
          </div>
        );
      })}
    </div>
  );
}
