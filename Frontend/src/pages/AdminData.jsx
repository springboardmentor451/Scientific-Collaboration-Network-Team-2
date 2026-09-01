import { useCallback, useEffect, useMemo, useState } from "react";
import { FaPlus, FaTrash } from "react-icons/fa";
import { useLocation } from "react-router-dom";
import DashboardLayout from "../layouts/DashboardLayout";
import { deleteAdminPublication, deleteAdminResearcher, getAdminCollaborations, getAdminPublications, getAdminResearchers } from "../services/adminService";
import { createInstitution, deleteInstitution, getInstitutions } from "../services/institutionService";
import { createConference, deleteConference, getConferences } from "../services/conferenceService";
import { deleteProject, getAdminProjects } from "../services/projectService";
import "../styles/admin.css";

const tabs = ["researchers", "publications", "collaborations", "institutions", "conferences", "projects"];
const institutionInitial = { name: "", short_name: "", location: "", description: "", research_areas: "", website: "" };
const conferenceInitial = { title: "", topic: "", location: "", starts_at: "", ends_at: "", description: "", registration_url: "", is_open: true };

function AdminData() {
  const location = useLocation();
  const routeTab = location.pathname.split("/").pop();
  const tab = tabs.includes(routeTab) ? routeTab : "researchers";
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [institution, setInstitution] = useState(institutionInitial);
  const [conference, setConference] = useState(conferenceInitial);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loaders = useMemo(() => ({
    researchers: getAdminResearchers,
    publications: getAdminPublications,
    collaborations: getAdminCollaborations,
    institutions: getInstitutions,
    conferences: getConferences,
    projects: getAdminProjects,
  }), []);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(await loaders[tab]());
    } catch (e) {
      setData([]);
      setError(e.response?.data?.detail || "Could not load system data.");
    } finally {
      setLoading(false);
    }
  }, [loaders, tab]);

  useEffect(() => {
    const requestId = window.setTimeout(load, 0);
    return () => window.clearTimeout(requestId);
  }, [load]);

  const remove = async (type, item) => {
    if (!window.confirm(`Permanently delete ${item.name || item.title}?`)) return;
    try {
      if (type === "researchers") await deleteAdminResearcher(item.id);
      if (type === "publications") await deleteAdminPublication(item.id);
      if (type === "institutions") await deleteInstitution(item.id);
      if (type === "conferences") await deleteConference(item.id);
      if (type === "projects") await deleteProject(item.id);
      setMessage("Record deleted successfully."); load();
    } catch (e) { setError(e.response?.data?.detail || "Delete failed."); }
  };
  const addInstitution = async (event) => { event.preventDefault(); try { await createInstitution({ ...institution, research_areas: institution.research_areas.split(",").map((x) => x.trim()).filter(Boolean), description: institution.description || null, website: institution.website || null }); setInstitution(institutionInitial); setMessage("Institution added to the live database."); load(); } catch (e) { setError(e.response?.data?.detail || "Could not add institution."); } };
  const addConference = async (event) => { event.preventDefault(); try { await createConference({ ...conference, starts_at: new Date(conference.starts_at).toISOString(), ends_at: conference.ends_at ? new Date(conference.ends_at).toISOString() : null, description: conference.description || null, registration_url: conference.registration_url || null }); setConference(conferenceInitial); setMessage("Conference added to the live database."); load(); } catch (e) { setError(e.response?.data?.detail || "Could not add conference."); } };
  const title = (item) => item.name || item.title || `${item.requester_name} → ${item.recipient_name}`;
  const heading = useMemo(() => ({ researchers: "Researcher Management", publications: "Publication Management", collaborations: "Collaboration Management", institutions: "Institution Management", conferences: "Conference Management", projects: "Project Management" }[tab]), [tab]);

  return <DashboardLayout><div className="admin-page"><header><h1>{heading}</h1><p>Manage live {tab} records stored in Supabase PostgreSQL.</p></header>{error && <p className="admin-error">{error} <button type="button" onClick={load}>Retry</button></p>}{message && <p className="admin-success">{message}</p>}<div className="admin-module-count">{loading ? "Loading records…" : `${data.length} ${tab} record${data.length === 1 ? "" : "s"}`}</div>
    {tab === "institutions" && <form className="admin-create-form" onSubmit={addInstitution}><h2><FaPlus /> Add institution</h2><input required placeholder="Institution name" value={institution.name} onChange={(e) => setInstitution({ ...institution, name: e.target.value })} /><input required placeholder="Short name" value={institution.short_name} onChange={(e) => setInstitution({ ...institution, short_name: e.target.value })} /><input required placeholder="Location" value={institution.location} onChange={(e) => setInstitution({ ...institution, location: e.target.value })} /><input placeholder="Research areas (comma separated)" value={institution.research_areas} onChange={(e) => setInstitution({ ...institution, research_areas: e.target.value })} /><textarea placeholder="Description" value={institution.description} onChange={(e) => setInstitution({ ...institution, description: e.target.value })} /><button className="ui-button ui-button--primary">Save institution</button></form>}
    {tab === "conferences" && <form className="admin-create-form" onSubmit={addConference}><h2><FaPlus /> Add conference</h2><input required placeholder="Conference title" value={conference.title} onChange={(e) => setConference({ ...conference, title: e.target.value })} /><input required placeholder="Topic" value={conference.topic} onChange={(e) => setConference({ ...conference, topic: e.target.value })} /><input required placeholder="Location" value={conference.location} onChange={(e) => setConference({ ...conference, location: e.target.value })} /><label>Starts<input required type="datetime-local" value={conference.starts_at} onChange={(e) => setConference({ ...conference, starts_at: e.target.value })} /></label><label>Ends<input type="datetime-local" value={conference.ends_at} onChange={(e) => setConference({ ...conference, ends_at: e.target.value })} /></label><textarea placeholder="Description" value={conference.description} onChange={(e) => setConference({ ...conference, description: e.target.value })} /><button className="ui-button ui-button--primary">Save conference</button></form>}
    <div className={`admin-records admin-records--${tab}`}>{!loading && data.map((item) => <article key={item.id}><div><strong>{title(item)}</strong>{tab === "researchers" && <span>Field: {item.field || "Not specified"} · Institution: {item.institution || "Not specified"} · {item.publication_count ?? 0} publications · {item.collaboration_count ?? 0} collaborations</span>}{tab === "publications" && <span>Owner: {item.owner_name} · {item.research_area} · {item.publication_year} · {item.venue}</span>}{tab === "collaborations" && <span>{item.requester_name} → {item.recipient_name} · Status: {item.status} · {new Date(item.created_at).toLocaleDateString()}</span>}{tab === "institutions" && <span>{item.location} · {item.researcher_count} researchers · {item.publication_count} publications</span>}{tab === "conferences" && <span>{item.topic} · {item.location} · {item.participant_count} registered</span>}{tab === "projects" && <span>Owner #{item.owner_id} · {item.research_area} · Status: {item.status}</span>}</div>{tab !== "collaborations" && <button aria-label={`Delete ${title(item)}`} onClick={() => remove(tab, item)}><FaTrash /></button>}</article>)}{!loading && !data.length && <p>No {tab} records found.</p>}</div>
  </div></DashboardLayout>;
}
export default AdminData;
