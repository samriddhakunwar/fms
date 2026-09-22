import { useEffect, useState } from "react";
import api, { getErrorMessage } from "../services/api";

function emptyLine() {
  return { product: "", quantity: 1 };
}

export default function SalesPage() {
  const [sales, setSales] = useState([]);
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [soldTo, setSoldTo] = useState("");
  const [lines, setLines] = useState([emptyLine()]);
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  const [viewSale, setViewSale] = useState(null);

  const loadSales = async (params = {}) => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/sales/", { params });
      setSales(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const loadProducts = async () => {
    try {
      const { data } = await api.get("/products/");
      setProducts(data);
    } catch {
      // Product dropdown just stays empty; the table above shows any error.
    }
  };

  useEffect(() => {
    loadSales();
    loadProducts();
  }, []);

  const applyFilters = (event) => {
    event.preventDefault();
    const params = {};
    if (search) params.search = search;
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    loadSales(params);
  };

  const openForm = () => {
    setSoldTo("");
    setLines([emptyLine()]);
    setFormError("");
    setShowForm(true);
  };

  const updateLine = (index, field, value) => {
    setLines((prev) =>
      prev.map((line, i) => (i === index ? { ...line, [field]: value } : line))
    );
  };

  const addLine = () => setLines((prev) => [...prev, emptyLine()]);
  const removeLine = (index) =>
    setLines((prev) => prev.filter((_, i) => i !== index));

  const productById = (id) => products.find((p) => String(p.id) === String(id));

  const lineSubtotal = (line) => {
    const product = productById(line.product);
    if (!product || !line.quantity) return 0;
    return Number(product.selling_price) * Number(line.quantity);
  };

  const total = lines.reduce((sum, line) => sum + lineSubtotal(line), 0);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormError("");

    if (!soldTo.trim()) {
      setFormError("Enter the customer this sale is for.");
      return;
    }

    const validLines = lines.filter((line) => line.product && Number(line.quantity) > 0);
    if (validLines.length === 0) {
      setFormError("Add at least one product line.");
      return;
    }

    setSaving(true);
    try {
      await api.post("/sales/", {
        sold_to: soldTo.trim(),
        items_input: validLines.map((line) => ({
          product: Number(line.product),
          quantity: Number(line.quantity),
        })),
      });
      setShowForm(false);
      await Promise.all([loadSales(), loadProducts()]);
    } catch (err) {
      setFormError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <div className="page-head d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h2 className="mb-0">Sales</h2>
        <button className="btn btn-primary" onClick={openForm}>
          + New Sale
        </button>
      </div>

      <form className="row g-2 mb-3" onSubmit={applyFilters}>
        <div className="col-auto" style={{ minWidth: "220px" }}>
          <input
            type="search"
            className="form-control"
            placeholder="Search invoice number…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="col-auto">
          <input
            type="date"
            className="form-control"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>
        <div className="col-auto">
          <input
            type="date"
            className="form-control"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
        <div className="col-auto">
          <button type="submit" className="btn btn-outline-secondary">
            Apply
          </button>
        </div>
      </form>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      <div className="table-responsive">
        <table className="table table-hover align-middle bg-white">
          <thead>
            <tr>
              <th>Invoice Number</th>
              <th>Sold To</th>
              <th>Total Amount</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="text-center py-4">
                  Loading…
                </td>
              </tr>
            ) : sales.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center py-4 text-muted">
                  No sales recorded.
                </td>
              </tr>
            ) : (
              sales.map((sale) => (
                <tr key={sale.id}>
                  <td>{sale.invoice_number}</td>
                  <td>{sale.sold_to}</td>
                  <td>{Number(sale.total_amount).toFixed(2)}</td>
                  <td>{new Date(sale.sale_date).toLocaleString()}</td>
                  <td>
                    <button
                      className="btn btn-sm btn-outline-secondary"
                      onClick={() => setViewSale(sale)}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showForm && (
        <>
          <div className="modal d-block" tabIndex={-1} role="dialog">
            <div className="modal-dialog modal-lg" role="document">
              <div className="modal-content">
                <form onSubmit={handleSubmit}>
                  <div className="modal-header">
                    <h5 className="modal-title">New Sale</h5>
                    <button
                      type="button"
                      className="btn-close"
                      onClick={() => setShowForm(false)}
                      aria-label="Close"
                    />
                  </div>
                  <div className="modal-body">
                    {formError && (
                      <div className="alert alert-danger py-2">{formError}</div>
                    )}

                    <div className="mb-3" style={{ maxWidth: "360px" }}>
                      <label className="form-label" htmlFor="sold-to">
                        Sold To
                      </label>
                      <input
                        id="sold-to"
                        type="text"
                        className="form-control"
                        placeholder="e.g. Shyam Pvt. Ltd."
                        value={soldTo}
                        onChange={(e) => setSoldTo(e.target.value)}
                        required
                      />
                    </div>

                    <table className="table">
                      <thead>
                        <tr>
                          <th>Product</th>
                          <th style={{ width: "120px" }}>Quantity</th>
                          <th style={{ width: "120px" }}>Unit Price</th>
                          <th style={{ width: "120px" }}>Subtotal</th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        {lines.map((line, index) => {
                          const product = productById(line.product);
                          return (
                            <tr key={index}>
                              <td>
                                <select
                                  className="form-select"
                                  value={line.product}
                                  onChange={(e) =>
                                    updateLine(index, "product", e.target.value)
                                  }
                                  required
                                >
                                  <option value="" disabled>
                                    Select product…
                                  </option>
                                  {products.map((p) => (
                                    <option key={p.id} value={p.id}>
                                      {p.product_name} ({p.quantity_in_stock} in stock)
                                    </option>
                                  ))}
                                </select>
                              </td>
                              <td>
                                <input
                                  type="number"
                                  min="1"
                                  className="form-control"
                                  value={line.quantity}
                                  onChange={(e) =>
                                    updateLine(index, "quantity", e.target.value)
                                  }
                                  required
                                />
                              </td>
                              <td>
                                {product ? Number(product.selling_price).toFixed(2) : "—"}
                              </td>
                              <td>{lineSubtotal(line).toFixed(2)}</td>
                              <td>
                                {lines.length > 1 && (
                                  <button
                                    type="button"
                                    className="btn btn-sm btn-outline-danger"
                                    onClick={() => removeLine(index)}
                                  >
                                    ✕
                                  </button>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>

                    <button
                      type="button"
                      className="btn btn-sm btn-outline-secondary"
                      onClick={addLine}
                    >
                      + Add Line
                    </button>

                    <div className="text-end mt-3 fs-5">
                      Total: <strong>{total.toFixed(2)}</strong>
                    </div>
                  </div>
                  <div className="modal-footer">
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => setShowForm(false)}
                    >
                      Cancel
                    </button>
                    <button type="submit" className="btn btn-primary" disabled={saving}>
                      {saving ? "Recording…" : "Complete Sale"}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
          <div className="modal-backdrop show" />
        </>
      )}

      {viewSale && (
        <>
          <div className="modal d-block" tabIndex={-1} role="dialog">
            <div className="modal-dialog" role="document">
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">Invoice {viewSale.invoice_number}</h5>
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => setViewSale(null)}
                    aria-label="Close"
                  />
                </div>
                <div className="modal-body">
                  <p className="text-muted mb-2">
                    Sold to {viewSale.sold_to} on{" "}
                    {new Date(viewSale.sale_date).toLocaleString()}
                  </p>
                  <table className="table table-sm">
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>Qty</th>
                        <th>Unit Price</th>
                        <th>Subtotal</th>
                      </tr>
                    </thead>
                    <tbody>
                      {viewSale.items.map((item) => (
                        <tr key={item.id}>
                          <td>{item.product_name}</td>
                          <td>{item.quantity}</td>
                          <td>{Number(item.unit_price).toFixed(2)}</td>
                          <td>{Number(item.subtotal).toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <div className="text-end fs-5">
                    Total: <strong>{Number(viewSale.total_amount).toFixed(2)}</strong>
                  </div>
                </div>
                <div className="modal-footer">
                  <button className="btn btn-secondary" onClick={() => setViewSale(null)}>
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div className="modal-backdrop show" />
        </>
      )}
    </>
  );
}
