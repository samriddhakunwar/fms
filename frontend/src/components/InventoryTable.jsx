import { inventory } from '../data/factoryData';

export default function InventoryTable({ canManage, onAdd }) {
  return (
    <section className="simple-card">
      <div className="card-title">
        <h2>Inventory Stock</h2>
        {canManage && <button onClick={onAdd}>Add Item</button>}
      </div>

      <table>
        <thead><tr><th>Item Name</th><th>Quantity</th><th>Status</th></tr></thead>
        <tbody>
          {inventory.map((stock) => (
            <tr key={stock.item}>
              <td>{stock.item}</td>
              <td>{stock.quantity}</td>
              <td><span className={stock.status === 'Low Stock' ? 'status low' : 'status'}>{stock.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
