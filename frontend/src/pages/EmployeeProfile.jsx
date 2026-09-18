import { useAuth } from "../context/AuthContext";

export default function EmployeeProfile() {
  const { user } = useAuth();

  return (
    <>
      <h2 className="mb-4">My Profile</h2>
      <div className="card shadow-sm" style={{ maxWidth: "480px" }}>
        <div className="card-body">
          <dl className="row mb-0">
            <dt className="col-5">Username</dt>
            <dd className="col-7">{user?.username}</dd>

            <dt className="col-5">Full Name</dt>
            <dd className="col-7">
              {user?.first_name} {user?.last_name}
            </dd>

            <dt className="col-5">Email</dt>
            <dd className="col-7">{user?.email || "—"}</dd>

            <dt className="col-5">Phone</dt>
            <dd className="col-7">{user?.phone_number || "—"}</dd>

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
