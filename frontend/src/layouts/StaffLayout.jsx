import { Outlet } from "react-router-dom";
import DashboardLayout from "./DashboardLayout";

const NAV_ITEMS = [
  { label: "Dashboard", path: "/staff-dashboard" },
  { label: "Inventory", path: "/staff-dashboard/inventory" },
  { label: "My Profile", path: "/staff-dashboard/profile" },
];

export default function StaffLayout() {
  return (
    <DashboardLayout navItems={NAV_ITEMS}>
      <Outlet />
    </DashboardLayout>
  );
}
