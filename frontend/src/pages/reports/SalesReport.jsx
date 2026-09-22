import { useEffect, useMemo, useState } from "react";

import api, { getErrorMessage } from "../../services/api";
import SalesCharts from "../../charts/SalesCharts";
import { salesSeriesForRange, salesStats } from "../../charts/aggregate";

/**
 * Sales Report.
 *
 * The report answers "how did sales go over this period", so it leads with the
 * headline figures and the same revenue/volume charts the Admin Dashboard
 * shows — not a row-by-row invoice list. The individual invoices already have a
 * home on the Sales page; repeating them here only buried the trend.
 */

const money = (value) =>
  `Rs ${Number(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;

const longDay = (iso) =>
  new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });

export default function SalesReport() {
  const [sales, setSales] = useState([]);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  // The range the loaded rows actually cover, which only moves on Apply — the
  // charts must not redraw while the user is still picking dates.
  const [range, setRange] = useState({ start: "", end: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async (start, end) => {
    setLoading(true);
    setError("");
    try {
      const params = {};
      if (start) params.start_date = start;
      if (end) params.end_date = end;
      const { data } = await api.get("/sales/", { params });
      setSales(data);
      setRange({ start, end });
    } catch (err) {
      setError(getErrorMessage(err));
      setSales([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load("", "");
  }, []);

  const series = useMemo(
    () => salesSeriesForRange(sales, range.start, range.end),
    [sales, range]
  );
  const stats = useMemo(() => salesStats(series), [series]);

  const applyFilters = (event) => {
    event.preventDefault();
    load(startDate, endDate);
  };

  const resetFilters = () => {
    setStartDate("");
    setEndDate("");
    load("", "");
  };

  const filtered = Boolean(range.start || range.end);
  const subtitle = filtered
    ? `${range.start ? longDay(range.start) : "Earliest"} – ${
        range.end ? longDay(range.end) : "Today"
      }`
    : "Last 7 days";

  const tiles = [
    { label: "Total sales", value: stats.totalSales },
    { label: "Total revenue", value: money(stats.totalRevenue) },
    {
      label: "Average daily revenue",
      value: money(stats.avgDailyRevenue),
      caption: `Across ${stats.days} day${stats.days === 1 ? "" : "s"}`,
    },
    {
      label: "Busiest day",
      value: stats.busiestDay ? `${stats.busiestDay.count} sales` : "—",
      caption: stats.busiestDay ? longDay(stats.busiestDay.day) : null,
    },
    {
      label: "Quietest day",
      value: stats.quietestDay ? `${stats.quietestDay.count} sales` : "—",
      caption: stats.quietestDay
        ? `${longDay(stats.quietestDay.day)} · days with sales only`
        : null,
    },
    {
      label: "Best revenue day",
      value: stats.bestRevenueDay ? money(stats.bestRevenueDay.revenue) : "—",
      caption: stats.bestRevenueDay ? longDay(stats.bestRevenueDay.day) : null,
    },
  ];

  return (
    <>
      <form className="row g-2 mb-3 align-items-center" onSubmit={applyFilters}>
        <div className="col-auto">
          <input
            type="date"
            className="form-control"
            aria-label="Start date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>
        <div className="col-auto">
          <input
            type="date"
            className="form-control"
            aria-label="End date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
        <div className="col-auto">
          <button type="submit" className="btn btn-outline-secondary">
            Apply
          </button>
        </div>
        {filtered && (
          <div className="col-auto">
            <button
              type="button"
              className="btn btn-link px-0"
              onClick={resetFilters}
            >
              Clear
            </button>
          </div>
        )}
      </form>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      <div className="row g-3 mb-3">
        {tiles.map((tile) => (
          <div className="col-6 col-lg-4 col-xl-2" key={tile.label}>
            <div className="card shadow-sm h-100">
              <div className="card-body">
                <h3 className="mb-1">{loading ? "—" : tile.value}</h3>
                <p className="text-muted mb-0 small">{tile.label}</p>
                {!loading && tile.caption && (
                  <p className="text-muted mb-0 small">{tile.caption}</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <SalesCharts
        series={series}
        subtitle={subtitle}
        loading={loading}
        error={error}
        emptyMessage="No sales in this period."
      />
    </>
  );
}
