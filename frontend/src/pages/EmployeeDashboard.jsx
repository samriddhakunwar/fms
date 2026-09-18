import { useAuth } from "../context/AuthContext";

export default function EmployeeDashboard() {
  const { user } = useAuth();

  return (
    <>
      <h2 className="mb-4">Employee Dashboard</h2>
      <div className="card shadow-sm" style={{ maxWidth: "480px" }}>
        <div className="card-body">
          <h5 className="card-title">
            {user?.first_name} {user?.last_name}
          </h5>
          <dl className="row mb-0 mt-3">
            <dt className="col-5">Email</dt>
            <dd className="col-7">{user?.email || "—"}</dd>

            <dt className="col-5">Status</dt>
            <dd className="col-7">
              <span className={`badge ${user?.is_active ? "bg-success" : "bg-secondary"}`}>
                {user?.is_active ? "Active" : "Inactive"}
              </span>
            </dd>
          </dl>
        </div>
      </div>
    </>
  );
}
