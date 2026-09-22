import { useEffect, useState } from "react";
import api, { getErrorMessage } from "../services/api";
import { useAuth } from "../context/AuthContext";

/**
 * Customer orders — what was asked for, before anything leaves the factory.
 *
 * An order is not a sale: it moves no stock. Fulfilling one (Admin only)
 * raises the invoice and deducts the stock in a single server-side step.
 *
 * Admin gets full CRUD plus fulfilment. Inventory Manager may raise, view and
 * delete orders but not amend them — the API refuses a manager's PUT/PATCH, so
 * hiding the Edit button here only saves them a pointless round trip.
 */

const STATUS_BADGE = {
  PENDING: { label: "Pending", className: "bg-secondary" },
  CONFIRMED: { label: "Confirmed", className: "bg-primary" },
  FULFILLED: { label: "Fulfilled", className: "bg-success" },
  CANCELLED: { label: "Cancelled", className: "bg-danger" },
};

const STATUS_OPTIONS = ["PENDING", "CONFIRMED", "CANCELLED"];

function emptyLine() {
  return { product: "", quantity: 1 };
}

export default function OrdersPage() {
  const { role } = useAuth();
  const isAdmin = role === "ADMIN";

  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [customerName, setCustomerName] = useState("");
  const [expectedDate, setExpectedDate] = useState("");
  const [orderStatus, setOrderStatus] = useState("PENDING");
  const [notes, setNotes] = useState("");
  const [lines, setLines] = useState([emptyLine()]);
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  const [viewOrder, setViewOrder] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [fulfilTarget, setFulfilTarget] = useState(null);
  const [working, setWorking] = useState(false);

  const loadOrders = async (params = {}) => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/orders/", { params });
      setOrders(data);
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
      // The product dropdown just stays empty; the table shows any error.
    }
  };

  useEffect(() => {
    loadOrders();
    loadProducts();
  }, []);

  const applyFilters = (event) => {
    event.preventDefault();
    const params = {};
    if (search) params.search = search;
    if (statusFilter) params.status = statusFilter;
    loadOrders(params);
  };

  const openAddForm = () => {
    setEditingId(null);
    setCustomerName("");
    setExpectedDate("");
    setOrderStatus("PENDING");
    setNotes("");
    setLines([emptyLine()]);
    setFormError("");
    setShowForm(true);
  };

  const openEditForm = (order) => {
    setEditingId(order.id);
    setCustomerName(order.customer_name);
    setExpectedDate(order.expected_delivery_date || "");
    setOrderStatus(order.status);
    setNotes(order.notes || "");
    setLines(
      order.items.length
        ? order.items.map((item) => ({
            product: String(item.product),
            quantity: item.quantity,
          }))
        : [emptyLine()]
    );
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

    if (!customerName.trim()) {
      setFormError("Enter the customer this order is for.");
      return;
    }

    const validLines = lines.filter(
      (line) => line.product && Number(line.quantity) > 0
    );
    if (validLines.length === 0) {
      setFormError("Add at least one product line.");
      return;
    }

    const payload = {
      customer_name: customerName.trim(),
      status: orderStatus,
      notes,
      expected_delivery_date: expectedDate || null,
      items_input: validLines.map((line) => ({
        product: Number(line.product),
        quantity: Number(line.quantity),
      })),
    };

    setSaving(true);
    try {
      if (editingId) {
        await api.put(`/orders/${editingId}/`, payload);
      } else {
        await api.post("/orders/", payload);
      }
      setShowForm(false);
      await loadOrders();
    } catch (err) {
      setFormError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setWorking(true);
    try {
      await api.delete(`/orders/${deleteTarget.id}/`);
      setDeleteTarget(null);
      await loadOrders();
    } catch (err) {
      setError(getErrorMessage(err));
      setDeleteTarget(null);
    } finally {
      setWorking(false);
    }
  };

  const confirmFulfil = async () => {
    if (!fulfilTarget) return;
    setWorking(true);
    setError("");
    try {
      const { data } = await api.post(`/orders/${fulfilTarget.id}/fulfil/`);
      setFulfilTarget(null);
      setNotice(
        `Order ${fulfilTarget.order_number} fulfilled — invoice ${data.invoice_number} raised and stock deducted.`
      );
      await loadOrders();
    } catch (err) {
      setError(getErrorMessage(err));
      setFulfilTarget(null);
    } finally {
      setWorking(false);
    }
  };

  return (
    <>
      <div className="page-head d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h2 className="mb-0">Orders</h2>
        <button className="btn btn-primary" onClick={openAddForm}>
          + New Order
        </button>
      </div>

      <form className="row g-2 mb-3" onSubmit={applyFilters}>
        <div className="col-auto" style={{ minWidth: "220px" }}>
          <input
            type="search"
            className="form-control"
            placeholder="Search order number or customer…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="col-auto">
          <select
            className="form-select"
            aria-label="Status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All statuses</option>
            {Object.entries(STATUS_BADGE).map(([value, { label }]) => (
              <option value={value} key={value}>
                {label}
              </option>
            ))}
          </select>
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

      {notice && (
        <div className="alert alert-success d-flex justify-content-between" role="alert">
          <span>{notice}</span>
          <button
            type="button"
            className="btn-close"
            aria-label="Dismiss"
            onClick={() => setNotice("")}
          />
        </div>
      )}

      <div className="table-responsive">
        <table className="table table-hover align-middle bg-white">
          <thead>
            <tr>
              <th>Order Number</th>
              <th>Customer</th>
              <th>Status</th>
              <th>Total Amount</th>
              <th>Ordered</th>
              <th>Invoice</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="text-center py-4">
                  Loading…
                </td>
              </tr>
            ) : orders.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-4 text-muted">
                  No orders found.
                </td>
              </tr>
            ) : (
              orders.map((order) => {
                const badge = STATUS_BADGE[order.status] || STATUS_BADGE.PENDING;
                const open =
                  order.status === "PENDING" || order.status === "CONFIRMED";
                return (
                  <tr key={order.id}>
                    <td>{order.order_number}</td>
                    <td>{order.customer_name}</td>
                    <td>
                      <span className={`badge ${badge.className}`}>
                        {badge.label}
                      </span>
                    </td>
                    <td>{Number(order.total_amount).toFixed(2)}</td>
                    <td>{new Date(order.order_date).toLocaleDateString()}</td>
                    <td className="text-muted">{order.invoice_number || "—"}</td>
                    <td className="text-nowrap">
                      <button
                        className="btn btn-sm btn-outline-secondary me-2"
                        onClick={() => setViewOrder(order)}
                      >
                        View
                      </button>
                      {isAdmin && open && (
                        <button
                          className="btn btn-sm btn-outline-primary me-2"
                          onClick={() => openEditForm(order)}
                        >
                          Edit
                        </button>
                      )}
                      {isAdmin && open && (
                        <button
                          className="btn btn-sm btn-outline-success me-2"
                          onClick={() => setFulfilTarget(order)}
                        >
                          Fulfil
                        </button>
                      )}
                      {order.status !== "FULFILLED" && (
                        <button
                          className="btn btn-sm btn-outline-danger"
                          onClick={() => setDeleteTarget(order)}
                        >
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })
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
                    <h5 className="modal-title">
                      {editingId ? "Edit Order" : "New Order"}
                    </h5>
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

                    <div className="row">
                      <div className="col-12 col-md-5 mb-3">
                        <label className="form-label" htmlFor="customer-name">
                          Customer
                        </label>
                        <input
                          id="customer-name"
                          className="form-control"
                          value={customerName}
                          onChange={(e) => setCustomerName(e.target.value)}
                          required
                        />
                      </div>
                      <div className="col-6 col-md-4 mb-3">
                        <label className="form-label" htmlFor="expected-date">
                          Expected Delivery
                        </label>
                        <input
                          id="expected-date"
                          type="date"
                          className="form-control"
                          value={expectedDate}
                          onChange={(e) => setExpectedDate(e.target.value)}
                        />
                      </div>
                      <div className="col-6 col-md-3 mb-3">
                        <label className="form-label" htmlFor="order-status">
                          Status
                        </label>
                        <select
                          id="order-status"
                          className="form-select"
                          value={orderStatus}
                          onChange={(e) => setOrderStatus(e.target.value)}
                        >
                          {STATUS_OPTIONS.map((value) => (
                            <option value={value} key={value}>
                              {STATUS_BADGE[value].label}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <table className="table table-sm align-middle">
                      <thead>
                        <tr>
                          <th style={{ width: "55%" }}>Product</th>
                          <th>Quantity</th>
                          <th>Subtotal</th>
                          <th />
                        </tr>
                      </thead>
                      <tbody>
                        {lines.map((line, index) => (
                          <tr key={index}>
                            <td>
                              <select
                                className="form-select"
                                aria-label="Product"
                                value={line.product}
                                onChange={(e) =>
                                  updateLine(index, "product", e.target.value)
                                }
                              >
                                <option value="">Select a product…</option>
                                {products
                                  .filter((product) => product.is_active)
                                  .map((product) => (
                                    <option value={product.id} key={product.id}>
                                      {product.product_name} ({product.sku}) —{" "}
                                      {product.quantity_in_stock} in stock
                                    </option>
                                  ))}
                              </select>
                            </td>
                            <td style={{ width: "120px" }}>
                              <input
                                type="number"
                                min="1"
                                className="form-control"
                                aria-label="Quantity"
                                value={line.quantity}
                                onChange={(e) =>
                                  updateLine(index, "quantity", e.target.value)
                                }
                              />
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
                        ))}
                      </tbody>
                    </table>

                    <button
                      type="button"
                      className="btn btn-sm btn-outline-secondary"
                      onClick={addLine}
                    >
                      + Add Line
                    </button>

                    <div className="mt-3">
                      <label className="form-label" htmlFor="order-notes">
                        Notes
                      </label>
                      <textarea
                        id="order-notes"
                        className="form-control"
                        rows={2}
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                      />
                    </div>

                    <div className="text-end mt-3 fs-5">
                      Total: <strong>{total.toFixed(2)}</strong>
                    </div>
                    <p className="text-muted small text-end mb-0">
                      Ordering does not move stock — that happens when the order
                      is fulfilled.
                    </p>
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
                      {saving ? "Saving…" : editingId ? "Save Changes" : "Place Order"}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
          <div className="modal-backdrop show" />
        </>
      )}

      {viewOrder && (
        <>
          <div className="modal d-block" tabIndex={-1} role="dialog">
            <div className="modal-dialog" role="document">
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">Order {viewOrder.order_number}</h5>
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => setViewOrder(null)}
                    aria-label="Close"
                  />
                </div>
                <div className="modal-body">
                  <p className="text-muted mb-2">
                    {viewOrder.customer_name} · placed{" "}
                    {new Date(viewOrder.order_date).toLocaleString()}
                    {viewOrder.expected_delivery_date &&
                      ` · expected ${new Date(
                        `${viewOrder.expected_delivery_date}T00:00:00`
                      ).toLocaleDateString()}`}
                  </p>
                  {viewOrder.invoice_number && (
                    <p className="mb-2">
                      Invoiced as <strong>{viewOrder.invoice_number}</strong>
                    </p>
                  )}
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
                      {viewOrder.items.map((item) => (
                        <tr key={item.id}>
                          <td>{item.product_name}</td>
                          <td>{item.quantity}</td>
                          <td>{Number(item.unit_price).toFixed(2)}</td>
                          <td>{Number(item.subtotal).toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {viewOrder.notes && (
                    <p className="text-muted small mb-2">{viewOrder.notes}</p>
                  )}
                  <div className="text-end fs-5">
                    Total:{" "}
                    <strong>{Number(viewOrder.total_amount).toFixed(2)}</strong>
                  </div>
                </div>
                <div className="modal-footer">
                  <button
                    className="btn btn-secondary"
                    onClick={() => setViewOrder(null)}
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div className="modal-backdrop show" />
        </>
      )}

      {fulfilTarget && (
        <>
          <div className="modal d-block" tabIndex={-1} role="dialog">
            <div className="modal-dialog" role="document">
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">Fulfil Order</h5>
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => setFulfilTarget(null)}
                    aria-label="Close"
                  />
                </div>
                <div className="modal-body">
                  Raise an invoice for <strong>{fulfilTarget.order_number}</strong>{" "}
                  and deduct its {fulfilTarget.items.length} line
                  {fulfilTarget.items.length === 1 ? "" : "s"} from stock? The
                  order is then closed to further edits.
                </div>
                <div className="modal-footer">
                  <button
                    className="btn btn-secondary"
                    onClick={() => setFulfilTarget(null)}
                  >
                    Cancel
                  </button>
                  <button
                    className="btn btn-success"
                    onClick={confirmFulfil}
                    disabled={working}
                  >
                    {working ? "Fulfilling…" : "Fulfil & Invoice"}
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div className="modal-backdrop show" />
        </>
      )}

      {deleteTarget && (
        <>
          <div className="modal d-block" tabIndex={-1} role="dialog">
            <div className="modal-dialog" role="document">
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">Delete Order</h5>
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => setDeleteTarget(null)}
                    aria-label="Close"
                  />
                </div>
                <div className="modal-body">
                  Are you sure you want to delete{" "}
                  <strong>{deleteTarget.order_number}</strong> for{" "}
                  {deleteTarget.customer_name}? This cannot be undone.
                </div>
                <div className="modal-footer">
                  <button
                    className="btn btn-secondary"
                    onClick={() => setDeleteTarget(null)}
                  >
                    Cancel
                  </button>
                  <button
                    className="btn btn-danger"
                    onClick={confirmDelete}
                    disabled={working}
                  >
                    {working ? "Deleting…" : "Delete"}
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
