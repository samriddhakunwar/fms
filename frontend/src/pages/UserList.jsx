import { useEffect, useState } from "react";
import api, { getErrorMessage } from "../services/api";

const EMPTY_FORM = {
  username: "",
  password: "",
  first_name: "",
  last_name: "",
  email: "",
  phone_number: "",
  role: "STAFF",
  is_active: true,
};

const ROLE_LABELS = {
  ADMIN: "Admin",
  INVENTORY_MANAGER: "Inventory Manager",
  STAFF: "Staff",
};

export default function UserList() {
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
      const { data } = await api.get("/users/");
      setUsers(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const openAddForm = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setFormErrors({});
    setShowForm(true);
  };

  const openEditForm = (user) => {
    setEditingId(user.id);
    setForm({
      username: user.username,
      password: "",
      first_name: user.first_name || "",
      last_name: user.last_name || "",
      email: user.email || "",
      phone_number: user.phone_number || "",
      role: user.role,
      is_active: user.is_active,
    });
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
        await api.patch(`/users/${editingId}/`, payload);
      } else {
        await api.post("/users/", payload);
      }
      setShowForm(false);
      await loadUsers();
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
      await api.delete(`/users/${deleteTarget.id}/`);
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
        <h2 className="mb-0">Users</h2>
        <button className="btn btn-primary" onClick={openAddForm}>
          + Add User
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
              <th>Role</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="text-center py-4">
                  Loading…
                </td>
              </tr>
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-4 text-muted">
                  No users found.
                </td>
              </tr>
            ) : (
              users.map((user) => (
                <tr key={user.id}>
                  <td>{user.username}</td>
                  <td>
                    {user.first_name} {user.last_name}
                  </td>
                  <td>{user.email || "—"}</td>
                  <td>{ROLE_LABELS[user.role] || user.role}</td>
                  <td>
                    <span className={`badge ${user.is_active ? "bg-success" : "bg-secondary"}`}>
                      {user.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="text-nowrap">
                    <button
                      className="btn btn-sm btn-outline-primary me-2"
                      onClick={() => openEditForm(user)}
                    >
                      Edit
                    </button>
                    <button
                      className="btn btn-sm btn-outline-danger"
                      onClick={() => setDeleteTarget(user)}
                    >
                      Delete
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
            <div className="modal-dialog" role="document">
              <div className="modal-content">
                <form onSubmit={handleFormSubmit}>
                  <div className="modal-header">
                    <h5 className="modal-title">{editingId ? "Edit User" : "Add User"}</h5>
                    <button
                      type="button"
                      className="btn-close"
                      onClick={() => setShowForm(false)}
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
                      <label className="form-label">Username</label>
                      <input
                        className="form-control"
                        value={form.username}
                        onChange={handleFormChange("username")}
                        disabled={!!editingId}
                        required
                      />
                      {formErrors.username && (
                        <div className="text-danger small">{formErrors.username[0]}</div>
                      )}
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
                      {formErrors.password && (
                        <div className="text-danger small">{formErrors.password[0]}</div>
                      )}
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

                    <div className="row">
                      <div className="col-6 mb-3">
                        <label className="form-label">Role</label>
                        <select
                          className="form-select"
                          value={form.role}
                          onChange={handleFormChange("role")}
                        >
                          <option value="ADMIN">Admin</option>
                          <option value="INVENTORY_MANAGER">Inventory Manager</option>
                          <option value="STAFF">Staff</option>
                        </select>
                      </div>
                      <div className="col-6 mb-3">
                        <label className="form-label">Status</label>
                        <select
                          className="form-select"
                          value={String(form.is_active)}
                          onChange={handleFormChange("is_active")}
                        >
                          <option value="true">Active</option>
                          <option value="false">Inactive</option>
                        </select>
                      </div>
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
                  <h5 className="modal-title">Delete User</h5>
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => setDeleteTarget(null)}
                    aria-label="Close"
                  />
                </div>
                <div className="modal-body">
                  Are you sure you want to delete{" "}
                  <strong>{deleteTarget.username}</strong>? This cannot be undone.
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
