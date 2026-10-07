import { useState } from "react";

const emptyLine = () => ({ product: "", quantity: 1 });

/** Product/quantity lines of the order and sale forms, priced from `products`. */
export default function useLineItems(products) {
  const [lines, setLines] = useState([emptyLine()]);

  const productById = (id) => products.find((p) => String(p.id) === String(id));

  const lineSubtotal = (line) => {
    const product = productById(line.product);
    if (!product || !line.quantity) return 0;
    return Number(product.selling_price) * Number(line.quantity);
  };

  return {
    lines,
    total: lines.reduce((sum, line) => sum + lineSubtotal(line), 0),
    productById,
    lineSubtotal,
    // Start from a saved record's items, or one blank line.
    reset: (items = []) =>
      setLines(
        items.length
          ? items.map((item) => ({ product: String(item.product), quantity: item.quantity }))
          : [emptyLine()]
      ),
    updateLine: (index, field, value) =>
      setLines((prev) =>
        prev.map((line, i) => (i === index ? { ...line, [field]: value } : line))
      ),
    addLine: () => setLines((prev) => [...prev, emptyLine()]),
    removeLine: (index) => setLines((prev) => prev.filter((_, i) => i !== index)),
  };
}
