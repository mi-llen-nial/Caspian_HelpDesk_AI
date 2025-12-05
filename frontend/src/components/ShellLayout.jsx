import React from "react";
import { NavLink } from "react-router-dom";

export default function ShellLayout({ children }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar__logo">
          <div className="sidebar__logo-mark">KZ</div>
          <div className="sidebar__logo-text">
            <span className="sidebar__logo-title">Kazakhtelecom</span>
            <span className="sidebar__logo-subtitle">HelpDesk AI</span>
          </div>
        </div>
        <nav className="sidebar__nav">
          <NavLink to="/dashboard" className={({ isActive }) => navClass(isActive)}>
            <span className="sidebar__nav-dot" />
            Дашборд
          </NavLink>
          <NavLink to="/leads" className={({ isActive }) => navClass(isActive)}>
            <span className="sidebar__nav-dot" />
            Пользователи / Лиды
          </NavLink>
          <NavLink to="/faq" className={({ isActive }) => navClass(isActive)}>
            <span className="sidebar__nav-dot" />
            База знаний
          </NavLink>
        </nav>
        <div className="sidebar__footer">v0.1 • AI Help Desk</div>
      </aside>
      <div className="main">
        <header className="topbar">
          <div className="topbar__title">Панель управления</div>
        </header>
        <main className="main__content">{children}</main>
      </div>
    </div>
  );
}

function navClass(isActive) {
  return `sidebar__nav-link${isActive ? " sidebar__nav-link--active" : ""}`;
}

