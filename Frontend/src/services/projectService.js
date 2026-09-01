import api from "./api";
export const getProjects = async () => (await api.get("/projects")).data;
export const createProject = async (data) => (await api.post("/projects", data)).data;
export const getProject = async (id) => (await api.get(`/projects/${id}`)).data;
export const updateProject = async (id, data) => (await api.put(`/projects/${id}`, data)).data;
export const deleteProject = async (id) => api.delete(`/projects/${id}`);
export const getAdminProjects = async () => (await api.get("/projects/admin/all")).data;
export const addProjectMember = async (id, researcherId) => (await api.post(`/projects/${id}/assignments`, null, { params: { researcher_id: researcherId } })).data;
export const removeProjectMember = async (id, researcherId) => (await api.delete(`/projects/${id}/assignments/${researcherId}`)).data;
