import { Outlet } from "react-router-dom";
import DashboardLayout from "./DashboardLayout";

const NAV_ITEMS = [
  { label: "Dashboard", path: "/inventory-dashboard" },
  { label: "Inventory", path: "/inventory-dashboard/products" },
  { label: "Orders", path: "/inventory-dashboard/orders" },
  { label: "Sales", path: "/inventory-dashboard/sales" },
  { label: "Reports", path: "/inventory-dashboard/reports" },
  { label: "Staff", path: "/inventory-dashboard/staff" },
];

export default function InventoryManagerLayout() {
  return (
    <DashboardLayout navItems={NAV_ITEMS}>
      <Outlet />
    </DashboardLayout>
  );
}
