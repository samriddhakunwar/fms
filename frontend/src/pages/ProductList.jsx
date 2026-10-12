import { useState } from "react";
import { ConfirmModal, FieldError, Modal, SearchInput, StatusRow } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import useLiveList from "../hooks/useLiveList";
import api, { formErrorsFrom, getErrorMessage } from "../services/api";

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
  const { role } = useAuth();
  const canManage = role === "ADMIN" || role === "MANAGER";

  const [search, setSearch] = useState("");
  const {
    items: products,
    loading,
    busy,
    error: listError,
    reload: loadProducts,
    searching,
  } = useLiveList("/products/", search);
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState(null);

  const openForm = (product) => {
    setEditingId(product?.id ?? null);
    setForm(
      product
        ? {
            product_name: product.product_name,
            description: product.description || "",
            sku: product.sku,
            selling_price: product.selling_price,
            quantity_in_stock: product.quantity_in_stock,
            minimum_stock_level: product.minimum_stock_level,
          }
        : EMPTY_FORM
    );
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
      loadProducts();
    } catch (err) {
      setFormErrors(formErrorsFrom(err));
    } finally {
      setSaving(false);
    }
  };

  const confirmDelete = async () => {
    try {
      await api.delete(`/products/${deleteTarget.id}/`);
      setDeleteTarget(null);
      loadProducts();
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
          <button className="btn btn-primary" onClick={() => openForm()}>
            + Add Product
          </button>
        )}
      </div>

      <div className="row g-2 mb-3">
        <div className="col-12 col-sm-auto flex-grow-1" style={{ maxWidth: "360px" }}>
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search products by name or SKU…"
            busy={busy && !loading}
          />
        </div>
      </div>

      {(error || listError) && (
        <div className="alert alert-danger" role="alert">
          {error || listError}
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
            <StatusRow loading={loading} empty={products.length === 0} colSpan={canManage ? 7 : 6}>
              {searching ? "No matching records found." : "No products found."}
            </StatusRow>
            {!loading &&
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
                          onClick={() => openForm(product)}
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
              })}
          </tbody>
        </table>
      </div>

      {showForm && (
        <Modal
          title={editingId ? "Edit Product" : "Add Product"}
          onClose={closeForm}
          onSubmit={handleFormSubmit}
          saving={saving}
          submitLabel={saving ? "Saving…" : "Save"}
        >
          {formErrors.non_field_errors && (
            <div className="alert alert-danger py-2">{formErrors.non_field_errors[0]}</div>
          )}

          <div className="mb-3">
            <label className="form-label">Product Name</label>
            <input
              className="form-control"
              value={form.product_name}
              onChange={handleFormChange("product_name")}
              required
            />
            <FieldError errors={formErrors.product_name} />
          </div>

          <div className="mb-3">
            <label className="form-label">SKU</label>
            <input
              className="form-control"
              value={form.sku}
              onChange={handleFormChange("sku")}
              required
            />
            <FieldError errors={formErrors.sku} />
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
              <FieldError errors={formErrors.selling_price} />
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
        </Modal>
      )}

      {deleteTarget && (
        <ConfirmModal
          title="Delete Product"
          onClose={() => setDeleteTarget(null)}
          onConfirm={confirmDelete}
        >
          Are you sure you want to delete{" "}
          <strong>{deleteTarget.product_name}</strong>? This cannot be undone.
        </ConfirmModal>
      )}
    </>
  );
}
