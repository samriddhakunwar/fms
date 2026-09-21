import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import { INK, MARK, TOOLTIP_PROPS } from "./theme";

/**
 * Part-to-whole donut.
 *
 * Every slice is directly labelled with its count and the legend repeats the
 * category name, so identity never depends on telling two hues apart. Slices
 * under 5% are left unlabelled rather than allowed to collide — their values
 * stay in the legend and tooltip, so nothing is hidden.
 */
export default function DonutChart({ data, height = 260, valueSuffix = "" }) {
  const total = data.reduce((sum, slice) => sum + slice.value, 0);

  const renderLabel = ({ cx, cy, midAngle, outerRadius, value }) => {
    if (!total || value / total < 0.05) return null;

    const radians = -midAngle * (Math.PI / 180);
    const radius = outerRadius + 16;
    const x = cx + radius * Math.cos(radians);
    const y = cy + radius * Math.sin(radians);

    return (
      <text
        x={x}
        y={y}
        // Labels wear ink, never the slice colour — the mark carries identity.
        fill={INK.secondary}
        fontSize={12}
        fontWeight={600}
        textAnchor={x > cx ? "start" : "end"}
        dominantBaseline="central"
      >
        {value}
      </text>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart margin={{ top: 8, right: 28, bottom: 0, left: 28 }}>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="45%"
          innerRadius="52%"
          outerRadius="76%"
          // The 2px surface-coloured gap that separates touching segments.
          stroke={INK.surface}
          strokeWidth={MARK.gapWidth}
          paddingAngle={1}
          label={renderLabel}
          labelLine={false}
          isAnimationActive={false}
        >
          {data.map((slice) => (
            <Cell key={slice.name} fill={slice.color} />
          ))}
        </Pie>

        <Tooltip
          {...TOOLTIP_PROPS}
          cursor={false}
          formatter={(value, name) => [
            `${value}${valueSuffix} (${total ? Math.round((value / total) * 100) : 0}%)`,
            name,
          ]}
        />

        <Legend
          verticalAlign="bottom"
          height={28}
          iconType="circle"
          iconSize={9}
          formatter={(name) => (
            <span style={{ color: INK.secondary, fontSize: 12 }}>{name}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
