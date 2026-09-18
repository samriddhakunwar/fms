import { useEffect, useState } from "react";
import api, { getErrorMessage } from "../../services/api";

const STATUS_BADGE = {
  IN_STOCK: { label: "In Stock", className: "bg-success" },
  LOW_STOCK: { label: "⚠ Low Stock", className: "bg-warning text-dark" },
  OUT_OF_STOCK: { label: "Out of Stock", className: "bg-danger" },
};

export default function InventoryReportTable() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lowStockOnly, setLowStockOnly] = useState(false);

  const load = async (onlyLowStock) => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/products/", {
        params: onlyLowStock ? { low_stock: "true" } : {},
      });
      setProducts(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(false);
  }, []);

  return (
    <>
      <div className="form-check mb-3">
        <input
          type="checkbox"
          className="form-check-input"
          id="lowStockOnly"
          checked={lowStockOnly}
          onChange={(e) => {
            setLowStockOnly(e.target.checked);
            load(e.target.checked);
          }}
        />
        <label className="form-check-label" htmlFor="lowStockOnly">
          Show low-stock products only
        </label>
      </div>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      <div className="table-responsive">
        <table className="table table-hover align-middle bg-white">
          <thead>
            <tr>
              <th>Product</th>
              <th>Current Stock</th>
              <th>Minimum Stock</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={4} className="text-center py-4">
                  Loading…
                </td>
              </tr>
            ) : products.length === 0 ? (
              <tr>
                <td colSpan={4} className="text-center py-4 text-muted">
                  No products found.
                </td>
              </tr>
            ) : (
              products.map((product) => {
                const badge = STATUS_BADGE[product.stock_status] || STATUS_BADGE.IN_STOCK;
                return (
                  <tr key={product.id}>
                    <td>{product.product_name}</td>
                    <td>{product.quantity_in_stock}</td>
                    <td>{product.minimum_stock_level}</td>
                    <td>
                      <span className={`badge ${badge.className}`}>{badge.label}</span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
