import { useState } from "react";
import { useNavigate } from "react-router-dom";

import AppSidebar from "./AppSidebar";
import EmployeeTable from "./EmployeeTable";
import InventoryTable from "./InventoryTable";
import OrdersTable from "./OrdersTable";
import PageHeader from "./PageHeader";

import DashboardContent from "../pages/DashboardContent";
import ProfileContent from "../pages/ProfileContent";
import ReportsContent from "../pages/ReportsContent";
import SalesContent from "../pages/SalesContent";

import { roleNames } from "../data/factoryData";

export default function FactoryApp({ role }) {
  const navigate = useNavigate();

  const [page, setPage] = useState("Dashboard");
  const [message, setMessage] = useState("");

  const showMessage = (text) => {
    setMessage(text);

    window.setTimeout(() => {
      setMessage("");
    }, 2500);
  };

  const renderPage = () => {
    switch (page) {
      case "Inventory":
        return (
          <>
            <InventoryTable
              canManage={role !== "staff"}
              onAdd={() =>
                showMessage("New item form will open here.")
              }
            />
          </>
        );

      case "Orders":
        return (
          <>
            <PageHeader
              title="Order Management"
              description="Manage customer orders and their current status."
            />

            <OrdersTable
              onAdd={() =>
                showMessage("New order form will open here.")
              }
            />
          </>
        );

      case "Sales":
        return <SalesContent />;

      case "Reports":
        return (
          <ReportsContent
            onDownload={() =>
              showMessage("Report download started.")
            }
          />
        );

      case "User Management":
      case "Staff Records":
        return (
          <>
            <PageHeader
              title={page}
              description="List of factory employees."
            />

            <EmployeeTable />
          </>
        );

      case "My Profile":
        return <ProfileContent />;

      default:
        return (
          <DashboardContent
            role={role}
            onAddItem={() =>
              showMessage("New item form will open here.")
            }
            onAddOrder={() =>
              showMessage("New order form will open here.")
            }
          />
        );
    }
  };

  return (
    <div className="simple-app">
      <AppSidebar
        role={role}
        page={page}
        onSelect={setPage}
        onLogout={() => navigate("/login")}
      />

      <main className="simple-main">
        <header>
          <span>Factory Management System</span>
          <span>{roleNames[role]}</span>
        </header>

        {message && (
          <div className="message">
            {message}
          </div>
        )}

        <div className="page-content">
          {renderPage()}
        </div>
      </main>
    </div>
  );
}