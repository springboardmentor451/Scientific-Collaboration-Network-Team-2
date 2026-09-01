import { useEffect, useMemo, useState } from "react";
import { FaSearch, FaTrash } from "react-icons/fa";
import DashboardLayout from "../layouts/DashboardLayout";
import { useAuth } from "../context/AuthContext";
import { deleteAdminUser, getAdminUsers, setUserApproval, setUserRole, setUserStatus } from "../services/adminService";
import "../styles/admin.css";

const roles = ["System Admin", "Institution Admin", "Researcher", "Reviewer", "Publisher"];
function AdminUsers() {
  const { user: admin } = useAuth(); const [users, setUsers] = useState([]); const [search, setSearch] = useState(""); const [error, setError] = useState("");
  const load = () => getAdminUsers().then(setUsers).catch((e) => setError(e.response?.data?.detail || "Could not load users.")); useEffect(() => { load(); }, []);
  const filtered = useMemo(() => users.filter((u) => `${u.full_name} ${u.email} ${u.role} ${u.approval_status}`.toLowerCase().includes(search.toLowerCase())), [users, search]);
  const update = async (action) => { try { const updated = await action(); setUsers((current) => current.map((item) => item.id === updated.id ? updated : item)); } catch (e) { setError(e.response?.data?.detail || "Update failed."); } };
  const remove = async (item) => { if (!window.confirm(`Permanently delete ${item.full_name}?`)) return; try { await deleteAdminUser(item.id); setUsers((current) => current.filter((value) => value.id !== item.id)); } catch (e) { setError(e.response?.data?.detail || "Delete failed."); } };
  return <DashboardLayout><div className="admin-page"><header><h1>User Management</h1><p>Approve accounts and manage roles without exposing passwords.</p></header>{error && <p className="admin-error">{error}</p>}<div className="admin-search"><FaSearch /><input placeholder="Search name, email, role, or approval status" value={search} onChange={(e) => setSearch(e.target.value)} /></div><div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>User</th><th>Role</th><th>Approval</th><th>Status</th><th>Actions</th></tr></thead><tbody>{filtered.map((item) => <tr key={item.id}><td><strong>{item.full_name}</strong><small>{item.email}</small></td><td><select value={item.role} disabled={item.id === admin.id} onChange={(e) => update(() => setUserRole(item.id, e.target.value))}>{roles.map((role) => <option key={role}>{role}</option>)}</select></td><td><select value={item.approval_status} disabled={item.id === admin.id} onChange={(e) => update(() => setUserApproval(item.id, e.target.value))}><option>Pending</option><option>Approved</option><option>Rejected</option></select></td><td><span className={item.is_active ? "status-active" : "status-inactive"}>{item.is_active ? "Active" : "Inactive"}</span></td><td><div className="admin-row-actions"><button disabled={item.id === admin.id} onClick={() => update(() => setUserStatus(item.id, !item.is_active))}>{item.is_active ? "Deactivate" : "Activate"}</button><button className="danger" disabled={item.id === admin.id} onClick={() => remove(item)}><FaTrash /></button></div></td></tr>)}</tbody></table></div></div></DashboardLayout>;
}
export default AdminUsers;
