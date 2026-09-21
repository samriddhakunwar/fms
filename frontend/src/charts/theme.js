/**
 * Chart theme
 * ===========
 * Chart colours are a separate job from UI chrome, so they live here rather
 * than in index.css: a hue that works as a button background is often wrong
 * as a data mark. Every set below was checked with a CVD/contrast validator
 * against the white card surface the charts actually render on (#ffffff).
 *
 * The ink and grid values mirror the --fms-* tokens in index.css so the axes
 * and labels match the rest of the app.
 */

/**
 * Categorical slots — for data where the categories are the subject and have
 * no natural order (payment method, employee status).
 *
 * Validated all-pairs on the white card surface: lightness band, chroma floor,
 * CVD separation, normal-vision floor and contrast all pass. The order is the
 * safety mechanism, so take slots from the front and never reorder or cycle.
 * A fifth category folds into "Other" rather than inventing a hue.
 */
export const CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"];

/**
 * Stock status is a *status* scale, not a categorical one — the hues are fixed
 * by meaning and match the table badges on the inventory page.
 *
 * Red/amber/green cannot clear a colour-blindness separation gate by hue alone
 * (deuteranopia collapses red against green); no choice of three status hues
 * can. Identity therefore never rests on colour here: every segment is directly
 * labelled and the legend repeats the name. These are darker steps than the
 * Bootstrap badge colours so each clears 3:1 against the white card — the raw
 * badge amber sits at 1.63:1, which is unreadable as a chart mark.
 */
export const STOCK_STATUS = {
  IN_STOCK: { label: "In Stock", color: "#198754" },
  LOW_STOCK: { label: "Low Stock", color: "#997404" },
  OUT_OF_STOCK: { label: "Out of Stock", color: "#b02a37" },
};

/** Single-hue default for one-series charts (trend bars and lines). */
export const SERIES_HUE = CATEGORICAL[0];

/** Mirrors the --fms-* ink tokens so charts match the surrounding UI. */
export const INK = {
  primary: "#18212b",
  secondary: "#5b6774",
  muted: "#8b95a1",
  grid: "#e6eaef",
  surface: "#ffffff",
};

/** Fixed mark specs — applied identically by every chart in the app. */
export const MARK = {
  /** Bars never fill their slot; the leftover band is deliberate air. */
  barMaxWidth: 24,
  /** Rounded data-end, square at the baseline. */
  barRadius: [4, 4, 0, 0],
  lineWidth: 2,
  dotRadius: 4,
  /** The surface-coloured gap that separates touching marks. */
  gapWidth: 2,
};

/** Recharts axis props — recessive, so the data stays the loud part. */
export const AXIS_PROPS = {
  stroke: INK.grid,
  tick: { fill: INK.muted, fontSize: 12 },
  tickLine: false,
};

/** Tooltip chrome, matching the app's card styling. */
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
