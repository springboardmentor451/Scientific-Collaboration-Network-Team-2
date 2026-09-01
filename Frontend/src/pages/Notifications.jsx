import { useEffect, useMemo, useState } from "react";
import DashboardLayout from "../layouts/DashboardLayout";
import NotificationPanel from "../components/NotificationPanel";
import { useAuth } from "../context/AuthContext";

function Notifications() {
  const { user } = useAuth(); const isAdmin = ["Admin", "System Admin"].includes(user?.role); const key = user?.id ? `scna_notifications_${isAdmin ? "admin" : "user"}_${user.id}` : null;
  const [items, setItems] = useState([]);
  useEffect(() => { const timer = window.setTimeout(() => setItems(key ? JSON.parse(localStorage.getItem(key) || "[]") : []), 0); return () => window.clearTimeout(timer); }, [key]);
  useEffect(() => { if (key) localStorage.setItem(key, JSON.stringify(items)); }, [key, items]);
  const unread = useMemo(() => items.filter((item) => !item.read).length, [items]);
  return <DashboardLayout><div className="profile-page"><header><h1>Notifications</h1><p>{isAdmin ? "System and administration updates for your SCNA workspace." : "Your collaboration, research, and account updates."}</p></header><section className="notification-page-card"><NotificationPanel notifications={items} unreadCount={unread} onRead={(id) => setItems((list) => list.map((item) => item.id === id ? { ...item, read: true } : item))} onReadAll={() => setItems((list) => list.map((item) => ({ ...item, read: true })))} onClear={() => setItems([])} onViewAll={() => {}} /></section></div></DashboardLayout>;
}
export default Notifications;
