import api from "./api";

export const loginUser = async (email, password) => {
  const response = await api.post("/users/login", {
    email,
    password,
  });

  return response.data;
};

export const registerUser = async (registration) => {
  const response = await api.post("/users/register", registration);

  return response.data;
};

export const verifyEmail = async (email, code) => (await api.post("/users/verify-email", { email, code })).data;
export const resendVerification = async (email) => (await api.post("/users/resend-verification", { email })).data;
export const requestPasswordReset = async (identifier) => (await api.post("/users/password-reset/request", { identifier })).data;
export const confirmPasswordReset = async (identifier, code, newPassword) => (await api.post("/users/password-reset/confirm", { identifier, code, new_password: newPassword })).data;

export const getCurrentUser = async () => (await api.get("/users/me")).data;
export const updateCurrentUser = async (profile) => (await api.put("/users/me", profile)).data;
export const verifyCurrentPassword = async (currentPassword) => (await api.post("/users/me/password/verify", { current_password: currentPassword })).data;
export const changeCurrentPassword = async (currentPassword, newPassword) => (await api.put("/users/me/password", { current_password: currentPassword, new_password: newPassword })).data;
export const logoutUser = async () => (await api.post("/users/logout")).data;
