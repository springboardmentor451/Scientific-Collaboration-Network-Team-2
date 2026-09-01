import api from "./api";
export const getPublications = async () => (await api.get("/publications")).data;
export const createPublication = async (data) => (await api.post("/publications", data)).data;
export const updatePublication = async (id, data) => (await api.put(`/publications/${id}`, data)).data;
export const deletePublication = async (id) => api.delete(`/publications/${id}`);
export const uploadPublicationDocument = async (id, file) => {
  const body = new FormData();
  body.append("file", file);
  return (await api.post(`/publications/${id}/upload`, body, { headers: { "Content-Type": "multipart/form-data" } })).data;
};
export const assignPublicationAuthor = async (id, researcherId) => (await api.post(`/publications/${id}/authors/${researcherId}`)).data;
export const removePublicationAuthor = async (id, researcherId) => (await api.delete(`/publications/${id}/authors/${researcherId}`)).data;
export const openPublicationDocument = async (id) => {
  const response = await api.get(`/publications/${id}/document`, { responseType: "blob" });
  const url = URL.createObjectURL(response.data);
  window.open(url, "_blank", "noopener,noreferrer");
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
};
