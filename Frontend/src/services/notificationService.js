import api from "./api";
export const getMyNotifications = async () => (await api.get("/notifications/my")).data;
export const markAllNotificationsRead = async () => (await api.put("/notifications/read-all")).data;
export const markNotificationRead = async (id) => (await api.put(`/notifications/${id}/read`)).data;
export const sendAnnouncement = async (data) => (await api.post("/notifications/announcement", data)).data;
