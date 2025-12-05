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
          <h1>Дашборд</h1>
          <p className="page-header__subtitle">Общая сводка по обращениям и авто‑решениям.</p>
        </div>
      </div>
      <div className="cards">
        <StatCard
          label="Всего тикетов"
          value={metrics?.total_tickets}
          loading={loading}
        />
        <StatCard label="Новые сегодня" value={metrics?.new_today} loading={loading} />
        <StatCard
          label="% авто‑закрытых"
          value={metrics ? `${metrics.auto_closed_percent.toFixed(1)}%` : null}
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

