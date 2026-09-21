import { useEffect, useState } from "react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";

import ChartCard from "../charts/ChartCard";
import DonutChart from "../charts/DonutChart";
import { stockStatusBreakdown } from "../charts/aggregate";

export default function EmployeeDashboard() {
  const { user } = useAuth();

  const [stock, setStock] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Employees have read-only access to products, so the stock breakdown is the
  // one report they can be shown.
  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      try {
        const { data } = await api.get("/products/");
        setStock(stockStatusBreakdown(data));
      } catch {
        setError("Could not load inventory data.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <>
      <h2 className="mb-4">Employee Dashboard</h2>

      <div className="row g-3">
        <div className="col-12 col-lg-6">
          <div className="card shadow-sm h-100">
            <div className="card-body">
              <h5 className="card-title">
                {user?.first_name} {user?.last_name}
              </h5>
              <dl className="row mb-0 mt-3">
                <dt className="col-5">Email</dt>
                <dd className="col-7">{user?.email || "—"}</dd>

                <dt className="col-5">Status</dt>
                <dd className="col-7">
                  <span
                    className={`badge ${user?.is_active ? "bg-success" : "bg-secondary"}`}
                  >
                    {user?.is_active ? "Active" : "Inactive"}
                  </span>
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="col-12 col-lg-6">
          <ChartCard
            title="Stock Status"
            subtitle="Products by stock level"
            loading={loading}
            error={error}
            empty={!stock.some((slice) => slice.value > 0)}
          >
            <DonutChart data={stock} />
          </ChartCard>
        </div>
      </div>
    </>
  );
}
