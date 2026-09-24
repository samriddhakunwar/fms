export const CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"];

export const STOCK_STATUS = {
  IN_STOCK: { label: "In Stock", color: "#198754" },
  LOW_STOCK: { label: "Low Stock", color: "#997404" },
  OUT_OF_STOCK: { label: "Out of Stock", color: "#b02a37" },
};

export const SERIES_HUE = CATEGORICAL[0];

export const INK = {
  primary: "#18212b",
  secondary: "#5b6774",
  muted: "#8b95a1",
  grid: "#e6eaef",
  surface: "#ffffff",
};

export const MARK = {
  barMaxWidth: 24,
  /** Rounded data-end, square at the baseline. */
  barRadius: [4, 4, 0, 0],
  lineWidth: 2,
  dotRadius: 4,
  gapWidth: 2,
};

export const AXIS_PROPS = {
  stroke: INK.grid,
  tick: { fill: INK.muted, fontSize: 12 },
  tickLine: false,
};

export const TOOLTIP_PROPS = {
  contentStyle: {
    background: INK.surface,
    border: `1px solid ${INK.grid}`,
    borderRadius: 8,
    fontSize: 13,
    boxShadow: "0 4px 12px rgba(16, 24, 40, 0.07)",
  },
  labelStyle: { color: INK.primary, fontWeight: 600, marginBottom: 2 },
  itemStyle: { color: INK.secondary },
  cursor: { fill: "rgba(42, 120, 214, 0.06)" },
};
