import ChartCard from "./ChartCard";
import { TrendBarChart, TrendLineChart } from "./TrendChart";

const money = (value) => `Rs ${Number(value).toLocaleString()}`;

const moneyTick = (value) =>
  value >= 1000 ? `Rs ${Math.round(value / 1000)}k` : `Rs ${value}`;

export default function SalesCharts({
  series,
  subtitle,
  volumeSubtitle = subtitle,
  loading,
  error,
  emptyMessage,
}) {
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
        <ChartCard title="Sales Volume" subtitle={volumeSubtitle} {...state}>
          <TrendLineChart data={series} xKey="label" yKey="count" />
        </ChartCard>
      </div>
    </div>
  );
}
