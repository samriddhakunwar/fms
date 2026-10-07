import SalesReport from "./reports/SalesReport";

export default function ReportsPage() {
  return (
    <>
      <h2 className="mb-4">Reports</h2>

      <ul className="nav nav-tabs mb-3">
        <li className="nav-item">
          <button className="nav-link active">Sales Report</button>
        </li>
      </ul>

      <SalesReport />
    </>
  );
}
