import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FaBullhorn, FaEnvelope, FaPaperPlane } from "react-icons/fa";
import DashboardLayout from "../layouts/DashboardLayout";
import { sendAnnouncement } from "../services/notificationService";
import "../styles/announcements.css";

const roles = ["All", "Researcher", "Faculty", "Student", "Institution Admin", "Reviewer", "Publisher"];

function Announcements() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ subject: "", message: "", recipient_role: "All", send_email: false });
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);
  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }));
  const submit = async (event) => {
    event.preventDefault(); setFeedback(""); setError("");
    if (form.subject.trim().length < 2 || form.message.trim().length < 2) { setError("Please enter a subject and message of at least two characters."); return; }
    setSending(true);
    try {
      const result = await sendAnnouncement({ ...form, subject: form.subject.trim(), message: form.message.trim(), recipient_role: form.recipient_role === "All" ? null : form.recipient_role });
      const mailSummary = form.send_email ? ` Email delivered: ${result.email_sent_count ?? 0}; email delivery failed: ${result.email_failed_count ?? 0}.` : "";
      setFeedback(`${result.message || "Announcement sent."} In-app recipients: ${result.recipient_count ?? 0}.${mailSummary}`);
      setForm({ subject: "", message: "", recipient_role: "All", send_email: false });
    } catch (requestError) { setError(requestError.response?.data?.detail || "The announcement could not be sent. Please try again."); } finally { setSending(false); }
  };
  return <DashboardLayout><div className="admin-page announcement-page"><header className="admin-hero"><span>Administrator communication</span><h1>Send Announcement</h1><p>Send an SCNA notification to approved users, with optional email delivery.</p></header><section className="announcement-card"><div className="announcement-card__intro"><FaBullhorn /><div><h2>Announcement details</h2><p>In-app notifications are always created. Email is sent only when you select the option below.</p></div></div>{error && <p className="admin-error" role="alert">{error}</p>}{feedback && <p className="announcement-success" role="status">{feedback}</p>}<form className="announcement-form" onSubmit={submit}><label>Subject<input value={form.subject} maxLength="200" required onChange={(event) => update("subject", event.target.value)} placeholder="Example: Upcoming collaboration seminar" /></label><label>Recipients<select value={form.recipient_role} onChange={(event) => update("recipient_role", event.target.value)}>{roles.map((role) => <option key={role} value={role}>{role === "All" ? "All approved users" : role}</option>)}</select></label><label className="announcement-form__message">Message<textarea value={form.message} maxLength="5000" required rows="8" onChange={(event) => update("message", event.target.value)} placeholder="Write a clear message for the selected recipients…" /></label><label className="announcement-email-option"><input type="checkbox" checked={form.send_email} onChange={(event) => update("send_email", event.target.checked)} /><span><FaEnvelope aria-hidden="true" /><strong>Also send by email</strong><small>Deliver this announcement to each selected recipient’s verified email address.</small></span></label><div className="announcement-actions"><button type="button" className="ui-button" onClick={() => navigate("/admin")}>Cancel</button><button type="submit" className="ui-button ui-button--primary" disabled={sending}>{sending ? "Sending…" : <><FaPaperPlane /> Send announcement</>}</button></div></form></section></div></DashboardLayout>;
}

export default Announcements;
