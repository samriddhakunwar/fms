import { useEffect, useState } from "react";
import api, { getErrorMessage } from "../services/api";

const EMPTY_FORM = {
  full_name: "",
  email: "",
  phone: "",
  address: "",
  designation: "",
  joining_date: "",
  salary: "",
  status: "ACTIVE",
};

export default function EmployeeList() {
  const [employees, setEmployees] = useState([]);
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

  const loadEmployees = async (params = {}) => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/employees/", { params });
      setEmployees(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEmployees();
  }, []);

  const applyFilters = (event) => {
    event.preventDefault();
    const params = {};
    if (search) params.search = search;
    if (statusFilter) params.status = statusFilter;
    loadEmployees(params);
  };

  const openAddForm = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setFormErrors({});
    setShowForm(true);
  };

  const openEditForm = (employee) => {
    setEditingId(employee.id);
    setForm({
      full_name: employee.full_name,
      email: employee.email || "",
      phone: employee.phone || "",
      address: employee.address || "",
      designation: employee.designation,
      joining_date: employee.joining_date,
      salary: employee.salary,
      status: employee.status,
    });
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
    try {
      if (editingId) {
        await api.put(`/employees/${editingId}/`, form);
      } else {
        await api.post("/employees/", form);
      }
      setShowForm(false);
      await loadEmployees();
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
      await api.delete(`/employees/${deleteTarget.id}/`);
      setDeleteTarget(null);
      await loadEmployees();
    } catch (err) {
      setError(getErrorMessage(err));
      setDeleteTarget(null);
    }
  };

  return (
    <>
      <div className="page-head d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h2 className="mb-0">Employees</h2>
        <button className="btn btn-primary" onClick={openAddForm}>
          + Add Employee
        </button>
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
            ) : employees.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-4 text-muted">
                  No employees found.
                </td>
              </tr>
            ) : (
              employees.map((employee) => (
                <tr key={employee.id}>
                  <td>{employee.full_name}</td>
                  <td>{employee.designation}</td>
                  <td>{employee.email || "—"}</td>
                  <td>{employee.phone || "—"}</td>
                  <td>{Number(employee.salary).toFixed(2)}</td>
                  <td>
                    <span
                      className={`badge ${
                        employee.status === "ACTIVE" ? "bg-success" : "bg-secondary"
                      }`}
                    >
                      {employee.status === "ACTIVE" ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="text-nowrap">
                    <button
                      className="btn btn-sm btn-outline-primary me-2"
                      onClick={() => openEditForm(employee)}
                    >
                      Edit
                    </button>
                    <button
                      className="btn btn-sm btn-outline-danger"
                      onClick={() => setDeleteTarget(employee)}
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
                    <h5 className="modal-title">
                      {editingId ? "Edit Employee" : "Add Employee"}
                    </h5>
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
                      <label className="form-label">Full Name</label>
                      <input
                        className="form-control"
                        value={form.full_name}
                        onChange={handleFormChange("full_name")}
                        required
                      />
                      {formErrors.full_name && (
                        <div className="text-danger small">{formErrors.full_name[0]}</div>
                      )}
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
                        {formErrors.email && (
                          <div className="text-danger small">{formErrors.email[0]}</div>
                        )}
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
                          className="form-control"
                          value={form.salary}
                          onChange={handleFormChange("salary")}
                          required
                        />
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
                  <h5 className="modal-title">Delete Employee</h5>
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => setDeleteTarget(null)}
                    aria-label="Close"
                  />
                </div>
                <div className="modal-body">
                  Are you sure you want to delete{" "}
                  <strong>{deleteTarget.full_name}</strong>? This cannot be undone.
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
