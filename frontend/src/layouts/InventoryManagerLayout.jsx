import { Outlet } from "react-router-dom";
import DashboardLayout from "./DashboardLayout";

const NAV_ITEMS = [
  { label: "Dashboard", path: "/inventory-dashboard" },
  { label: "Inventory", path: "/inventory-dashboard/products" },
  { label: "Inventory Reports", path: "/inventory-dashboard/reports" },
];

export default function InventoryManagerLayout() {
  return (
    <DashboardLayout navItems={NAV_ITEMS}>
      <Outlet />
    </DashboardLayout>
  );
}
