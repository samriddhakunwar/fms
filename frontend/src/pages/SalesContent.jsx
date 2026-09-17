import PageHeader from '../components/PageHeader';

export default function SalesContent() {
  return (
    <>
      <PageHeader title="Sales Records" description="Completed orders are recorded as sales." />
      <section className="simple-card"><h2>Recent Sales</h2><p>Total sales this month: <b>Rs. 1,27,500</b></p><p>Completed orders: <b>8</b></p></section>
    </>
  );
}
