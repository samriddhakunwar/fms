import { roleNames } from '../data/factoryData';
import InventoryTable from '../components/InventoryTable';
import OrdersTable from '../components/OrdersTable';

export default function DashboardContent({ role, onAddOrder, onAddItem }) {
  return (
    <>
      <h1>{roleNames[role]} Dashboard</h1>
      <p className="page-text">Welcome to the Factory Management System.</p>
      <div className="summary-cards">
        <div><h3>24</h3><p>Inventory Items</p></div>
        <div><h3>12</h3><p>Open Orders</p></div>
        <div><h3>Rs. 1,27,500</h3><p>Monthly Sales</p></div>
      </div>
      {role === 'staff' ? <InventoryTable onAdd={onAddItem} /> : <OrdersTable onAdd={onAddOrder} />}
    </>
  );
}
