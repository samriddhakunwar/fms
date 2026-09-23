import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import Login from "./pages/Login";
import Unauthorized from "./pages/Unauthorized";
import ProtectedRoute from "./routes/ProtectedRoute";

import AdminLayout from "./layouts/AdminLayout";
import EmployeeLayout from "./layouts/EmployeeLayout";
import InventoryManagerLayout from "./layouts/InventoryManagerLayout";

import AdminDashboard from "./pages/AdminDashboard";
import EmployeeDashboard from "./pages/EmployeeDashboard";
import EmployeeList from "./pages/EmployeeList";
import EmployeeProfile from "./pages/EmployeeProfile";
import InventoryDashboard from "./pages/InventoryDashboard";
import OrdersPage from "./pages/OrdersPage";
import ProductList from "./pages/ProductList";
import ReportsPage from "./pages/ReportsPage";
import SalaryList from "./pages/SalaryList";
import SalesPage from "./pages/SalesPage";
import UserList from "./pages/UserList";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/unauthorized" element={<Unauthorized />} />

          <Route element={<ProtectedRoute allowedRoles={["ADMIN"]} />}>
            <Route path="/admin-dashboard" element={<AdminLayout />}>
              <Route index element={<AdminDashboard />} />
              <Route path="inventory" element={<ProductList />} />
              <Route path="employees" element={<EmployeeList />} />
              <Route path="salary" element={<SalaryList />} />
              <Route path="orders" element={<OrdersPage />} />
              <Route path="sales" element={<SalesPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="users" element={<UserList />} />
            </Route>
          </Route>

          <Route element={<ProtectedRoute allowedRoles={["INVENTORY_MANAGER"]} />}>
            <Route path="/inventory-dashboard" element={<InventoryManagerLayout />}>
              <Route index element={<InventoryDashboard />} />
              <Route path="products" element={<ProductList />} />
              <Route path="orders" element={<OrdersPage />} />
              {/* Sales and staff records are read-only for this
                  role: the pages hide every write action and the
                  API refuses one if it is called directly. */}
              <Route path="sales" element={<SalesPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="staff" element={<EmployeeList />} />
            </Route>
          </Route>

          <Route element={<ProtectedRoute allowedRoles={["STAFF"]} />}>
            <Route path="/employee-dashboard" element={<EmployeeLayout />}>
              <Route index element={<EmployeeDashboard />} />
              <Route path="inventory" element={<ProductList />} />
              <Route path="profile" element={<EmployeeProfile />} />
            </Route>
          </Route>

          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
