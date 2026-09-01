import "./../styles/sidebar.css";
import { NavLink, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import {
  FaBars,
  FaTimes,
  FaHome,
  FaUsers,
  FaUniversity,
  FaBook,
  FaHandshake,
  FaCalendarAlt,
  FaChartBar,
  FaClipboardList,
  FaSignOutAlt,
  FaProjectDiagram,
  FaUserShield,
  FaQuoteRight,
  FaFolderOpen,
} from "react-icons/fa";
import { useAuth } from "../context/AuthContext";

function Sidebar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    const closeOnEscape = (event) => {
      if (event.key === "Escape") {
        setShowLogoutModal(false);
        setIsSidebarOpen(false);
      }
    };

    window.addEventListener("keydown", closeOnEscape);

    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);

  const closeSidebar = () => {
    setIsSidebarOpen(false);
  };

  const handleLogout = () => {
    logout();
    setShowLogoutModal(false);
    setIsSidebarOpen(false);
    navigate("/", { replace: true });
  };

  const normalNavigationItems = [
    { to: "/dashboard", label: "Dashboard", icon: FaHome },
    { to: "/researchers", label: "Researchers", icon: FaUsers },
    { to: "/institutions", label: "Institutions", icon: FaUniversity },
    { to: "/publications", label: "Publications", icon: FaBook },
    { to: "/collaborations", label: "Collaborations", icon: FaHandshake },
    { to: "/conferences", label: "Conferences", icon: FaCalendarAlt },
    { to: "/projects", label: "Projects", icon: FaFolderOpen },
    { to: "/citations", label: "Citations", icon: FaQuoteRight },
    { to: "/network", label: "Collaboration Network", icon: FaProjectDiagram },
    { to: "/reports", label: "Reports", icon: FaChartBar },
  ];
  const adminNavigationItems = [
    { to: "/admin", label: "Admin Dashboard", icon: FaUserShield },
    { to: "/admin/users", label: "User Management", icon: FaUsers },
    { to: "/admin/data/researchers", label: "Researcher Management", icon: FaUsers },
    { to: "/admin/data/publications", label: "Publication Management", icon: FaBook },
    { to: "/admin/data/collaborations", label: "Collaboration Management", icon: FaHandshake },
    { to: "/admin/data/institutions", label: "Institution Management", icon: FaUniversity },
    { to: "/admin/data/conferences", label: "Conference Management", icon: FaCalendarAlt },
    { to: "/admin/data/projects", label: "Project Management", icon: FaFolderOpen },
    { to: "/admin/citations", label: "Citation & Reference", icon: FaQuoteRight },
    { to: "/admin/reports", label: "Reports & Analytics", icon: FaChartBar },
    { to: "/audit", label: "Audit Logs", icon: FaClipboardList },
  ];
  const roleNavigation = {
    Researcher: normalNavigationItems,
    Faculty: normalNavigationItems.filter((item) => !["/institutions"].includes(item.to)),
    Student: normalNavigationItems.filter((item) => ["/dashboard", "/researchers", "/institutions", "/conferences", "/reports"].includes(item.to)),
    Collaborator: normalNavigationItems.filter((item) => ["/dashboard", "/researchers", "/collaborations", "/conferences", "/projects", "/network", "/reports"].includes(item.to)),
    "Institution Admin": normalNavigationItems.filter((item) => ["/dashboard", "/researchers", "/institutions", "/publications", "/collaborations", "/projects", "/reports"].includes(item.to)),
    Reviewer: [{ to: "/dashboard", label: "Dashboard", icon: FaHome }, { to: "/reviews", label: "Review Queue", icon: FaClipboardList }, { to: "/publications", label: "Publications", icon: FaBook }, { to: "/reports", label: "Reports", icon: FaChartBar }],
    Publisher: normalNavigationItems.filter((item) => ["/dashboard", "/publications", "/citations", "/conferences", "/reports"].includes(item.to)),
  };
  const navigationItems = ["Admin", "System Admin"].includes(user?.role) ? adminNavigationItems : (roleNavigation[user?.role] || roleNavigation.Researcher);

  return (
    <>
      <button
        type="button"
        className="mobile-menu-toggle"
        aria-label={isSidebarOpen ? "Close navigation menu" : "Open navigation menu"}
        aria-controls="sidebar-navigation"
        aria-expanded={isSidebarOpen}
        onClick={() => setIsSidebarOpen((currentState) => !currentState)}
      >
        {isSidebarOpen ? <FaTimes /> : <FaBars />}
      </button>

      <aside className={`sidebar ${isSidebarOpen ? "sidebar-open" : ""}`}>
        <div className="logo-section">
          <span className="logo-section__mark" aria-hidden="true">
            <FaProjectDiagram />
          </span>
          <span className="logo-section__copy">
            <h2>SCNA</h2>
            <p>Collaboration intelligence</p>
          </span>
        </div>

        <nav id="sidebar-navigation" aria-label="Primary navigation">
          <ul className="sidebar-menu">
            {navigationItems.map(({ to, label, icon: Icon }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  className={({ isActive }) => (isActive ? "active-link" : "")}
                  onClick={closeSidebar}
                >
                  <Icon aria-hidden="true" />
                  <span>{label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <button
          type="button"
          className="logout-btn"
          onClick={() => setShowLogoutModal(true)}
        >
          <FaSignOutAlt aria-hidden="true" />
          <span>Logout</span>
        </button>
      </aside>

      {isSidebarOpen && (
        <button
          type="button"
          className="sidebar-backdrop"
          aria-label="Close navigation menu"
          onClick={closeSidebar}
        />
      )}

      {showLogoutModal && (
        <div
          className="modal-overlay"
          role="presentation"
          onMouseDown={() => setShowLogoutModal(false)}
        >
          <div
            className="logout-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="logout-modal-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <h2 id="logout-modal-title">Log out?</h2>
            <p>Are you sure you want to log out of the Research Portal?</p>

            <div className="modal-buttons">
              <button
                type="button"
                className="cancel-btn"
                onClick={() => setShowLogoutModal(false)}
              >
                Cancel
              </button>

              <button
                type="button"
                className="confirm-btn"
                onClick={handleLogout}
              >
                Log out
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default Sidebar;
