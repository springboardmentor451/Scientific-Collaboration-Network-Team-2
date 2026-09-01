import api from "./api";
export const getNetworkGraph = async () => (await api.get("/network/graph")).data;
