import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ROLE_LABELS = {
  ADMIN: "Admin",
  INVENTORY_MANAGER: "Manager",
  STAFF: "Staff",
};

export default function DashboardLayout({ title, navItems, children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="d-flex flex-column vh-100">
      <nav className="navbar navbar-dark bg-primary px-3 flex-shrink-0">
        <button
          className="btn btn-outline-light d-lg-none me-2"
          type="button"
          onClick={() => setSidebarOpen((open) => !open)}
        >
          ☰
        </button>
        <span className="navbar-brand mb-0">Factory Management System</span>
        <div className="ms-auto d-flex align-items-center gap-3">
          <span className="text-light small d-none d-sm-inline">
            {user?.first_name || user?.username} · {ROLE_LABELS[user?.role] || user?.role}
          </span>
          <button className="btn btn-sm btn-outline-light" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>

      <div className="d-flex flex-grow-1 overflow-hidden">
        <aside
          className={`bg-light border-end flex-shrink-0 ${sidebarOpen ? "d-block" : "d-none"} d-lg-block`}
          style={{ width: "220px", overflowY: "auto" }}
        >
          <ul className="nav nav-pills flex-column p-3 gap-1">
            {navItems.map((item) => (
              <li className="nav-item" key={item.path}>
                <Link
                  to={item.path}
                  className={`nav-link ${location.pathname === item.path ? "active" : "text-dark"}`}
                  onClick={() => setSidebarOpen(false)}
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </aside>

        <main className="flex-grow-1 p-3 p-md-4 overflow-auto">
          {title && <h2 className="mb-4">{title}</h2>}
          {children}
        </main>
      </div>
    </div>
  );
}
