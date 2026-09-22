import { useEffect, useState } from "react";

import api, { getErrorMessage } from "../services/api";
import { useAuth } from "../context/AuthContext";

/**
 * The signed-in employee's own profile: their login details plus the HR record
 * linked to the account.
 *
 * The record comes from /employees/me/, which resolves it from the session —
 * there is no id in the URL to change, and the employee list and detail routes
 * are closed to this role, so a colleague's profile is not reachable from here
 * by any means.
 */
export default function EmployeeProfile() {
  const { user } = useAuth();

  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get("/employees/me/");
        setRecord(data);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const money = (value) =>
    `Rs ${Number(value).toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;

  return (
    <>
      <h2 className="mb-4">My Profile</h2>

      <div className="row g-3">
        <div className="col-12 col-lg-6">
          <div className="card shadow-sm h-100">
            <div className="card-body">
              <h5 className="mb-3">Account</h5>
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
                  <span
                    className={`badge ${
                      user?.is_active ? "bg-success" : "bg-secondary"
                    }`}
                  >
                    {user?.is_active ? "Active" : "Inactive"}
                  </span>
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="col-12 col-lg-6">
          <div className="card shadow-sm h-100">
            <div className="card-body">
              <h5 className="mb-3">Employment</h5>

              {loading ? (
                <p className="text-muted mb-0">Loading…</p>
              ) : error ? (
                <p className="text-muted mb-0">{error}</p>
              ) : (
                <dl className="row mb-0">
                  <dt className="col-5">Name on record</dt>
                  <dd className="col-7">{record.full_name}</dd>

                  <dt className="col-5">Designation</dt>
                  <dd className="col-7">{record.designation}</dd>

                  <dt className="col-5">Joining Date</dt>
                  <dd className="col-7">
                    {new Date(
                      `${record.joining_date}T00:00:00`
                    ).toLocaleDateString()}
                  </dd>

                  <dt className="col-5">Base Salary</dt>
                  <dd className="col-7">{money(record.salary)}</dd>

                  <dt className="col-5">Phone</dt>
                  <dd className="col-7">{record.phone || "—"}</dd>

                  <dt className="col-5">Address</dt>
                  <dd className="col-7">{record.address || "—"}</dd>

                  <dt className="col-5">Employment Status</dt>
                  <dd className="col-7">
                    <span
                      className={`badge ${
                        record.status === "ACTIVE" ? "bg-success" : "bg-secondary"
                      }`}
                    >
                      {record.status === "ACTIVE" ? "Active" : "Inactive"}
                    </span>
                  </dd>
                </dl>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
