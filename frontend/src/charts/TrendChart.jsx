import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { AXIS_PROPS, INK, MARK, SERIES_HUE, TOOLTIP_PROPS } from "./theme";

const GRID = <CartesianGrid stroke={INK.grid} strokeWidth={1} vertical={false} />;

export function TrendBarChart({
  data,
  xKey,
  yKey,
  height = 240,
  formatValue,
  formatTick,
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        {GRID}
        <XAxis dataKey={xKey} {...AXIS_PROPS} axisLine={{ stroke: INK.grid }} />
        <YAxis
          {...AXIS_PROPS}
          axisLine={false}
          width={68}
          tickFormatter={formatTick ?? formatValue}
        />
        <Tooltip
          {...TOOLTIP_PROPS}
          formatter={(value) => [formatValue ? formatValue(value) : value, ""]}
        />
        <Bar
          dataKey={yKey}
          fill={SERIES_HUE}
          maxBarSize={MARK.barMaxWidth}
          radius={MARK.barRadius}
          isAnimationActive={false}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function TrendLineChart({ data, xKey, yKey, height = 240, formatValue }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
        {GRID}
        <XAxis dataKey={xKey} {...AXIS_PROPS} axisLine={{ stroke: INK.grid }} />
        <YAxis
          {...AXIS_PROPS}
          axisLine={false}
          width={44}
          allowDecimals={false}
          tickFormatter={formatValue}
        />
        <Tooltip
          {...TOOLTIP_PROPS}
          cursor={{ stroke: INK.grid, strokeWidth: 1 }}
          formatter={(value) => [formatValue ? formatValue(value) : value, ""]}
        />
        <Line
          type="linear"
          dataKey={yKey}
          stroke={SERIES_HUE}
          strokeWidth={MARK.lineWidth}
          strokeLinecap="round"
          strokeLinejoin="round"
          dot={{
            r: MARK.dotRadius,
            fill: SERIES_HUE,
            stroke: INK.surface,
            strokeWidth: MARK.gapWidth,
          }}
          activeDot={{ r: MARK.dotRadius + 2 }}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function RankedBarChart({ data, height = 260 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 16, bottom: 0, left: 8 }}
      >
        <CartesianGrid stroke={INK.grid} strokeWidth={1} horizontal={false} />
        <XAxis type="number" {...AXIS_PROPS} axisLine={{ stroke: INK.grid }} />
        <YAxis
          type="category"
          dataKey="name"
          {...AXIS_PROPS}
          axisLine={false}
          width={110}
          tick={{ fill: INK.secondary, fontSize: 12 }}
        />
        <Tooltip {...TOOLTIP_PROPS} formatter={(value) => [value, "In stock"]} />
        <Bar
          dataKey="value"
          fill={SERIES_HUE}
          maxBarSize={MARK.barMaxWidth}
          radius={[0, 4, 4, 0]}
          isAnimationActive={false}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
