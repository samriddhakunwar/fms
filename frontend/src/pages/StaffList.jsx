import { useEffect, useState } from "react";
import { ConfirmModal, FieldError, Modal, StatusRow } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import api, { formErrorsFrom, getErrorMessage } from "../services/api";

const EMPTY_FORM = {
  user: "",
  full_name: "",
  email: "",
  phone: "",
  address: "",
  designation: "",
  joining_date: "",
  salary: "",
  status: "ACTIVE",
  login_username: "",
  login_password: "",
};

const NEW_LOGIN = "__new__";

export default function StaffList() {
  const { role } = useAuth();
  const canManage = role === "ADMIN";

  const [staff, setStaff] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const loadStaff = async (params = {}) => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/staff/", { params });
      setStaff(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const loadAccounts = async () => {
    try {
      // Only Staff logins can be linked to a staff record.
      const { data } = await api.get("/users/", { params: { role: "STAFF" } });
      setAccounts(data);
    } catch {
      // Link dropdown just stays empty.
    }
  };

  useEffect(() => {
    loadStaff();
    if (canManage) loadAccounts();
  }, [canManage]);

  const applyFilters = (event) => {
    event.preventDefault();
    const params = {};
    if (search) params.search = search;
    if (statusFilter) params.status = statusFilter;
    loadStaff(params);
  };

  const openForm = (member) => {
    setEditingId(member?.id ?? null);
    setForm(
      member
        ? {
            ...EMPTY_FORM,
            user: member.user ?? "",
            full_name: member.full_name,
            email: member.email || "",
            phone: member.phone || "",
            address: member.address || "",
            designation: member.designation,
            joining_date: member.joining_date,
            salary: member.salary,
            status: member.status,
          }
        : EMPTY_FORM
    );
    setFormErrors({});
    setShowForm(true);
  };

  const handleFormChange = (field) => (event) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleFormSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setFormErrors({});
    const { login_username, login_password, ...record } = form;
    const payload =
      form.user === NEW_LOGIN
        ? { ...record, user: null, login_username, login_password }
        : { ...record, user: form.user === "" ? null : form.user };
    try {
      if (editingId) {
        await api.put(`/staff/${editingId}/`, payload);
      } else {
        await api.post("/staff/", payload);
      }
      setShowForm(false);
      await loadStaff();
      if (form.user === NEW_LOGIN) loadAccounts();
    } catch (err) {
      setFormErrors(formErrorsFrom(err));
    } finally {
      setSaving(false);
    }
  };

  const confirmDelete = async () => {
    try {
      await api.delete(`/staff/${deleteTarget.id}/`);
      setDeleteTarget(null);
      await loadStaff();
    } catch (err) {
      setError(getErrorMessage(err));
      setDeleteTarget(null);
    }
  };

  return (
    <>
      <div className="page-head d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h2 className="mb-0">Staff</h2>
        {canManage && (
          <button className="btn btn-primary" onClick={() => openForm()}>
            + Add Staff
          </button>
        )}
      </div>

      <form className="row g-2 mb-3" onSubmit={applyFilters}>
        <div className="col-auto" style={{ minWidth: "220px" }}>
          <input
            type="search"
            className="form-control"
            placeholder="Search by name…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="col-auto">
          <select
            className="form-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
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

      <div className="table-responsive">
        <table className="table table-hover align-middle bg-white">
          <thead>
            <tr>
              <th>Name</th>
              <th>Designation</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Salary</th>
              <th>Status</th>
              {canManage && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            <StatusRow loading={loading} empty={staff.length === 0} colSpan={canManage ? 7 : 6}>
              No staff found.
            </StatusRow>
            {!loading &&
              staff.map((member) => (
                <tr key={member.id}>
                  <td>{member.full_name}</td>
                  <td>{member.designation}</td>
                  <td>{member.email || "—"}</td>
                  <td>{member.phone || "—"}</td>
                  <td>{Number(member.salary).toFixed(2)}</td>
                  <td>
                    <span
                      className={`badge ${
                        member.status === "ACTIVE" ? "bg-success" : "bg-secondary"
                      }`}
                    >
                      {member.status === "ACTIVE" ? "Active" : "Inactive"}
                    </span>
                  </td>
                  {canManage && (
                    <td className="text-nowrap">
                      <button
                        className="btn btn-sm btn-outline-primary me-2"
                        onClick={() => openForm(member)}
                      >
                        Edit
                      </button>
                      <button
                        className="btn btn-sm btn-outline-danger"
                        onClick={() => setDeleteTarget(member)}
                      >
                        Delete
                      </button>
                    </td>
                  )}
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {showForm && (
        <Modal
          title={editingId ? "Edit Staff" : "Add Staff"}
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
            <label className="form-label">Full Name</label>
            <input
              className="form-control"
              value={form.full_name}
              onChange={handleFormChange("full_name")}
              required
            />
            <FieldError errors={formErrors.full_name} />
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
              <FieldError errors={formErrors.email} />
            </div>
            <div className="col-6 mb-3">
              <label className="form-label">Phone</label>
              <input
                className="form-control"
                value={form.phone}
                onChange={handleFormChange("phone")}
              />
            </div>
          </div>

          <div className="mb-3">
            <label className="form-label">Address</label>
            <textarea
              className="form-control"
              rows={2}
              value={form.address}
              onChange={handleFormChange("address")}
            />
          </div>

          <div className="row">
            <div className="col-6 mb-3">
              <label className="form-label">Designation</label>
              <input
                className="form-control"
                value={form.designation}
                onChange={handleFormChange("designation")}
                required
              />
            </div>
            <div className="col-6 mb-3">
              <label className="form-label">Joining Date</label>
              <input
                type="date"
                className="form-control"
                value={form.joining_date}
                onChange={handleFormChange("joining_date")}
                required
              />
            </div>
          </div>

          <div className="row">
            <div className="col-6 mb-3">
              <label className="form-label">Salary</label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="9999999999.99"
                className="form-control"
                value={form.salary}
                onChange={handleFormChange("salary")}
                required
              />
              <FieldError errors={formErrors.salary} />
            </div>
            <div className="col-6 mb-3">
              <label className="form-label">Status</label>
              <select
                className="form-select"
                value={form.status}
                onChange={handleFormChange("status")}
              >
                <option value="ACTIVE">Active</option>
                <option value="INACTIVE">Inactive</option>
              </select>
            </div>
          </div>

          <div className="mb-3">
            <label className="form-label">Login Account</label>
            <select
              className="form-select"
              value={form.user ?? ""}
              onChange={handleFormChange("user")}
            >
              <option value="">No linked account</option>
              <option value={NEW_LOGIN}>+ Create new login…</option>
              {accounts
                .filter(
                  (account) =>
                    !staff.some(
                      (other) => other.user === account.id && other.id !== editingId
                    )
                )
                .map((account) => (
                  <option value={account.id} key={account.id}>
                    {account.username}
                    {account.first_name || account.last_name
                      ? ` — ${account.first_name} ${account.last_name}`.trimEnd()
                      : ""}
                  </option>
                ))}
            </select>
            <div className="form-text">
              Only Staff logins can be linked. Linking one lets that
              person see this record on their own profile page.
              Optional.
            </div>
            <FieldError errors={formErrors.user} />
          </div>

          {form.user === NEW_LOGIN && (
            <div className="border rounded p-3 mb-3">
              <div className="mb-3">
                <label className="form-label">Username</label>
                <input
                  className="form-control"
                  value={form.login_username}
                  onChange={handleFormChange("login_username")}
                  autoComplete="off"
                  required
                />
                <FieldError errors={formErrors.login_username} />
              </div>
              <label className="form-label">Password</label>
              <input
                type="password"
                className="form-control"
                value={form.login_password}
                onChange={handleFormChange("login_password")}
                autoComplete="new-password"
                required
              />
              <FieldError errors={formErrors.login_password} />
              <div className="form-text">
                Creates a Staff login. Name, email and phone are copied
                from this record.
              </div>
            </div>
          )}
        </Modal>
      )}

      {deleteTarget && (
        <ConfirmModal
          title="Delete Staff"
          onClose={() => setDeleteTarget(null)}
          onConfirm={confirmDelete}
        >
          Are you sure you want to delete{" "}
          <strong>{deleteTarget.full_name}</strong>? This cannot be undone.
        </ConfirmModal>
      )}
    </>
  );
}
