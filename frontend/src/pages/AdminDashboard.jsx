import { useEffect, useState } from "react";
import api from "../services/api";

export default function AdminDashboard() {
  const [stats, setStats] = useState({
    total_employees: "—",
    total_products: "—",
    low_stock_products: "—",
    todays_sales: "—",
    todays_revenue: "—",
  });

  useEffect(() => {
    (async () => {
      try {
        const [employeesRes, productsRes, salesRes] = await Promise.all([
          api.get("/employees/summary/"),
          api.get("/products/summary/"),
          api.get("/sales/summary/"),
        ]);
        setStats({
          total_employees: employeesRes.data.total_employees,
          total_products: productsRes.data.total_products,
          low_stock_products: productsRes.data.low_stock_products,
          todays_sales: salesRes.data.todays_sales,
          todays_revenue: Number(salesRes.data.todays_revenue).toFixed(2),
        });
      } catch {
        // Cards keep their placeholder dashes on failure.
      }
    })();
  }, []);

  const cards = [
    { label: "Total Employees", value: stats.total_employees },
    { label: "Total Products", value: stats.total_products },
    { label: "Low Stock Products", value: stats.low_stock_products },
    { label: "Today's Sales", value: stats.todays_sales },
    { label: "Today's Revenue", value: stats.todays_revenue },
  ];

  return (
    <>
      <h2 className="mb-4">Admin Dashboard</h2>
      <div className="row g-3">
        {cards.map((card) => (
          <div className="col-6 col-md-4 col-lg" key={card.label}>
            <div className="card shadow-sm h-100">
              <div className="card-body">
                <h3 className="mb-1">{card.value}</h3>
                <p className="text-muted mb-0 small">{card.label}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
