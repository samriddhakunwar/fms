import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api, { getErrorMessage } from "../services/api";

const EMPTY_FORM = {
  product_name: "",
  description: "",
  sku: "",
  selling_price: "",
  quantity_in_stock: "",
  minimum_stock_level: "",
};

const STATUS_BADGE = {
  IN_STOCK: { label: "In Stock", className: "bg-success" },
  LOW_STOCK: { label: "⚠ Low Stock", className: "bg-warning text-dark" },
  OUT_OF_STOCK: { label: "Out of Stock", className: "bg-danger" },
};

export default function ProductList() {
  // Employees reach this page read-only. The API enforces that too — this
  // just stops the UI offering actions that would be rejected.
  const { role } = useAuth();
  const canManage = role === "ADMIN" || role === "INVENTORY_MANAGER";

  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState(null);

  const loadProducts = async (searchTerm = "") => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/products/", {
        params: searchTerm ? { search: searchTerm } : {},
      });
      setProducts(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    loadProducts(search);
  };

  const openAddForm = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setFormErrors({});
    setShowForm(true);
  };

  const openEditForm = (product) => {
    setEditingId(product.id);
    setForm({
      product_name: product.product_name,
      description: product.description || "",
      sku: product.sku,
      selling_price: product.selling_price,
      quantity_in_stock: product.quantity_in_stock,
      minimum_stock_level: product.minimum_stock_level,
    });
    setFormErrors({});
    setShowForm(true);
  };

  const closeForm = () => setShowForm(false);

  const handleFormChange = (field) => (event) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleFormSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setFormErrors({});

    try {
      if (editingId) {
        await api.put(`/products/${editingId}/`, form);
      } else {
        await api.post("/products/", form);
      }
      setShowForm(false);
      await loadProducts(search);
    } catch (err) {
      if (err.response?.status === 400 && err.response.data) {
        setFormErrors(err.response.data);
      } else {
        setFormErrors({ non_field_errors: [getErrorMessage(err)] });
      }
    } finally {
      setSaving(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await api.delete(`/products/${deleteTarget.id}/`);
      setDeleteTarget(null);
      await loadProducts(search);
    } catch (err) {
      setError(getErrorMessage(err));
      setDeleteTarget(null);
    }
  };

  return (
    <>
      <div className="page-head d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h2 className="mb-0">Inventory</h2>
        {canManage && (
          <button className="btn btn-primary" onClick={openAddForm}>
            + Add Product
          </button>
        )}
      </div>

      <form className="row g-2 mb-3" onSubmit={handleSearchSubmit}>
        <div className="col-auto flex-grow-1" style={{ maxWidth: "320px" }}>
          <input
            type="search"
            className="form-control"
            placeholder="Search by name or SKU…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="col-auto">
          <button type="submit" className="btn btn-outline-secondary">
            Search
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
              <th>Product Name</th>
              <th>SKU</th>
              <th>Selling Price</th>
              <th>Stock</th>
              <th>Minimum Stock</th>
              <th>Status</th>
              {canManage && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={canManage ? 7 : 6} className="text-center py-4">
                  Loading…
                </td>
              </tr>
            ) : products.length === 0 ? (
              <tr>
                <td colSpan={canManage ? 7 : 6} className="text-center py-4 text-muted">
                  No products found.
                </td>
              </tr>
            ) : (
              products.map((product) => {
                const badge = STATUS_BADGE[product.stock_status] || STATUS_BADGE.IN_STOCK;
                return (
                  <tr key={product.id}>
                    <td>{product.product_name}</td>
                    <td>{product.sku}</td>
                    <td>{Number(product.selling_price).toFixed(2)}</td>
                    <td>{product.quantity_in_stock}</td>
                    <td>{product.minimum_stock_level}</td>
                    <td>
                      <span className={`badge ${badge.className}`}>{badge.label}</span>
                    </td>
                    {canManage && (
                      <td className="text-nowrap">
                        <button
                          className="btn btn-sm btn-outline-primary me-2"
                          onClick={() => openEditForm(product)}
                        >
                          Edit
                        </button>
                        <button
                          className="btn btn-sm btn-outline-danger"
                          onClick={() => setDeleteTarget(product)}
                        >
                          Delete
                        </button>
                      </td>
                    )}
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
            <div className="modal-dialog" role="document">
              <div className="modal-content">
                <form onSubmit={handleFormSubmit}>
                  <div className="modal-header">
                    <h5 className="modal-title">
                      {editingId ? "Edit Product" : "Add Product"}
                    </h5>
                    <button
                      type="button"
                      className="btn-close"
                      onClick={closeForm}
                      aria-label="Close"
                    />
                  </div>
                  <div className="modal-body">
                    {formErrors.non_field_errors && (
                      <div className="alert alert-danger py-2">
                        {formErrors.non_field_errors[0]}
                      </div>
                    )}

                    <div className="mb-3">
                      <label className="form-label">Product Name</label>
                      <input
                        className="form-control"
                        value={form.product_name}
                        onChange={handleFormChange("product_name")}
                        required
                      />
                      {formErrors.product_name && (
                        <div className="text-danger small">{formErrors.product_name[0]}</div>
                      )}
                    </div>

                    <div className="mb-3">
                      <label className="form-label">SKU</label>
                      <input
                        className="form-control"
                        value={form.sku}
                        onChange={handleFormChange("sku")}
                        required
                      />
                      {formErrors.sku && (
                        <div className="text-danger small">{formErrors.sku[0]}</div>
                      )}
                    </div>

                    <div className="mb-3">
                      <label className="form-label">Description</label>
                      <textarea
                        className="form-control"
                        rows={2}
                        value={form.description}
                        onChange={handleFormChange("description")}
                      />
                    </div>

                    <div className="row">
                      <div className="col-4 mb-3">
                        <label className="form-label">Selling Price</label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          className="form-control"
                          value={form.selling_price}
                          onChange={handleFormChange("selling_price")}
                          required
                        />
                        {formErrors.selling_price && (
                          <div className="text-danger small">
                            {formErrors.selling_price[0]}
                          </div>
                        )}
                      </div>
                      <div className="col-4 mb-3">
                        <label className="form-label">Stock Qty</label>
                        <input
                          type="number"
                          min="0"
                          className="form-control"
                          value={form.quantity_in_stock}
                          onChange={handleFormChange("quantity_in_stock")}
                          required
                        />
                      </div>
                      <div className="col-4 mb-3">
                        <label className="form-label">Min Stock</label>
                        <input
                          type="number"
                          min="0"
                          className="form-control"
                          value={form.minimum_stock_level}
                          onChange={handleFormChange("minimum_stock_level")}
                          required
                        />
                      </div>
                    </div>
                  </div>
                  <div className="modal-footer">
                    <button type="button" className="btn btn-secondary" onClick={closeForm}>
                      Cancel
                    </button>
                    <button type="submit" className="btn btn-primary" disabled={saving}>
                      {saving ? "Saving…" : "Save"}
                    </button>
                  </div>
                </form>
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
                  <h5 className="modal-title">Delete Product</h5>
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => setDeleteTarget(null)}
                    aria-label="Close"
                  />
                </div>
                <div className="modal-body">
                  Are you sure you want to delete{" "}
                  <strong>{deleteTarget.product_name}</strong>? This cannot be undone.
                </div>
                <div className="modal-footer">
                  <button
                    className="btn btn-secondary"
                    onClick={() => setDeleteTarget(null)}
                  >
                    Cancel
                  </button>
                  <button className="btn btn-danger" onClick={confirmDelete}>
                    Delete
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
