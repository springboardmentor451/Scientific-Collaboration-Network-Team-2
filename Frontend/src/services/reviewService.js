import api from "./api";
export const getMyReviewQueue = async () => (await api.get("/reviews/my-queue")).data;
export const decideReview = async (id, data) => (await api.post(`/reviews/${id}/decision`, data)).data;
export const getReviews = async () => (await api.get("/reviews")).data;
export const assignReview = async (data) => (await api.post("/reviews/assign", data)).data;
