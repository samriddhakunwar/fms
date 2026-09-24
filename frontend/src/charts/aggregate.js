import { CATEGORICAL, STOCK_STATUS } from "./theme";

const OTHER_COLOR = "#8b95a1";

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

export function dailySalesSeries(sales, days = 7) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const keys = [];
  for (let offset = days - 1; offset >= 0; offset -= 1) {
    const day = new Date(today);
    day.setDate(day.getDate() - offset);
    keys.push(isoDay(day));
  }

  return bucketByDay(sales, keys);
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

export function labelDays(days) {
  return days.map((day) => ({
    day: day.day,
    label: shortDay(day.day),
    revenue: Number(day.revenue),
    count: day.count,
  }));
}

function bucketByDay(sales, dayKeys) {
  const buckets = new Map(dayKeys.map((key) => [key, { revenue: 0, count: 0 }]));

  for (const sale of sales) {
    if (!sale.sale_date) continue;
    const bucket = buckets.get(isoDay(new Date(sale.sale_date)));
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

function isoDay(date) {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

function shortDay(iso) {
  const [, month, day] = iso.split("-");
  return `${day}/${month}`;
}

