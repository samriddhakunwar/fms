import { useEffect, useState } from "react";
import api, { getErrorMessage } from "../../services/api";

export default function SalesReportTable() {
  const [sales, setSales] = useState([]);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async (params = {}) => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/sales/", { params });
      setSales(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const applyFilters = (event) => {
    event.preventDefault();
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    load(params);
  };

  return (
    <>
      <form className="row g-2 mb-3" onSubmit={applyFilters}>
        <div className="col-auto">
          <input
            type="date"
            className="form-control"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>
        <div className="col-auto">
          <input
            type="date"
            className="form-control"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
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
              <th>Invoice Number</th>
              <th>Sold By</th>
              <th>Total Amount</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={4} className="text-center py-4">
                  Loading…
                </td>
              </tr>
            ) : sales.length === 0 ? (
              <tr>
                <td colSpan={4} className="text-center py-4 text-muted">
                  No sales found.
                </td>
              </tr>
            ) : (
              sales.map((sale) => (
                <tr key={sale.id}>
                  <td>{sale.invoice_number}</td>
                  <td>{sale.sold_by_username}</td>
                  <td>{Number(sale.total_amount).toFixed(2)}</td>
                  <td>{new Date(sale.sale_date).toLocaleDateString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
