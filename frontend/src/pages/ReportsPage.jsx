import { useState } from "react";
import SalesReportTable from "./reports/SalesReportTable";

const TABS = [
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
