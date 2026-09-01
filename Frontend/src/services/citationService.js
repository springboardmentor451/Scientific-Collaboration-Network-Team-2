import api from "./api";
export const getAdminCitations = async () => (await api.get("/citations/admin/all")).data;
export const getCitation = async (id) => (await api.get(`/citations/${id}`)).data;
export const updateCitation = async (id, data) => (await api.put(`/citations/${id}`, data)).data;
