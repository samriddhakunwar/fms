import { useState } from "react";

import SalesReport from "./reports/SalesReport";
import { SearchInput, StatusRow } from "../components/ui";
import api, { getErrorMessage } from "../services/api";

const MAX_DAYS = 180;

const formatCell = (value, type) => {
  if (value === null || value === "") return "—";
  if (type === "money")
    return `Rs ${Number(value).toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  if (type === "int") return Number(value).toLocaleString();
  return value;
};

function validateRange(start, end) {
  if (!start || !end) return "Choose both a start date and an end date.";
  if (start > end) return "The start date cannot be after the end date.";
  const days = (new Date(end) - new Date(start)) / 86400000 + 1;
  if (days > MAX_DAYS) return `Choose a range of at most ${MAX_DAYS} days.`;
  return "";
}

/** Error text from a failed blob download, whose JSON body arrives as a Blob. */
async function downloadErrorMessage(err) {
  const data = err.response?.data;
  if (data instanceof Blob) {
    try {
      const parsed = JSON.parse(await data.text());
      if (parsed.detail) return parsed.detail;
    } catch {
      // Not JSON; fall through to the generic message.
    }
  }
  return getErrorMessage(err);
}

export default function ReportsPage() {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  // The filters the report on screen was generated with; downloads use exactly these.
  const [generated, setGenerated] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState("");
  const [error, setError] = useState("");
  // Narrows the rows on screen only; the downloads always contain the full report.
  const [rowSearch, setRowSearch] = useState("");
  const term = rowSearch.trim().toLowerCase();
  const visibleRows = !report
    ? []
    : term
      ? report.rows.filter((row) =>
          row.some((value) => String(value ?? "").toLowerCase().startsWith(term))
        )
      : report.rows;

  const stale =
    !generated ||
    generated.start_date !== startDate ||
    generated.end_date !== endDate;
  const canDownload = !stale && report && !loading && !downloading;

  const generate = async (event) => {
    event.preventDefault();
    const problem = validateRange(startDate, endDate);
    if (problem) {
      setError(problem);
      return;
    }
    const filters = { start_date: startDate, end_date: endDate };
    setLoading(true);
    setError("");
    setReport(null);
    setGenerated(null);
    try {
      const { data } = await api.get("/reports/sales/records/", {
        params: { start_date: startDate, end_date: endDate },
      });
      setReport(data);
      setGenerated(filters);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const download = async (format) => {
    if (!canDownload) return;
    setDownloading(format);
    setError("");
    try {
      const response = await api.get("/reports/sales/records/", {
        params: {
          start_date: generated.start_date,
          end_date: generated.end_date,
          export: format,
        },
        responseType: "blob",
      });
      const match = /filename="([^"]+)"/.exec(
        response.headers["content-disposition"] || ""
      );
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = match
        ? match[1]
        : `${report.title.replace(/ /g, "_")}_${generated.start_date}_to_${generated.end_date}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(await downloadErrorMessage(err));
    } finally {
      setDownloading("");
    }
  };

  return (
    <>
      <h2 className="mb-4">Reports</h2>

      <ul className="nav nav-tabs mb-3">
        <li className="nav-item">
          <button className="nav-link active">Sales Report</button>
        </li>
      </ul>

      <form className="row g-2 mb-3 align-items-end" onSubmit={generate}>
        <div className="col-6 col-md-auto">
          <label className="form-label small mb-1" htmlFor="report-start">
            Start date
          </label>
          <input
            id="report-start"
            type="date"
            className="form-control"
            value={startDate}
            max={endDate || undefined}
            onChange={(e) => setStartDate(e.target.value)}
            required
          />
        </div>
        <div className="col-6 col-md-auto">
          <label className="form-label small mb-1" htmlFor="report-end">
            End date
          </label>
          <input
            id="report-end"
            type="date"
            className="form-control"
            value={endDate}
            min={startDate || undefined}
            onChange={(e) => setEndDate(e.target.value)}
            required
          />
        </div>
        <div className="col-12 col-md-auto">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading && <span className="spinner-border spinner-border-sm me-2" />}
            Generate Report
          </button>
        </div>
        <div className="col-12 col-md-auto">
          <div className="btn-group">
            <button
              type="button"
              className="btn btn-outline-secondary"
              disabled={!canDownload}
              onClick={() => download("pdf")}
            >
              {downloading === "pdf" ? "Downloading…" : "Download PDF"}
            </button>
            <button
              type="button"
              className="btn btn-outline-secondary"
              disabled={!canDownload}
              onClick={() => download("xlsx")}
            >
              {downloading === "xlsx" ? "Downloading…" : "Download Excel"}
            </button>
          </div>
        </div>
      </form>

      {report && stale && (
        <div className="alert alert-info py-2">
          The dates have changed since this report was generated. Generate the
          report again to download it.
        </div>
      )}

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      {!report && !loading && !error && (
        <p className="text-muted">
          Choose a start and end date, then generate the report.
        </p>
      )}

      {generated && (
        <SalesReport startDate={generated.start_date} endDate={generated.end_date} />
      )}

      {(report || loading) && (
        <div className="card shadow-sm mt-3">
          <div className="card-body">
            <h5 className="mb-0">{report?.title ?? "Loading…"}</h5>
            {report && (
              <>
                <p className="text-muted small mb-1">
                  {report.start_date} to {report.end_date} · generated{" "}
                  {new Date(report.generated_at).toLocaleString()}
                </p>
                <p className="text-muted small fst-italic">{report.note}</p>

                <div className="row g-2 mb-3">
                  {report.summary.map((entry) => (
                    <div className="col-6 col-lg-3 col-xl-2" key={entry.label}>
                      <div className="border rounded p-2 h-100">
                        <div className="fw-semibold">
                          {formatCell(entry.value, entry.type)}
                        </div>
                        <div className="text-muted small">{entry.label}</div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mb-3" style={{ maxWidth: "360px" }}>
                  <SearchInput
                    value={rowSearch}
                    onChange={setRowSearch}
                    placeholder="Search rows by invoice, customer, product or SKU…"
                  />
                </div>
              </>
            )}

            <div className="table-responsive">
              <table className="table table-hover table-sm align-middle mb-0">
                <thead>
                  <tr>
                    {report?.columns.map((column) => (
                      <th
                        key={column.label}
                        className={column.type === "money" || column.type === "int" ? "text-end" : ""}
                      >
                        {column.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <StatusRow
                    loading={loading}
                    empty={visibleRows.length === 0}
                    colSpan={report?.columns.length || 1}
                  >
                    {report?.rows.length && term
                      ? "No matching records found."
                      : "No records found for the selected date range."}
                  </StatusRow>
                  {!loading &&
                    visibleRows.map((row, index) => (
                      <tr key={index}>
                        {row.map((value, column) => {
                          const { type } = report.columns[column];
                          return (
                            <td
                              key={column}
                              className={type === "money" || type === "int" ? "text-end" : ""}
                            >
                              {formatCell(value, type)}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
