import { useEffect, useState } from "react";
import DashboardLayout from "../layouts/DashboardLayout";
import { getAdminCitations } from "../services/citationService";
import "../styles/admin.css";

function AdminCitations(){const[citations,setCitations]=useState([]),[error,setError]=useState("");useEffect(()=>{getAdminCitations().then(setCitations).catch(e=>setError(e.response?.data?.detail||"Could not load citations."));},[]);return <DashboardLayout><div className="admin-page"><header><h1>Citation &amp; Reference Management</h1><p>Review citation records submitted by users.</p></header>{error&&<p className="admin-error">{error}</p>}<div className="admin-records">{citations.map(item=><article key={item.id}><div><strong>{item.cited_title}</strong><span>{item.cited_authors||"Unknown authors"} · Owner #{item.owner_id}</span></div></article>)}{!citations.length&&<p>No citation records found.</p>}</div></div></DashboardLayout>}
export default AdminCitations;
