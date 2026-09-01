import api from"./api";
export const getInstitutions=async()=>(await api.get("/institutions")).data;
export const createInstitution=async(data)=>(await api.post("/institutions",data)).data;
export const updateInstitution=async(id,data)=>(await api.put(`/institutions/${id}`,data)).data;
export const deleteInstitution=async(id)=>api.delete(`/institutions/${id}`);
export const getInstitutionReport=async(id)=>(await api.get(`/institutions/${id}/report`)).data;
