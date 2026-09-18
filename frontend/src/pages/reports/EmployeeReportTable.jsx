import { useEffect, useState } from "react";
import api, { getErrorMessage } from "../../services/api";

export default function EmployeeReportTable() {
  const [employees, setEmployees] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async (status) => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/employees/", {
        params: status ? { status } : {},
      });
      setEmployees(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load("");
  }, []);

  return (
    <>
      <div className="mb-3" style={{ maxWidth: "220px" }}>
        <select
          className="form-select"
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            load(e.target.value);
          }}
        >
          <option value="">All statuses</option>
          <option value="ACTIVE">Active</option>
          <option value="INACTIVE">Inactive</option>
        </select>
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
              <th>Designation</th>
              <th>Status</th>
              <th>Salary</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={4} className="text-center py-4">
                  Loading…
                </td>
              </tr>
            ) : employees.length === 0 ? (
              <tr>
                <td colSpan={4} className="text-center py-4 text-muted">
                  No employees found.
                </td>
              </tr>
            ) : (
              employees.map((employee) => (
                <tr key={employee.id}>
                  <td>{employee.full_name}</td>
                  <td>{employee.designation}</td>
                  <td>
                    <span
                      className={`badge ${
                        employee.status === "ACTIVE" ? "bg-success" : "bg-secondary"
                      }`}
                    >
                      {employee.status === "ACTIVE" ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td>{Number(employee.salary).toFixed(2)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
