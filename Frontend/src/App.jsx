import { Route, Routes } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import VerifyEmail from "./pages/VerifyEmail";
import ForgotPassword from "./pages/ForgotPassword";
import Notifications from "./pages/Notifications";
import Dashboard from "./pages/Dashboard";
import Researchers from "./pages/Researchers";
import Institutions from "./pages/Institutions";
import Publications from "./pages/Publications";
import Collaborations from "./pages/Collaborations";
import Conferences from "./pages/Conferences";
import Reports from "./pages/Reports";
import Audit from "./pages/Audit";
import Profile from "./pages/Profile";
import ProtectedRoute from "./components/ProtectedRoute";
import AdminDashboard from "./pages/AdminDashboard";
import AdminUsers from "./pages/AdminUsers";
import AdminData from "./pages/AdminData";
import AdminCitations from "./pages/AdminCitations";
import Announcements from "./pages/Announcements";
import Projects from "./pages/Projects";
import Citations from "./pages/Citations";
import Network from "./pages/Network";
import Reviews from "./pages/Reviews";
import { NotFound, Unauthorized } from "./pages/AccessState";
import ProtectedLayout from "./layouts/ProtectedLayout";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/unauthorized" element={<Unauthorized />} />

      <Route element={<ProtectedLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/researchers" element={<Researchers />} />
        <Route path="/institutions" element={<Institutions />} />
        <Route path="/publications" element={<Publications />} />
        <Route path="/collaborations" element={<Collaborations />} />
        <Route path="/conferences" element={<Conferences />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/citations" element={<Citations />} />
        <Route path="/network" element={<Network />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/reviews" element={<ProtectedRoute roles={["Reviewer", "Admin", "System Admin"]}><Reviews /></ProtectedRoute>} />
        <Route path="/audit" element={<ProtectedRoute roles={["Admin", "System Admin"]}><Audit /></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute roles={["Admin", "System Admin"]}><AdminDashboard /></ProtectedRoute>} />
        <Route path="/admin/users" element={<ProtectedRoute roles={["Admin", "System Admin"]}><AdminUsers /></ProtectedRoute>} />
        <Route path="/admin/data" element={<ProtectedRoute roles={["Admin", "System Admin"]}><AdminData /></ProtectedRoute>} />
        <Route path="/admin/data/:module" element={<ProtectedRoute roles={["Admin", "System Admin"]}><AdminData /></ProtectedRoute>} />
        <Route path="/admin/citations" element={<ProtectedRoute roles={["Admin", "System Admin"]}><AdminCitations /></ProtectedRoute>} />
        <Route path="/admin/reports" element={<ProtectedRoute roles={["Admin", "System Admin"]}><Reports /></ProtectedRoute>} />
        <Route path="/admin/announcements" element={<ProtectedRoute roles={["Admin", "System Admin"]}><Announcements /></ProtectedRoute>} />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default App;
