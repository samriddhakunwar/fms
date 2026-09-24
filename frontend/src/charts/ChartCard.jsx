export default function ChartCard({
  title,
  subtitle,
  loading,
  error,
  empty,
  emptyMessage,
  children,
}) {
  return (
    <div className="card shadow-sm h-100">
      <div className="card-body d-flex flex-column">
        <div className="mb-3">
          <h5 className="mb-0">{title}</h5>
          {subtitle && <p className="text-muted small mb-0">{subtitle}</p>}
        </div>

        <div className="flex-grow-1 d-flex align-items-center justify-content-center">
          {loading ? (
            <span className="text-muted small">Loading…</span>
          ) : error ? (
            <span className="text-muted small">{error}</span>
          ) : empty ? (
            <span className="text-muted small">
              {emptyMessage ?? "No data to chart yet."}
            </span>
          ) : (
            <div className="w-100">{children}</div>
          )}
        </div>
      </div>
    </div>
  );
}
