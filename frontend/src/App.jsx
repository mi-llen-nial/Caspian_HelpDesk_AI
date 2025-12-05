import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import ShellLayout from "./components/ShellLayout.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import LeadsPage from "./pages/LeadsPage.jsx";
import TicketDetailsPage from "./pages/TicketDetailsPage.jsx";
import FaqPage from "./pages/FaqPage.jsx";

export default function App() {
  return (
    <ShellLayout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/leads" element={<LeadsPage />} />
        <Route path="/tickets/:id" element={<TicketDetailsPage />} />
        <Route path="/faq" element={<FaqPage />} />
      </Routes>
    </ShellLayout>
  );
}

