import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./../styles/navbar.css";
import {
  FaBell,
  FaBullhorn,
  FaSearch,
  FaChevronDown,
  FaCheckCircle,
  FaSignOutAlt,
} from "react-icons/fa";
import { useAuth } from "../context/AuthContext";
import ThemeToggle from "./ThemeToggle";
import ProfileAvatar from "./ProfileAvatar";
import NotificationPanel from "./NotificationPanel";

const userNotifications = [
  ["collaboration", "New Collaboration Request", "A researcher wants to collaborate with you.", "5 minutes ago"], ["publication", "New Publication", "A publication matching your research interests was added.", "1 hour ago"], ["event", "Upcoming Research Event", "Research Collaboration Seminar is scheduled for tomorrow.", "Yesterday"], ["security", "Account Security", "Your account password was recently changed.", "Yesterday"],
];
const adminNotifications = [
  ["user", "New User Registered", "A new user has registered on SCNA.", "5 minutes ago"], ["researcher", "Researcher Verification Pending", "Researcher profiles are awaiting review.", "1 hour ago"], ["publication", "New Publication Added", "A new publication has been added to the system.", "3 hours ago"], ["backup", "Database Backup Successful", "Database backup completed successfully.", "Yesterday"], ["security", "Security Alert", "Multiple failed login attempts detected.", "Yesterday"],
];
const defaultsFor = (isAdmin) => (isAdmin ? adminNotifications : userNotifications).map(([type, title, message, time], index) => ({ id: `${isAdmin ? "admin" : "user"}-${index}`, type, title, message, time, read: index > 1 }));

function Navbar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const navbarMenusRef = useRef(null);

  const [activeMenu, setActiveMenu] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");

  const userName = user?.full_name || "User";
  const userRole = user?.role || "User";
  const isAdmin = ["Admin", "System Admin"].includes(userRole);
  const notificationKey = user?.id ? `scna_notifications_${isAdmin ? "admin" : "user"}_${user.id}` : null;

  useEffect(() => { if (!notificationKey) return undefined; const timer = window.setTimeout(() => { const saved = localStorage.getItem(notificationKey); setNotifications(saved ? JSON.parse(saved) : defaultsFor(isAdmin)); }, 0); return () => window.clearTimeout(timer); }, [notificationKey, isAdmin]);
  useEffect(() => { if (notificationKey) localStorage.setItem(notificationKey, JSON.stringify(notifications)); }, [notificationKey, notifications]);

  const unreadNotifications = useMemo(
    () => notifications.filter((notification) => !notification.read).length,
    [notifications]
  );

  useEffect(() => {
    const handleOutsideClick = (event) => {
      if (
        navbarMenusRef.current &&
        !navbarMenusRef.current.contains(event.target)
      ) {
        setActiveMenu(null);
      }
    };

    const handleEscape = (event) => {
      if (event.key === "Escape") {
        setActiveMenu(null);
      }
    };

    document.addEventListener("mousedown", handleOutsideClick);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  const toggleMenu = (menuName) => {
    setActiveMenu((currentMenu) =>
      currentMenu === menuName ? null : menuName
    );
  };

  const markAllNotificationsAsRead = () => setNotifications((items) => items.map((item) => ({ ...item, read: true })));
  const markNotificationAsRead = (id) => setNotifications((items) => items.map((item) => item.id === id ? { ...item, read: true } : item));

  const handleLogout = () => {
    logout();
    setActiveMenu(null);
    navigate("/", { replace: true });
  };

  const submitSearch = (event) => {
    event.preventDefault();
    const query = searchQuery.trim();
    if (!query) return;
    setSearchQuery("");
    navigate(`/researchers?search=${encodeURIComponent(query)}`);
  };

  return (
    <header className="navbar">
      <form className="navbar-search" role="search" onSubmit={submitSearch}>
        <label className="sr-only" htmlFor="global-search">
          Search researchers and publications
        </label>

        <FaSearch className="search-icon" aria-hidden="true" />

        <input
          id="global-search"
          type="search"
          placeholder="Search researchers, publications..."
          autoComplete="off"
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
        />
      </form>

      <div className="navbar-right" ref={navbarMenusRef}>
        <div className="navbar-menu-wrapper">
          <button
            type="button"
            className="navbar-icon-button notification"
            aria-label={
              unreadNotifications > 0
                ? `Notifications: ${unreadNotifications} unread`
                : "Notifications: no unread notifications"
            }
            aria-haspopup="menu"
            aria-expanded={activeMenu === "notifications"}
            title="Notifications"
            onClick={() => toggleMenu("notifications")}
          >
            <FaBell aria-hidden="true" />

            {unreadNotifications > 0 && (
              <span className="badge" aria-hidden="true">
                {unreadNotifications}
              </span>
            )}
          </button>

          {activeMenu === "notifications" && <NotificationPanel notifications={notifications} unreadCount={unreadNotifications} onRead={markNotificationAsRead} onReadAll={markAllNotificationsAsRead} onClear={() => setNotifications([])} onViewAll={() => { setActiveMenu(null); navigate("/notifications"); }} />}
        </div>

        {isAdmin && <button type="button" className="navbar-icon-button" aria-label="Send announcement" title="Send announcement" onClick={() => { setActiveMenu(null); navigate("/admin/announcements"); }}><FaBullhorn aria-hidden="true" /></button>}

        <ThemeToggle />
        <div className="profile-menu-wrapper">
          <button
            type="button"
            className="profile"
            aria-label={`Open account menu for ${userName}`}
            aria-haspopup="menu"
            aria-expanded={activeMenu === "profile"}
            onClick={() => toggleMenu("profile")}
          >
            <ProfileAvatar name={userName} />

            <span className="profile-info">
              <strong>{userName}</strong>
              <small>{userRole}</small>
            </span>

            <FaChevronDown
              className={`profile-chevron ${
                activeMenu === "profile" ? "profile-chevron--open" : ""
              }`}
              aria-hidden="true"
            />
          </button>

          {activeMenu === "profile" && (
            <div className="profile-menu" role="menu">
              <div className="profile-menu__account">
                <ProfileAvatar name={userName} className="profile-menu__avatar" />

                <div>
                  <strong>{userName}</strong>
                  <span>{userRole}</span>
                </div>
              </div>

              <div className="profile-menu__status">
                <FaCheckCircle aria-hidden="true" />
                <span>Signed in and active</span>
              </div>

              <div className="profile-menu__details">
                <div>
                  <span>Access level</span>
                  <strong>{userRole}</strong>
                </div>

                <div>
                  <span>Workspace</span>
                  <strong>Research Portal</strong>
                </div>
              </div>

              <div className="profile-menu__divider" />

              <button type="button" className="profile-menu__logout" role="menuitem" onClick={() => { setActiveMenu(null); navigate("/profile"); }}>
                View and edit profile
              </button>

              <button
                type="button"
                className="profile-menu__logout"
                role="menuitem"
                onClick={handleLogout}
              >
                <FaSignOutAlt aria-hidden="true" />
                Log out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default Navbar;
