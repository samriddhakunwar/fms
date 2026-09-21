/**
 * Chart aggregation helpers.
 *
 * Every report already has a list endpoint, so the dashboards reuse those and
 * roll the rows up here rather than adding summary endpoints to the API.
 */

import { CATEGORICAL, STOCK_STATUS } from "./theme";

/** The de-emphasis gray used for a folded "Other" slice. */
const OTHER_COLOR = "#8b95a1";

/** Counts products per stock status, keeping the fixed In → Low → Out order. */
export function stockStatusBreakdown(products) {
  const counts = { IN_STOCK: 0, LOW_STOCK: 0, OUT_OF_STOCK: 0 };

  for (const product of products) {
    if (counts[product.stock_status] !== undefined) {
      counts[product.stock_status] += 1;
    }
  }

  return Object.entries(STOCK_STATUS).map(([key, { label, color }]) => ({
    name: label,
    value: counts[key],
    color,
  }));
}

/**
 * Counts rows by one field and paints them from the categorical slots in order.
 * Anything past the available slots folds into "Other" — a generated hue would
 * be indistinguishable from an existing one under colour-blindness.
 */
export function countByField(rows, field, labels) {
  const counts = new Map();

  for (const row of rows) {
    const key = row[field];
    if (key == null) continue;
    counts.set(key, (counts.get(key) || 0) + 1);
  }

  const ordered = [...counts.entries()].sort((a, b) => b[1] - a[1]);
  const head = ordered.slice(0, CATEGORICAL.length);
  const tail = ordered.slice(CATEGORICAL.length);

  const slices = head.map(([key, value], index) => ({
    name: labels?.[key] ?? key,
    value,
    color: CATEGORICAL[index],
  }));

  if (tail.length) {
    slices.push({
      name: "Other",
      value: tail.reduce((sum, [, value]) => sum + value, 0),
      color: OTHER_COLOR,
    });
  }

  return slices;
}

/** Builds a dense last-N-days series, so days with no sales still show as 0. */
export function dailySalesSeries(sales, days = 7) {
  const buckets = new Map();
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  for (let offset = days - 1; offset >= 0; offset -= 1) {
    const day = new Date(today);
    day.setDate(day.getDate() - offset);
    buckets.set(isoDay(day), { revenue: 0, count: 0 });
  }

  for (const sale of sales) {
    if (!sale.sale_date) continue;
    const key = isoDay(new Date(sale.sale_date));
    const bucket = buckets.get(key);
    if (!bucket) continue; // outside the window
    bucket.revenue += Number(sale.total_amount) || 0;
    bucket.count += 1;
  }

  return [...buckets.entries()].map(([key, { revenue, count }]) => ({
    day: key,
    label: shortDay(key),
    revenue: Number(revenue.toFixed(2)),
    count,
  }));
}

/** Highest-stock products, for a magnitude comparison. */
export function topProductsByStock(products, limit = 8) {
  return [...products]
    .sort((a, b) => b.quantity_in_stock - a.quantity_in_stock)
    .slice(0, limit)
    .map((product) => ({
      name: product.product_name,
      value: product.quantity_in_stock,
    }));
}

function isoDay(date) {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

function shortDay(iso) {
  const [, month, day] = iso.split("-");
  return `${day}/${month}`;
}
