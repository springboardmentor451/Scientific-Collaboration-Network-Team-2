import api from "./api";
export const sendCollaborationRequest = async (researcherId, message) => (await api.post("/collaborations/request", { researcher_id: researcherId, message })).data;
export const getSentRequests = async () => (await api.get("/collaborations/requests/sent")).data;
export const getReceivedRequests = async () => (await api.get("/collaborations/requests/received")).data;
export const getMyCollaborations = async () => (await api.get("/collaborations/my")).data;
export const respondToRequest = async (id, decision) => (await api.put(`/collaborations/requests/${id}/${decision}`)).data;
export const cancelCollaborationRequest = async (id) => (await api.put(`/collaborations/requests/${id}/cancel`)).data;
