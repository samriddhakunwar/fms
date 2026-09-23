import { useEffect, useState } from "react";
import api, { getErrorMessage } from "../services/api";

const EMPTY_FORM = {
  employee: "",
  amount: "",
  remarks: "",
};

export default function SalaryList() {
  const [payments, setPayments] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const [paymentsRes, employeesRes] = await Promise.all([
        api.get("/salary-payments/"),
        api.get("/employees/"),
      ]);
      setPayments(paymentsRes.data);
      setEmployees(employeesRes.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openAddForm = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setFormErrors({});
    setShowForm(true);
  };

  const openEditForm = (payment) => {
    setEditingId(payment.id);
    setForm({
      employee: payment.employee,
      amount: payment.amount,
      remarks: payment.remarks || "",
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
        await api.put(`/salary-payments/${editingId}/`, form);
      } else {
        await api.post("/salary-payments/", form);
      }
      setShowForm(false);
      await loadData();
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
      await api.delete(`/salary-payments/${deleteTarget.id}/`);
      setDeleteTarget(null);
      await loadData();
    } catch (err) {
      setError(getErrorMessage(err));
      setDeleteTarget(null);
    }
  };

  return (
    <>
      <div className="page-head d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h2 className="mb-0">Salary Payments</h2>
        <button className="btn btn-primary" onClick={openAddForm}>
          + Add Payment
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
              <th>Employee</th>
              <th>Amount</th>
              <th>Remarks</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={4} className="text-center py-4">
                  Loading…
                </td>
              </tr>
            ) : payments.length === 0 ? (
              <tr>
                <td colSpan={4} className="text-center py-4 text-muted">
                  No salary payments recorded.
                </td>
              </tr>
            ) : (
              payments.map((payment) => (
                <tr key={payment.id}>
                  <td>{payment.employee_name}</td>
                  <td>{Number(payment.amount).toFixed(2)}</td>
                  <td>{payment.remarks || "—"}</td>
                  <td className="text-nowrap">
                    <button
                      className="btn btn-sm btn-outline-primary me-2"
                      onClick={() => openEditForm(payment)}
                    >
                      Edit
                    </button>
                    <button
                      className="btn btn-sm btn-outline-danger"
                      onClick={() => setDeleteTarget(payment)}
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
                      {editingId ? "Edit Payment" : "Add Salary Payment"}
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
                      <label className="form-label">Employee</label>
                      <select
                        className="form-select"
                        value={form.employee}
                        onChange={handleFormChange("employee")}
                        required
                      >
                        <option value="" disabled>
                          Select employee…
                        </option>
                        {employees.map((employee) => (
                          <option key={employee.id} value={employee.id}>
                            {employee.full_name}
                          </option>
                        ))}
                      </select>
                      {formErrors.employee && (
                        <div className="text-danger small">{formErrors.employee[0]}</div>
                      )}
                    </div>

                    <div className="mb-3">
                      <label className="form-label">Amount</label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        className="form-control"
                        value={form.amount}
                        onChange={handleFormChange("amount")}
                        required
                      />
                    </div>

                    <div className="mb-3">
                      <label className="form-label">Remarks</label>
                      <textarea
                        className="form-control"
                        rows={2}
                        value={form.remarks}
                        onChange={handleFormChange("remarks")}
                      />
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
                  <h5 className="modal-title">Delete Payment</h5>
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => setDeleteTarget(null)}
                    aria-label="Close"
                  />
                </div>
                <div className="modal-body">
                  Delete the {Number(deleteTarget.amount).toFixed(2)} payment to{" "}
                  <strong>{deleteTarget.employee_name}</strong>?
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
