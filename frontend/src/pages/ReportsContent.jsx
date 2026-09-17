import PageHeader from '../components/PageHeader';

export default function ReportsContent({ onDownload }) {
  return (
    <>
      <PageHeader title="Sales Reports" description="Simple sales summary for August 2026." />
      <section className="simple-card"><h2>Monthly Sales Report</h2><div className="report-box"><p>Total Sales</p><strong>Rs. 1,27,500</strong><p>Number of completed orders: 8</p><button onClick={onDownload}>Download Report</button></div></section>
    </>
  );
}
