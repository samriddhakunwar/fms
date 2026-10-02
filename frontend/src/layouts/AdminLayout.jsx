import { Outlet } from "react-router-dom";
import DashboardLayout from "./DashboardLayout";

const NAV_ITEMS = [
  { label: "Dashboard", path: "/admin-dashboard" },
  { label: "Inventory", path: "/admin-dashboard/inventory" },
  { label: "Orders", path: "/admin-dashboard/orders" },
  { label: "Sales", path: "/admin-dashboard/sales" },
  { label: "Reports", path: "/admin-dashboard/reports" },
  { label: "Staff", path: "/admin-dashboard/staff" },
  { label: "Managers", path: "/admin-dashboard/managers" },
  { label: "Admins", path: "/admin-dashboard/admins" },
];

export default function AdminLayout() {
  return (
    <DashboardLayout navItems={NAV_ITEMS}>
      <Outlet />
    </DashboardLayout>
  );
}
