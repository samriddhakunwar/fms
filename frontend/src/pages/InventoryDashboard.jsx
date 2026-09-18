import { useEffect, useState } from "react";
import api from "../services/api";

export default function InventoryDashboard() {
  const [stats, setStats] = useState({
    total_products: "—",
    low_stock_products: "—",
    out_of_stock_products: "—",
  });

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get("/products/summary/");
        setStats(data);
      } catch {
        // Cards keep their placeholder dashes on failure.
      }
    })();
  }, []);

  const cards = [
    { label: "Total Products", value: stats.total_products },
    { label: "Low Stock Products", value: stats.low_stock_products },
    { label: "Out of Stock Products", value: stats.out_of_stock_products },
  ];

  return (
    <>
      <h2 className="mb-4">Inventory Manager Dashboard</h2>
      <div className="row g-3">
        {cards.map((card) => (
          <div className="col-6 col-md-4" key={card.label}>
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
