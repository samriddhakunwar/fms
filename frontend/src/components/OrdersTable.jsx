import { orders } from '../data/factoryData';

export default function OrdersTable({ onAdd }) {
  return (
    <section className="simple-card">
      <div className="card-title">
        <h2>Customer Orders</h2>
        <button onClick={onAdd}>Add Order</button>
      </div>

      <table>
        <thead><tr><th>Order ID</th><th>Customer</th><th>Amount</th><th>Status</th></tr></thead>
        <tbody>
          {orders.map((order) => (
            <tr key={order.id}>
              <td>{order.id}</td><td>{order.customer}</td><td>{order.amount}</td>
              <td><span className="status">{order.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
