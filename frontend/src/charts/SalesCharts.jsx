import ChartCard from "./ChartCard";
import { TrendBarChart, TrendLineChart } from "./TrendChart";

/**
 * The pair of sales charts — revenue and volume — shared by the Admin
 * Dashboard and the Sales Report in both the admin and manager panels.
 *
 * The caller passes an already-bucketed series (see dailySalesSeries and
 * salesSeriesForRange in ./aggregate) so each page decides its own window:
 * the dashboard shows a fixed last-7-days, while the report follows whatever
 * date range its filters select.
 *
 * Revenue and count stay two charts rather than one with two y-axes, for the
 * reason given in TrendChart.
 */

const money = (value) => `Rs ${Number(value).toLocaleString()}`;

// Axis ticks get the short form so they fit; the tooltip still shows exact.
const moneyTick = (value) =>
  value >= 1000 ? `Rs ${Math.round(value / 1000)}k` : `Rs ${value}`;

export default function SalesCharts({
  series,
  subtitle,
  loading,
  error,
  emptyMessage,
}) {
  // A series of all-zero days is as empty as no series at all — both should
  // read as "nothing sold", not as a chart flatlined against the axis.
  const empty = !series.some((day) => day.count > 0);
  const state = { loading, error, empty, emptyMessage };

  return (
    <div className="row g-3">
      <div className="col-12 col-lg-6">
        <ChartCard title="Revenue" subtitle={subtitle} {...state}>
          <TrendBarChart
            data={series}
            xKey="label"
            yKey="revenue"
            formatValue={money}
            formatTick={moneyTick}
          />
        </ChartCard>
      </div>

      <div className="col-12 col-lg-6">
        <ChartCard title="Sales Volume" subtitle={subtitle} {...state}>
          <TrendLineChart data={series} xKey="label" yKey="count" />
        </ChartCard>
      </div>
    </div>
  );
}
