import { useEffect, useState } from "react";
import { FaBookOpen, FaHandshake, FaHourglassHalf, FaCalendarCheck } from "react-icons/fa";
import DashboardLayout from "../layouts/DashboardLayout";
import { deleteGeneratedReport, downloadGeneratedReport, generateInstitutionReport, getGeneratedReports, getMyReport } from "../services/reportService";
import { getInstitutions } from "../services/institutionService";
import { getAdminStatistics } from "../services/adminService";
import { useAuth } from "../context/AuthContext";
import "../styles/reports.css";
import "../styles/management-table.css";

const cards = [["publication_count", "My publications", FaBookOpen], ["collaboration_count", "Accepted collaborations", FaHandshake], ["pending_received", "Requests awaiting me", FaHourglassHalf], ["conference_registrations", "Conference registrations", FaCalendarCheck]];

function Reports() {
  const { user } = useAuth();
  const isAdmin = ["Admin", "System Admin"].includes(user?.role);
  const [report, setReport] = useState(null);
  const [generated, setGenerated] = useState([]);
  const [institutions, setInstitutions] = useState([]);
  const [institutionId, setInstitutionId] = useState("");
  const [error, setError] = useState("");
  const loadGenerated = () => getGeneratedReports().then(setGenerated).catch(() => setGenerated([]));
  useEffect(() => { (isAdmin ? getAdminStatistics() : getMyReport()).then(setReport).catch((e) => setError(e.response?.data?.detail || "Could not load analytics.")); loadGenerated(); if (isAdmin || user?.role === "Institution Admin") getInstitutions().then(setInstitutions).catch(() => setInstitutions([])); }, [isAdmin, user?.role]);
  const reportCards = isAdmin
    ? [["total_users", "Total users", FaBookOpen], ["total_researchers", "Researchers", FaHandshake], ["total_publications", "Publications", FaHourglassHalf], ["accepted_collaborations", "Accepted collaborations", FaCalendarCheck]]
    : cards;
  const exportCsv = () => { const rows = [["Metric", "Value"], ...reportCards.map(([field, label]) => [label, report[field] ?? 0])]; const blob = new Blob([rows.map((row) => row.join(",")).join("\n")], { type: "text/csv" }); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = isAdmin ? "scna-system-report.csv" : "scna-personal-report.csv"; link.click(); URL.revokeObjectURL(url); };
  return <DashboardLayout><div className="reports-page">
    <header className="reports-page__header reports-page__header--actions"><div><h1>{isAdmin ? "System Reports & Analytics" : "My Reports & Analytics"}</h1><p>{isAdmin ? "Protected, live statistics for the full SCNA platform." : "A live summary of your research activity and collaboration network."}</p></div>{report && <div className="reports-export-actions"><button className="ui-button ui-button--secondary" onClick={exportCsv}>Export CSV</button><button className="ui-button ui-button--primary" onClick={() => window.print()}>Export PDF</button></div>}</header>
    {error && <p className="module-error">{error}</p>}{!report && !error && <p className="reports-loading">Loading analytics...</p>}
    {report && <>{(isAdmin || user?.role === "Institution Admin") && <section className="reports-generator"><div><h2>Generate institution report</h2><p>Select an institution to create a database-backed report with export files.</p></div><div className="reports-generator__controls"><select value={institutionId} onChange={(event) => setInstitutionId(event.target.value)}><option value="">Select institution</option>{institutions.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select><button className="ui-button ui-button--primary" disabled={!institutionId} onClick={async () => { try { await generateInstitutionReport(institutionId); loadGenerated(); } catch (requestError) { setError(requestError.response?.data?.detail || "Could not generate report."); } }}>Generate report</button></div>{generated.length > 0 && <div className="management-table-wrap reports-generated-table"><table className="management-table"><thead><tr><th>Report</th><th>Institution</th><th>Generated</th><th>Actions</th></tr></thead><tbody>{generated.map((item) => <tr key={item.id}><td>{item.report_type}</td><td>{item.payload?.institution || "—"}</td><td>{new Date(item.created_at).toLocaleString()}</td><td><div className="management-actions"><button onClick={() => downloadGeneratedReport(item.id, "xlsx")}>Export Excel</button><button onClick={() => downloadGeneratedReport(item.id, "pdf")}>Export PDF</button><button className="danger" onClick={async () => { if (!window.confirm("Delete this generated report?")) return; await deleteGeneratedReport(item.id); loadGenerated(); }}>Delete</button></div></td></tr>)}</tbody></table></div>}</section>}<section className="reports-summary">{reportCards.map(([field, label, Icon]) => <article className="reports-summary__card" key={field}><Icon/><span>{label}</span><strong>{report[field] ?? 0}</strong></article>)}</section>
      {isAdmin ? <section className="report-insights"><article className="report-insight report-insight--wide"><h2>Role distribution</h2><div className="report-tags">{Object.entries(report.role_distribution || {}).map(([role, count]) => <span key={role}>{role}: {count}</span>)}</div></article><article className="report-insight"><h2>Account status</h2><p>{report.active_users ?? 0} active and {report.inactive_users ?? 0} inactive accounts.</p></article><article className="report-insight"><h2>Collaboration requests</h2><p>{report.collaboration_requests ?? 0} requests recorded across the platform.</p></article></section> : <section className="report-insights">
        <article className="report-insight"><h2>Research interests</h2><div className="report-tags">{(report.interests || []).length ? report.interests.map(x => <span key={x}>{x}</span>) : <p>Add research interests to your profile to improve discovery.</p>}</div></article>
        <article className="report-insight"><h2>Skills &amp; expertise</h2><div className="report-tags">{(report.skills || []).length ? report.skills.map(x => <span key={x}>{x}</span>) : <p>Add skills to your profile so collaborators can find you.</p>}</div></article>
        <article className="report-insight report-insight--wide"><h2>Publication trend</h2>{(report.publication_trends || []).length ? <div className="trend-list">{report.publication_trends.map(x => <div className="trend-row" key={x.year}><span>{x.year}</span><div><i style={{width:`${Math.max(8,x.count*18)}px`}}/></div><strong>{x.count}</strong></div>)}</div> : <p>No trend is available yet. Add your first publication to begin.</p>}</article>
      </section>}</>}
  </div></DashboardLayout>;
}
export default Reports;
