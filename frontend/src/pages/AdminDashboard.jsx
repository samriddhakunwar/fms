import { useEffect, useState } from "react";
import api from "../services/api";

import ChartCard from "../charts/ChartCard";
import DonutChart from "../charts/DonutChart";
import { TrendBarChart, TrendLineChart } from "../charts/TrendChart";
import {
  countByField,
  dailySalesSeries,
  stockStatusBreakdown,
} from "../charts/aggregate";

const STAFF_STATUS_LABELS = {
  ACTIVE: "Active",
  INACTIVE: "Inactive",
};

const money = (value) => `Rs ${Number(value).toLocaleString()}`;

const moneyTick = (value) =>
  value >= 1000 ? `Rs ${Math.round(value / 1000)}k` : `Rs ${value}`;

export default function AdminDashboard() {
  const [stats, setStats] = useState({
    total_staff: "—",
    total_products: "—",
    low_stock_products: "—",
    todays_sales: "—",
    todays_revenue: "—",
  });

  const [charts, setCharts] = useState({
    stock: [],
    staff: [],
    sales: [],
  });
  const [chartsLoading, setChartsLoading] = useState(true);
  const [chartsError, setChartsError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [staffRes, productsRes, salesRes] = await Promise.all([
          api.get("/staff/summary/"),
          api.get("/products/summary/"),
          api.get("/sales/summary/"),
        ]);
        setStats({
          total_staff: staffRes.data.total_staff,
          total_products: productsRes.data.total_products,
          low_stock_products: productsRes.data.low_stock_products,
          todays_sales: salesRes.data.todays_sales,
          todays_revenue: Number(salesRes.data.todays_revenue).toFixed(2),
        });
      } catch {
        // Cards keep placeholder dashes.
      }
    })();
  }, []);

  useEffect(() => {
    (async () => {
      setChartsLoading(true);
      setChartsError("");
      try {
        const [products, staff, sales] = await Promise.all([
          api.get("/products/"),
          api.get("/staff/"),
          api.get("/sales/"),
        ]);
        setCharts({
          stock: stockStatusBreakdown(products.data),
          staff: countByField(staff.data, "status", STAFF_STATUS_LABELS),
          sales: dailySalesSeries(sales.data, 7),
        });
      } catch {
        setChartsError("Could not load report data.");
      } finally {
        setChartsLoading(false);
      }
    })();
  }, []);

  const cards = [
    { label: "Total Staff", value: stats.total_staff },
    { label: "Total Products", value: stats.total_products },
    { label: "Low Stock Products", value: stats.low_stock_products },
    { label: "Today's Sales", value: stats.todays_sales },
    { label: "Today's Revenue", value: stats.todays_revenue },
  ];

  const hasSales = charts.sales.some((day) => day.count > 0);
  const chartState = { loading: chartsLoading, error: chartsError };

  return (
    <>
      <h2 className="mb-4">Admin Dashboard</h2>

      <div className="row g-3 mb-4">
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

      <div className="row g-3 mb-3">
        <div className="col-12 col-lg-6">
          <ChartCard
            title="Stock Status"
            subtitle="Products by stock level"
            {...chartState}
            empty={!charts.stock.some((slice) => slice.value > 0)}
          >
            <DonutChart data={charts.stock} />
          </ChartCard>
        </div>

        <div className="col-12 col-lg-6">
          <ChartCard
            title="Staff"
            subtitle="Active vs inactive"
            {...chartState}
            empty={charts.staff.length === 0}
          >
            <DonutChart data={charts.staff} />
          </ChartCard>
        </div>
      </div>

      <div className="row g-3">
        <div className="col-12 col-lg-6">
          <ChartCard
            title="Revenue"
            subtitle="Last 7 days"
            {...chartState}
            empty={!hasSales}
          >
            <TrendBarChart
              data={charts.sales}
              xKey="label"
              yKey="revenue"
              formatValue={money}
              formatTick={moneyTick}
            />
          </ChartCard>
        </div>

        <div className="col-12 col-lg-6">
          <ChartCard
            title="Sales Volume"
            subtitle="Number of sales, last 7 days"
            {...chartState}
            empty={!hasSales}
          >
            <TrendLineChart data={charts.sales} xKey="label" yKey="count" />
          </ChartCard>
        </div>
      </div>
    </>
  );
}
