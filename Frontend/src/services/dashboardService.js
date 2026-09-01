import api from "./api";
export const getMyDashboard = async () => (await api.get("/dashboard/me")).data;
