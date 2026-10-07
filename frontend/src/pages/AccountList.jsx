import { useEffect, useState } from "react";
import { ConfirmModal, FieldError, Modal, StatusRow } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import api, { formErrorsFrom, getErrorMessage } from "../services/api";

const EMPTY_FORM = {
  username: "",
  password: "",
  first_name: "",
  last_name: "",
  email: "",
  phone_number: "",
  is_active: true,
};

// Admin and Manager accounts each live in their own table; the endpoint
// decides which one, so the role is never sent from here.
const KINDS = {
  ADMIN: { endpoint: "/admins/", title: "Admins", noun: "Admin" },
  MANAGER: { endpoint: "/managers/", title: "Managers", noun: "Manager" },
};

export default function AccountList({ kind }) {
  const { endpoint, title, noun } = KINDS[kind];
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const loadUsers = async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get(endpoint);
      setUsers(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [endpoint]);

  const openForm = (user) => {
    setEditingId(user?.id ?? null);
    setForm(
      user
        ? {
            username: user.username,
            password: "",
            first_name: user.first_name || "",
            last_name: user.last_name || "",
            email: user.email || "",
            phone_number: user.phone_number || "",
            is_active: user.is_active,
          }
        : EMPTY_FORM
    );
    setFormErrors({});
    setShowForm(true);
  };

  const handleFormChange = (field) => (event) => {
    const value = field === "is_active" ? event.target.value === "true" : event.target.value;
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleFormSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setFormErrors({});

    const payload = { ...form };
    if (editingId && !payload.password) delete payload.password;

    try {
      if (editingId) {
        await api.patch(`${endpoint}${editingId}/`, payload);
      } else {
        await api.post(endpoint, payload);
      }
      setShowForm(false);
      await loadUsers();
    } catch (err) {
      setFormErrors(formErrorsFrom(err));
    } finally {
      setSaving(false);
    }
  };

  const confirmDelete = async () => {
    try {
      await api.delete(`${endpoint}${deleteTarget.id}/`);
      setDeleteTarget(null);
      await loadUsers();
    } catch (err) {
      setError(getErrorMessage(err));
      setDeleteTarget(null);
    }
  };

  return (
    <>
      <div className="page-head d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h2 className="mb-0">{title}</h2>
        <button className="btn btn-primary" onClick={() => openForm()}>
          + Add {noun}
        </button>
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
              <th>Username</th>
              <th>Full Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <StatusRow loading={loading} empty={users.length === 0} colSpan={6}>
              No {title.toLowerCase()} found.
            </StatusRow>
            {!loading &&
              users.map((user) => (
                <tr key={user.id}>
                  <td>{user.username}</td>
                  <td>
                    {user.first_name} {user.last_name}
                  </td>
                  <td>{user.email || "—"}</td>
                  <td>{user.phone_number || "—"}</td>
                  <td>
                    <span className={`badge ${user.is_active ? "bg-success" : "bg-secondary"}`}>
                      {user.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="text-nowrap">
                    <button
                      className="btn btn-sm btn-outline-primary me-2"
                      onClick={() => openForm(user)}
                    >
                      Edit
                    </button>
                    {user.id !== currentUser?.id && (
                      <button
                        className="btn btn-sm btn-outline-danger"
                        onClick={() => setDeleteTarget(user)}
                      >
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {showForm && (
        <Modal
          title={editingId ? `Edit ${noun}` : `Add ${noun}`}
          onClose={() => setShowForm(false)}
          onSubmit={handleFormSubmit}
          saving={saving}
          submitLabel={saving ? "Saving…" : "Save"}
        >
          {formErrors.non_field_errors && (
            <div className="alert alert-danger py-2">
              {formErrors.non_field_errors[0]}
            </div>
          )}

          <div className="mb-3">
            <label className="form-label">Username</label>
            <input
              className="form-control"
              value={form.username}
              onChange={handleFormChange("username")}
              disabled={!!editingId}
              required
            />
            <FieldError errors={formErrors.username} />
          </div>

          <div className="mb-3">
            <label className="form-label">
              Password {editingId && <span className="text-muted">(leave blank to keep current)</span>}
            </label>
            <input
              type="password"
              className="form-control"
              value={form.password}
              onChange={handleFormChange("password")}
              required={!editingId}
            />
            <FieldError errors={formErrors.password} />
          </div>

          <div className="row">
            <div className="col-6 mb-3">
              <label className="form-label">First Name</label>
              <input
                className="form-control"
                value={form.first_name}
                onChange={handleFormChange("first_name")}
              />
            </div>
            <div className="col-6 mb-3">
              <label className="form-label">Last Name</label>
              <input
                className="form-control"
                value={form.last_name}
                onChange={handleFormChange("last_name")}
              />
            </div>
          </div>

          <div className="row">
            <div className="col-6 mb-3">
              <label className="form-label">Email</label>
              <input
                type="email"
                className="form-control"
                value={form.email}
                onChange={handleFormChange("email")}
              />
            </div>
            <div className="col-6 mb-3">
              <label className="form-label">Phone</label>
              <input
                className="form-control"
                value={form.phone_number}
                onChange={handleFormChange("phone_number")}
              />
            </div>
          </div>

          <div className="mb-3">
            <label className="form-label">Status</label>
            <select
              className="form-select"
              value={String(form.is_active)}
              onChange={handleFormChange("is_active")}
            >
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
            <FieldError errors={formErrors.is_active} />
          </div>
        </Modal>
      )}

      {deleteTarget && (
        <ConfirmModal
          title={`Delete ${noun}`}
          onClose={() => setDeleteTarget(null)}
          onConfirm={confirmDelete}
        >
          Are you sure you want to delete{" "}
          <strong>{deleteTarget.username}</strong>? This cannot be undone.
        </ConfirmModal>
      )}
    </>
  );
}
