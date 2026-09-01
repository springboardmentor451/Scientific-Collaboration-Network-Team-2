import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FaBook, FaCalendarAlt, FaChartBar, FaHandshake, FaProjectDiagram, FaUserCircle, FaUsers } from "react-icons/fa";
import DashboardLayout from "../layouts/DashboardLayout";
import { useAuth } from "../context/AuthContext";
import { getMyDashboard } from "../services/dashboardService";
import "./../styles/dashboard.css";

function Dashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState({ publications: 0, projects: 0, collaborations: 0, pending_requests: 0, upcoming_conferences: 0, institution_researchers: 0, draft_publications: 0, submitted_publications: 0, published_publications: 0, archived_publications: 0, research_interests: [] });
  useEffect(() => { getMyDashboard().then(setSummary).catch(() => {}); }, []);

  const profileFields = [user?.full_name, user?.institution, user?.department, user?.bio, user?.skills?.length, user?.research_interests?.length];
  const profileCompletion = Math.round((profileFields.filter(Boolean).length / profileFields.length) * 100);
  const researcherStatistics = [
    { label: "My Publications", value: summary.publications, icon: FaBook, note: "Research work you own", to: "/publications", tone: "indigo" },
    { label: "My Projects", value: summary.projects, icon: FaProjectDiagram, note: "Projects you lead", to: "/projects", tone: "violet" },
    { label: "My Collaborations", value: summary.collaborations, icon: FaHandshake, note: "Accepted connections", to: "/collaborations", tone: "violet" },
    { label: "Pending Requests", value: summary.pending_requests, icon: FaUsers, note: summary.pending_requests ? "Waiting for your response" : "You are all caught up", to: "/collaborations", tone: "teal" },
    { label: "Upcoming Conferences", value: summary.upcoming_conferences, icon: FaCalendarAlt, note: "Events available to explore", to: "/conferences", tone: "amber" },
  ];
  const roleStatistics = {
    Student: [
      { label: "Researchers", value: "Explore", icon: FaUsers, note: "Find mentors and research groups", to: "/researchers", tone: "teal" },
      { label: "Institutions", value: "Explore", icon: FaProjectDiagram, note: "Discover research organisations", to: "/institutions", tone: "indigo" },
      { label: "Conferences", value: summary.upcoming_conferences, icon: FaCalendarAlt, note: "Upcoming opportunities", to: "/conferences", tone: "amber" },
      { label: "My Profile", value: `${profileCompletion}%`, icon: FaUserCircle, note: "Complete your academic profile", to: "/profile", tone: "violet" },
    ],
    Reviewer: [
      { label: "Pending Reviews", value: summary.pending_reviews || 0, icon: FaBook, note: "Awaiting your review decision", to: "/reviews", tone: "indigo" },
      { label: "Completed Reviews", value: summary.completed_reviews || 0, icon: FaProjectDiagram, note: "Approved or rejected decisions", to: "/reviews", tone: "teal" },
      { label: "Assigned Publications", value: summary.publications, icon: FaBook, note: "Read-only review material", to: "/publications", tone: "violet" },
      { label: "My Profile", value: `${profileCompletion}%`, icon: FaUserCircle, note: "Review expertise", to: "/profile", tone: "amber" },
    ],
    Publisher: [
      { label: "Draft Publications", value: summary.draft_publications, icon: FaBook, note: "Work still being prepared", to: "/publications", tone: "indigo" },
      { label: "Submitted", value: summary.submitted_publications, icon: FaProjectDiagram, note: "Awaiting publication outcome", to: "/publications", tone: "teal" },
      { label: "Published", value: summary.published_publications, icon: FaBook, note: "Published research records", to: "/publications", tone: "violet" },
      { label: "Archived", value: summary.archived_publications, icon: FaUserCircle, note: "Archived publication records", to: "/publications", tone: "amber" },
    ],
    "Institution Admin": [
      { label: "Researchers", value: summary.institution_researchers, icon: FaUsers, note: "Institution researcher directory", to: "/researchers", tone: "teal" },
      { label: "Publications", value: summary.publications, icon: FaBook, note: "Institution publication records", to: "/publications", tone: "indigo" },
      { label: "Projects", value: summary.projects, icon: FaProjectDiagram, note: "Institution research projects", to: "/projects", tone: "violet" },
      { label: "Collaborations", value: summary.collaborations, icon: FaHandshake, note: "Institution collaboration activity", to: "/collaborations", tone: "amber" },
    ],
    Collaborator: [
      { label: "Active Collaborations", value: summary.collaborations, icon: FaHandshake, note: "Accepted research partnerships", to: "/collaborations", tone: "violet" },
      { label: "Pending Requests", value: summary.pending_requests, icon: FaUsers, note: "Requests awaiting your response", to: "/collaborations", tone: "teal" },
      { label: "Shared Projects", value: summary.projects, icon: FaProjectDiagram, note: "Projects you own or support", to: "/projects", tone: "indigo" },
      { label: "Upcoming Conferences", value: summary.upcoming_conferences, icon: FaCalendarAlt, note: "Events available to explore", to: "/conferences", tone: "amber" },
    ],
  };
  const statistics = roleStatistics[user?.role] || researcherStatistics;
  const roleGuidance = {
    Researcher: "Create your researcher profile, publish your work, and connect with experts in related fields.",
    Faculty: "Share publications, discover researchers, and build cross-institution collaborations.",
    Student: "Complete your profile, discover mentors, and explore research areas across the network.",
    Reviewer: "Review the publications assigned to you and keep a clear decision history.",
    Publisher: "Manage publication status, authors, citations, and research-document records.",
    "Institution Admin": "Manage your institution’s research data and view institution-level activity.",
    Collaborator: "Find relevant researchers and manage your active collaboration requests.",
  };
  const interests = summary.research_interests?.length ? summary.research_interests : user?.research_interests || [];
  const collaboratorActions = user?.role === "Collaborator";
  const publisherActions = user?.role === "Publisher";
  const studentActions = user?.role === "Student";
  const institutionAdminActions = user?.role === "Institution Admin";
  const reviewerActions = user?.role === "Reviewer";

  return <DashboardLayout><div className="dashboard">
    <header className="dashboard-header"><div><span className="dashboard-eyebrow"><FaProjectDiagram /> Personal research workspace</span><h1>Welcome back, {user?.full_name}</h1><p>{roleGuidance[user?.role] || "Manage your scientific collaboration network."}</p><strong className="dashboard-role">{user?.role}</strong></div><span className="dashboard-date">{new Intl.DateTimeFormat("en-IN", { weekday:"short", day:"numeric", month:"short", year:"numeric" }).format(new Date())}</span></header>

    <section className="cards" aria-label="Personal research statistics">{statistics.map(({label,value,icon:Icon,note,to,tone})=><Link className={`card card--${tone}`} to={to} key={label}><Icon className="card-icon"/><div className="card-copy"><h3>{label}</h3><h2>{value}</h2><span className="card-trend">{note}</span></div></Link>)}</section>

    <div className="dashboard-value-grid">
      <section className="dashboard-panel profile-progress-panel"><div className="dashboard-panel__heading"><div><span className="panel-kicker">Your presence</span><h2>Profile strength</h2></div><strong>{profileCompletion}%</strong></div><div className="profile-progress"><span style={{width:`${profileCompletion}%`}} /></div><p>{profileCompletion < 100 ? "A complete profile helps other researchers understand your background and expertise." : "Your profile is complete and ready to be discovered."}</p><Link className="panel-link" to="/profile"><FaUserCircle/> {profileCompletion < 100 ? "Complete my profile" : "Review my profile"}</Link></section>

      <section className="dashboard-panel"><div className="dashboard-panel__heading"><div><span className="panel-kicker">Your expertise</span><h2>Research interests</h2></div></div>{interests.length?<div className="interest-cloud">{interests.map(interest=><span key={interest}>{interest}</span>)}</div>:<div className="panel-empty"><p>No research interests added yet.</p><Link to="/profile">Add interests to your profile</Link></div>}<Link className="panel-link" to="/researchers"><FaUsers/> Discover matching researchers</Link></section>
    </div>

    <section className="dashboard-panel quick-actions-panel"><div className="dashboard-panel__heading"><div><span className="panel-kicker">Move your work forward</span><h2>Quick actions</h2></div></div><div className="quick-actions">{publisherActions ? <><Link to="/publications"><span><FaBook/></span><div><strong>Manage publications</strong><small>Create and maintain your publication records</small></div></Link><Link to="/citations"><span><FaProjectDiagram/></span><div><strong>Manage citations</strong><small>Maintain linked references and DOI records</small></div></Link><Link to="/conferences"><span><FaCalendarAlt/></span><div><strong>Explore conferences</strong><small>Review relevant research events</small></div></Link><Link to="/reports"><span><FaChartBar/></span><div><strong>Publication reports</strong><small>Review publication analytics</small></div></Link></> : studentActions ? <><Link to="/profile"><span><FaUserCircle/></span><div><strong>Complete my profile</strong><small>Add your interests, department, and academic skills</small></div></Link><Link to="/researchers"><span><FaUsers/></span><div><strong>Find researchers</strong><small>Explore mentors and research groups</small></div></Link><Link to="/institutions"><span><FaProjectDiagram/></span><div><strong>Explore institutions</strong><small>Discover universities and research organisations</small></div></Link><Link to="/conferences"><span><FaCalendarAlt/></span><div><strong>Explore conferences</strong><small>Find research events and participation opportunities</small></div></Link></> : institutionAdminActions ? <><Link to="/researchers"><span><FaUsers/></span><div><strong>Institution researchers</strong><small>Manage your assigned researcher directory</small></div></Link><Link to="/publications"><span><FaBook/></span><div><strong>Institution publications</strong><small>Maintain research output for your institution</small></div></Link><Link to="/projects"><span><FaProjectDiagram/></span><div><strong>Institution projects</strong><small>Manage projects and team assignments</small></div></Link><Link to="/reports"><span><FaChartBar/></span><div><strong>Institution reports</strong><small>Review institution-level analytics</small></div></Link></> : reviewerActions ? <><Link to="/reviews"><span><FaBook/></span><div><strong>Open review queue</strong><small>Complete assigned publication reviews</small></div></Link><Link to="/publications"><span><FaProjectDiagram/></span><div><strong>Assigned publications</strong><small>Read the material assigned for review</small></div></Link><Link to="/profile"><span><FaUserCircle/></span><div><strong>Review profile</strong><small>Keep your reviewing expertise current</small></div></Link><Link to="/notifications"><span><FaUsers/></span><div><strong>Notifications</strong><small>View review assignment updates</small></div></Link></> : <><Link to="/researchers"><span><FaUsers/></span><div><strong>Discover researchers</strong><small>Search by expertise or institution</small></div></Link>{!collaboratorActions && <Link to="/publications"><span><FaBook/></span><div><strong>Manage publications</strong><small>Add and review your research work</small></div></Link>}<Link to="/collaborations"><span><FaHandshake/></span><div><strong>Collaboration requests</strong><small>Review sent and received requests</small></div></Link>{collaboratorActions && <Link to="/projects"><span><FaProjectDiagram/></span><div><strong>My shared projects</strong><small>View projects you own or support</small></div></Link>}<Link to="/conferences"><span><FaCalendarAlt/></span><div><strong>Explore conferences</strong><small>Find upcoming research events</small></div></Link></>}</div></section>
  </div></DashboardLayout>;
}
export default Dashboard;
