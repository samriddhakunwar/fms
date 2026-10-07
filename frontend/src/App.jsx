import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import Login from "./pages/Login";
import Unauthorized from "./pages/Unauthorized";
import ProtectedRoute from "./routes/ProtectedRoute";
import { ADMIN_NAV, MANAGER_NAV, STAFF_NAV } from "./routes/roleRoutes";

import DashboardLayout from "./layouts/DashboardLayout";

import AccountList from "./pages/AccountList";
import AdminDashboard from "./pages/AdminDashboard";
import ManagerDashboard from "./pages/ManagerDashboard";
import OrdersPage from "./pages/OrdersPage";
import ProductList from "./pages/ProductList";
import ReportsPage from "./pages/ReportsPage";
import SalesPage from "./pages/SalesPage";
import StaffDashboard from "./pages/StaffDashboard";
import StaffList from "./pages/StaffList";
import StaffProfile from "./pages/StaffProfile";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/unauthorized" element={<Unauthorized />} />

          <Route element={<ProtectedRoute allowedRoles={["ADMIN"]} />}>
            <Route path="/admin-dashboard" element={<DashboardLayout navItems={ADMIN_NAV} />}>
              <Route index element={<AdminDashboard />} />
              <Route path="inventory" element={<ProductList />} />
              <Route path="orders" element={<OrdersPage />} />
              <Route path="sales" element={<SalesPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="staff" element={<StaffList />} />
              <Route path="managers" element={<AccountList kind="MANAGER" />} />
              <Route path="admins" element={<AccountList kind="ADMIN" />} />
            </Route>
          </Route>

          <Route element={<ProtectedRoute allowedRoles={["MANAGER"]} />}>
            <Route path="/manager-dashboard" element={<DashboardLayout navItems={MANAGER_NAV} />}>
              <Route index element={<ManagerDashboard />} />
              <Route path="products" element={<ProductList />} />
              <Route path="orders" element={<OrdersPage />} />
              <Route path="sales" element={<SalesPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="staff" element={<StaffList />} />
            </Route>
          </Route>

          <Route element={<ProtectedRoute allowedRoles={["STAFF"]} />}>
            <Route path="/staff-dashboard" element={<DashboardLayout navItems={STAFF_NAV} />}>
              <Route index element={<StaffDashboard />} />
              <Route path="inventory" element={<ProductList />} />
              <Route path="profile" element={<StaffProfile />} />
            </Route>
          </Route>

          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
