import api from"./api";
export const getConferences=async()=>(await api.get("/conferences")).data;
export const createConference=async(data)=>(await api.post("/conferences",data)).data;
export const updateConference=async(id,data)=>(await api.put(`/conferences/${id}`,data)).data;
export const deleteConference=async(id)=>api.delete(`/conferences/${id}`);
export const registerConference=async id=>(await api.post(`/conferences/${id}/register`)).data;
export const unregisterConference=async id=>(await api.delete(`/conferences/${id}/register`)).data;
export const getConferenceParticipants=async id=>(await api.get(`/conferences/${id}/participants`)).data;
