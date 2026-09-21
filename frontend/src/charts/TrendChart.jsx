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

/**
 * Single-series charts over time.
 *
 * One series means no legend box — the card's title already says what is
 * plotted, and a one-swatch legend would only restate it. The grid is
 * horizontal-only and hairline so it stays behind the data.
 *
 * Revenue and count are deliberately two separate charts rather than one with
 * two y-axes: a dual-axis chart lets the author imply a correlation by choosing
 * the scales, which is the single most misleading thing a chart can do.
 */

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
          // Wide enough for the longest tick: a clipped axis label is worse
          // than no axis at all. Ticks use the compact form, the tooltip the
          // full one.
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
          // Straight segments between readings. A smoothed curve would draw
          // values between two days that were never measured.
          type="linear"
          dataKey={yKey}
          stroke={SERIES_HUE}
          strokeWidth={MARK.lineWidth}
          strokeLinecap="round"
          strokeLinejoin="round"
          // The 2px surface ring keeps dots legible where they cross the line.
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

/**
 * Horizontal magnitude comparison — long product names need the room, which a
 * vertical column chart cannot give them without rotating the labels.
 */
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
          // Rounded data-end on the right, square against the baseline.
          radius={[0, 4, 4, 0]}
          isAnimationActive={false}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
