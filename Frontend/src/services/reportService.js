import api from "./api";
export const getMyReport = async () => (await api.get("/reports/my")).data;
export const getGeneratedReports = async () => (await api.get("/reports/generated")).data;
export const generateInstitutionReport = async (institutionId) => (await api.post(`/reports/generated/${institutionId}`)).data;
export const deleteGeneratedReport = async (id) => api.delete(`/reports/generated/${id}`);
export const downloadGeneratedReport = async (id, format) => {
  const response = await api.get(`/reports/generated/${id}/export.${format}`, { responseType: "blob" });
  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url; link.download = `scna-report-${id}.${format}`; link.click();
  URL.revokeObjectURL(url);
};
