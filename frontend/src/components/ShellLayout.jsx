import React from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import logo from "../assets/logo.png";
import iconDashboard from "../assets/icon-dashboard.svg";
import iconLeads from "../assets/icon-leads.svg";
import iconTemplates from "../assets/icon-templates.svg";

export default function ShellLayout({ children }) {
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const isLeadsRoute = location.pathname.startsWith("/leads");
  const searchParams = React.useMemo(
    () => new URLSearchParams(location.search),
    [location.search],
  );
  const activeDepartment = searchParams.get("department") || "";

  const departments = React.useMemo(
    () => [
      { code: "technical_support", label: "Техподдержка" },
      { code: "tv_support", label: "Телевидение и IPTV" },
      { code: "billing", label: "Биллинг и оплаты" },
      { code: "sales", label: "Продажи и подключения" },
      { code: "customer_care", label: "Сервис и обращения" },
      { code: "hr", label: "HR и вакансии" },
      { code: "partnership", label: "Партнёрство" },
    ],
    [],
  );

  function handleDepartmentClick(code) {
    const params = new URLSearchParams(location.search);
    if (params.get("department") === code) {
      params.delete("department");
    } else {
      params.set("department", code);
    }
    navigate(`/leads?${params.toString()}`);
  }

  return (
    <div className={`app-shell${sidebarCollapsed ? " app-shell--sidebar-collapsed" : ""}`}>
      <aside className={`sidebar${sidebarCollapsed ? " sidebar--collapsed" : ""}`}>
        <div className="sidebar__logo">
          <div className="sidebar__logo-mark sidebar__logo-mark--image">
            <img src={logo} alt="Kazakhtelecom" />
          </div>
          <div className="sidebar__logo-text">
            <span className="sidebar__logo-title">Kazakhtelecom</span>
            <span className="sidebar__logo-subtitle">HelpDesk AI</span>
          </div>
        </div>
        <nav className="sidebar__nav">
          <NavLink to="/dashboard" className={({ isActive }) => navClass(isActive)}>
            <img src={iconDashboard} className="sidebar__nav-icon" alt="" />
            <span className="sidebar__nav-label">Статистика</span>
          </NavLink>
          <NavLink to="/leads" className={({ isActive }) => navClass(isActive)}>
            <img src={iconLeads} className="sidebar__nav-icon" alt="" />
            <span className="sidebar__nav-label">Обращения</span>
          </NavLink>
          {isLeadsRoute && (
            <div className="sidebar__section">
              <div className="sidebar__section-title">Департаменты</div>
              <div className="sidebar__subnav">
                {departments.map((dep) => (
                  <button
                    key={dep.code}
                    type="button"
                    className={`sidebar__subnav-link${
                      activeDepartment === dep.code ? " sidebar__subnav-link--active" : ""
                    }`}
                    onClick={() => handleDepartmentClick(dep.code)}
                  >
                    {dep.label}
                  </button>
                ))}
              </div>
            </div>
          )}
          <NavLink to="/faq" className={({ isActive }) => navClass(isActive)}>
            <img src={iconTemplates} className="sidebar__nav-icon" alt="" />
            <span className="sidebar__nav-label">Шаблоны</span>
          </NavLink>
        </nav>
        <div className="sidebar__footer">v0.1 • AI Help Desk</div>
      </aside>
      <div className="main">
        <header className="topbar">
          <div className="topbar__left">
            <button
              type="button"
              className="sidebar-toggle"
              onClick={() => setSidebarCollapsed((v) => !v)}
            >
              <span className="sidebar-toggle__bar" />
              <span className="sidebar-toggle__bar" />
              <span className="sidebar-toggle__bar" />
            </button>
            <div className="topbar__title">Панель управления</div>
          </div>
        </header>
        <main className="main__content">{children}</main>
      </div>
    </div>
  );
}

function navClass(isActive) {
  return `sidebar__nav-link${isActive ? " sidebar__nav-link--active" : ""}`;
}
