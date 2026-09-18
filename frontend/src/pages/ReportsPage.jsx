import { useState } from "react";
import InventoryReportTable from "./reports/InventoryReportTable";
import EmployeeReportTable from "./reports/EmployeeReportTable";
import SalaryReportTable from "./reports/SalaryReportTable";
import SalesReportTable from "./reports/SalesReportTable";

const TABS = [
  { key: "inventory", label: "Inventory Report", Component: InventoryReportTable },
  { key: "employees", label: "Employee Report", Component: EmployeeReportTable },
  { key: "salary", label: "Salary Report", Component: SalaryReportTable },
  { key: "sales", label: "Sales Report", Component: SalesReportTable },
];

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState(TABS[0].key);
  const ActiveComponent = TABS.find((tab) => tab.key === activeTab).Component;

  return (
    <>
      <h2 className="mb-4">Reports</h2>

      <ul className="nav nav-tabs mb-3">
        {TABS.map((tab) => (
          <li className="nav-item" key={tab.key}>
            <button
              className={`nav-link ${activeTab === tab.key ? "active" : ""}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
            </button>
          </li>
        ))}
      </ul>

      <ActiveComponent />
    </>
  );
}
