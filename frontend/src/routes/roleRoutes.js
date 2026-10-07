export const ROLE_DASHBOARD_PATH = {
  ADMIN: "/admin-dashboard",
  MANAGER: "/manager-dashboard",
  STAFF: "/staff-dashboard",
};

export const ADMIN_NAV = [
  { label: "Dashboard", path: "/admin-dashboard" },
  { label: "Inventory", path: "/admin-dashboard/inventory" },
  { label: "Orders", path: "/admin-dashboard/orders" },
  { label: "Sales", path: "/admin-dashboard/sales" },
  { label: "Reports", path: "/admin-dashboard/reports" },
  { label: "Staff", path: "/admin-dashboard/staff" },
  { label: "Managers", path: "/admin-dashboard/managers" },
  { label: "Admins", path: "/admin-dashboard/admins" },
];

export const MANAGER_NAV = [
  { label: "Dashboard", path: "/manager-dashboard" },
  { label: "Inventory", path: "/manager-dashboard/products" },
  { label: "Orders", path: "/manager-dashboard/orders" },
  { label: "Sales", path: "/manager-dashboard/sales" },
  { label: "Reports", path: "/manager-dashboard/reports" },
  { label: "Staff", path: "/manager-dashboard/staff" },
];

export const STAFF_NAV = [
  { label: "Dashboard", path: "/staff-dashboard" },
  { label: "Inventory", path: "/staff-dashboard/inventory" },
  { label: "My Profile", path: "/staff-dashboard/profile" },
];

export const ROLE_LABELS = {
  ADMIN: "Admin",
  MANAGER: "Manager",
  STAFF: "Staff",
};
