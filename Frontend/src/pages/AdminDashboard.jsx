import { useEffect, useState } from "react";
import { FaBook, FaCalendarAlt, FaHandshake, FaUniversity, FaUserCheck, FaUserGraduate, FaUsers } from "react-icons/fa";
import DashboardLayout from "../layouts/DashboardLayout";
import { getAdminStatistics, getDataQuality } from "../services/adminService";
import "../styles/admin.css";

function AdminDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [quality, setQuality] = useState(null);

  useEffect(() => {
    getAdminStatistics().then(setData).catch((response) => setError(response.response?.data?.detail || "Could not load Admin statistics."));
    getDataQuality().then(setQuality).catch(() => {});
  }, []);

  if (!data) return <DashboardLayout><div className="admin-page">{error || "Loading Admin dashboard..."}</div></DashboardLayout>;

  const cards = [
    ["Total Users", data.total_users, FaUsers],
    ["Active Users", data.active_users, FaUserCheck],
    ["Researchers", data.total_researchers, FaUserGraduate],
    ["Publications", data.total_publications, FaBook],
    ["Institutions", data.total_institutions, FaUniversity],
    ["Conferences", data.total_conferences, FaCalendarAlt],
    ["Accepted Collaborations", data.accepted_collaborations, FaHandshake],
  ];

  return <DashboardLayout><div className="admin-page"><header className="admin-hero"><span>Privileged workspace</span><h1>Admin Dashboard</h1><p>Manage the SCNA platform through protected, live database operations.</p></header><section className="admin-stats">{cards.map(([label, value, Icon]) => <article key={label}><Icon /><div><strong>{value ?? 0}</strong><span>{label}</span></div></article>)}</section><div className="admin-grid"><section className="admin-panel"><h2>Recently registered users</h2>{(data.recent_users || []).map((user) => <div className="recent-user" key={user.id}><div><strong>{user.full_name}</strong><span>{user.email}</span></div><em>{user.role}</em></div>)}{!data.recent_users?.length && <p>No users registered yet.</p>}</section><section className="admin-panel"><h2>Data quality</h2>{quality ? <><p>Users without institution: <strong>{quality.users_without_institution ?? 0}</strong></p><p>Researchers without account: <strong>{quality.researchers_without_user ?? 0}</strong></p><p>Publications without DOI: <strong>{quality.publications_without_doi ?? 0}</strong></p></> : <p>Loading quality checks…</p>}</section></div></div></DashboardLayout>;
}

export default AdminDashboard;
