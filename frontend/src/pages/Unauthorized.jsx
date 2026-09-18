import { Link } from "react-router-dom";

export default function Unauthorized() {
  return (
    <div className="d-flex flex-column justify-content-center align-items-center vh-100 text-center px-3">
      <h1 className="display-6">403 — Access Denied</h1>
      <p className="text-muted">You do not have permission to view this page.</p>
      <Link to="/login" className="btn btn-primary mt-2">
        Back to Login
      </Link>
    </div>
  );
}
