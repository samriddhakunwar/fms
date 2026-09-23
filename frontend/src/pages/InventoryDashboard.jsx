import { useEffect, useState } from "react";
import api from "../services/api";

import ChartCard from "../charts/ChartCard";
import DonutChart from "../charts/DonutChart";
import { RankedBarChart } from "../charts/TrendChart";
import { stockStatusBreakdown, topProductsByStock } from "../charts/aggregate";

export default function InventoryDashboard() {
  const [stats, setStats] = useState({
    total_products: "—",
    low_stock_products: "—",
    out_of_stock_products: "—",
  });

  const [charts, setCharts] = useState({ stock: [], topProducts: [] });
  const [chartsLoading, setChartsLoading] = useState(true);
  const [chartsError, setChartsError] = useState("");

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

  // managers only have API access to products, so both charts here
  // are drawn from that one list.
  useEffect(() => {
    (async () => {
      setChartsLoading(true);
      setChartsError("");
      try {
        const { data } = await api.get("/products/");
        setCharts({
          stock: stockStatusBreakdown(data),
          topProducts: topProductsByStock(data, 8),
        });
      } catch {
        setChartsError("Could not load product data.");
      } finally {
        setChartsLoading(false);
      }
    })();
  }, []);

  const cards = [
    { label: "Total Products", value: stats.total_products },
    { label: "Low Stock Products", value: stats.low_stock_products },
    { label: "Out of Stock Products", value: stats.out_of_stock_products },
  ];

  const chartState = { loading: chartsLoading, error: chartsError };

  return (
    <>
      <h2 className="mb-4">manager Dashboard</h2>

      <div className="row g-3 mb-4">
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

      <div className="row g-3">
        <div className="col-12 col-lg-5">
          <ChartCard
            title="Stock Status"
            subtitle="Products by stock level"
            {...chartState}
            empty={!charts.stock.some((slice) => slice.value > 0)}
          >
            <DonutChart data={charts.stock} />
          </ChartCard>
        </div>

        <div className="col-12 col-lg-7">
          <ChartCard
            title="Highest Stock"
            subtitle="Units in stock, top 8 products"
            {...chartState}
            empty={charts.topProducts.length === 0}
          >
            <RankedBarChart data={charts.topProducts} />
          </ChartCard>
        </div>
      </div>
    </>
  );
}
