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
      </section>

      <section className="panel">
        <h2 className="panel__title">По приоритетам</h2>
        <div className="cards">
          <StatCard label="P1" value={metrics?.p1_tickets} loading={loading} />
          <StatCard label="P2" value={metrics?.p2_tickets} loading={loading} />
          <StatCard label="P3" value={metrics?.p3_tickets} loading={loading} />
          <StatCard label="P4" value={metrics?.p4_tickets} loading={loading} />
        </div>
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
