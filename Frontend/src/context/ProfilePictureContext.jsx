/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useState } from "react";
import { useAuth } from "./AuthContext";

const ProfilePictureContext = createContext(null);
const keyFor = (user) => user?.id ? `profilePicture_${user.id}` : null;

export function ProfilePictureProvider({ children }) {
  const { user } = useAuth();
  const storageKey = keyFor(user);
  const [profilePicture, setProfilePictureState] = useState(null);
  useEffect(() => { const timer = window.setTimeout(() => setProfilePictureState(storageKey ? localStorage.getItem(storageKey) : null), 0); return () => window.clearTimeout(timer); }, [storageKey]);
  const setProfilePicture = (imageData) => { if (!storageKey) return; if (imageData) localStorage.setItem(storageKey, imageData); else localStorage.removeItem(storageKey); setProfilePictureState(imageData || null); };
  return <ProfilePictureContext.Provider value={{ profilePicture, setProfilePicture }}>{children}</ProfilePictureContext.Provider>;
}

export const useProfilePicture = () => useContext(ProfilePictureContext);
