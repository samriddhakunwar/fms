import { Outlet } from "react-router-dom";
import DashboardLayout from "./DashboardLayout";

const NAV_ITEMS = [
  { label: "Dashboard", path: "/employee-dashboard" },
  { label: "Inventory", path: "/employee-dashboard/inventory" },
  { label: "My Profile", path: "/employee-dashboard/profile" },
];

export default function EmployeeLayout() {
  return (
    <DashboardLayout navItems={NAV_ITEMS}>
      <Outlet />
    </DashboardLayout>
  );
}
