import api from "./api";

export const getResearchers = async () => (await api.get("/researchers")).data;
export const createResearcher = async (researcher) => (await api.post("/researchers", researcher)).data;
export const updateResearcher = async (researcherId, researcher) => (await api.put(`/researchers/${researcherId}`, researcher)).data;
export const deleteResearcher = async (researcherId) => api.delete(`/researchers/${researcherId}`);
