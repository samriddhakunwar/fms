import { Outlet } from "react-router-dom";
import DashboardLayout from "./DashboardLayout";

const NAV_ITEMS = [
  { label: "Dashboard", path: "/manager-dashboard" },
  { label: "Inventory", path: "/manager-dashboard/products" },
  { label: "Orders", path: "/manager-dashboard/orders" },
  { label: "Sales", path: "/manager-dashboard/sales" },
  { label: "Reports", path: "/manager-dashboard/reports" },
  { label: "Staff", path: "/manager-dashboard/staff" },
];

export default function ManagerLayout() {
  return (
    <DashboardLayout navItems={NAV_ITEMS}>
      <Outlet />
    </DashboardLayout>
  );
}
