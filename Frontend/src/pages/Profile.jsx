import { useRef, useState } from "react";
import { FaCamera, FaKey, FaShieldAlt, FaSignOutAlt, FaTrash, FaUser } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../layouts/DashboardLayout";
import PasswordChangeModal from "../components/PasswordChangeModal";
import { useAuth } from "../context/AuthContext";
import { updateCurrentUser } from "../services/authService";
import { useProfilePicture } from "../context/ProfilePictureContext";
import "../styles/profile.css";
import "../styles/security-profile.css";

const isSystemAdmin = (role) => ["Admin", "System Admin"].includes(role);
const PasswordButton = ({ onClick }) => <button type="button" className="ui-button ui-button--secondary profile-password-button" onClick={onClick}><FaKey /> Change password</button>;
const SessionControl = () => { const { logout } = useAuth(); const navigate = useNavigate(); const signOut = () => { logout(); navigate("/", { replace: true }); }; return <section className="profile-session-card"><div><strong>Current session</strong><span>Securely sign out from this browser when you are finished.</span></div><button type="button" className="ui-button ui-button--secondary" onClick={signOut}><FaSignOutAlt /> Log out</button></section>; };

function AdminAccount({ user, onChangePassword }) {
  const joined = user.created_at ? new Date(user.created_at).toLocaleDateString() : "Account record available";
  return <><header><h1>System Admin Account</h1><p>Secure account details for this privileged platform administrator.</p></header><section className="profile-form admin-account-card"><div className="profile-identity"><div className="profile-photo profile-photo--admin"><FaShieldAlt /></div><span><strong>{user.full_name}</strong><small>System Admin · {user.email}</small></span><PasswordButton onClick={onChangePassword} /></div><div className="account-summary"><article><span>Role</span><strong>{user.role}</strong></article><article><span>Email</span><strong>{user.email}</strong></article><article><span>Account status</span><strong className={user.is_active ? "account-status--good" : "account-status--bad"}>{user.is_active ? "Active" : "Inactive"}</strong></article><article><span>Email verification</span><strong className={user.email_verified ? "account-status--good" : "account-status--bad"}>{user.email_verified ? "Verified" : "Not verified"}</strong></article><article><span>Member since</span><strong>{joined}</strong></article><article><span>Access scope</span><strong>Platform administration</strong></article></div></section></>;
}

function UserProfile({ user, onChangePassword }) {
  const { updateUser } = useAuth();
  const { profilePicture, setProfilePicture } = useProfilePicture();
  const fileRef = useRef(null);
  const [form, setForm] = useState({ full_name: user.full_name, institution: user.institution || "", department: user.department || "", bio: user.bio || "", research_interests: (user.research_interests || []).join(", "), skills: (user.skills || []).join(", ") });
  const [message, setMessage] = useState(""); const [error, setError] = useState("");
  const change = ({ target: { name, value } }) => setForm((current) => ({ ...current, [name]: value }));
  const save = async (event) => { event.preventDefault(); setMessage(""); setError(""); try { const list = (value) => value.split(",").map((item) => item.trim()).filter(Boolean); const updated = await updateCurrentUser({ ...form, institution: form.institution || null, department: form.department || null, research_interests: list(form.research_interests), skills: list(form.skills) }); updateUser(updated); setMessage("Profile updated successfully."); } catch (requestError) { setError(requestError.response?.data?.detail || "Could not update profile."); } };
  const selectPicture = (event) => { const file = event.target.files?.[0]; if (!file) return; if (!file.type.match(/^image\/(jpeg|png|webp)$/)) { setError("Please select a valid image file."); return; } if (file.size > 5 * 1024 * 1024) { setError("Image size must be less than 5 MB."); return; } const reader = new FileReader(); reader.onload = () => { setProfilePicture(reader.result); setMessage("Profile picture updated."); setError(""); }; reader.readAsDataURL(file); event.target.value = ""; };
  return <><header><h1>My Profile</h1><p>Manage the information other researchers see about you.</p></header><form className="profile-form" onSubmit={save}><div className="profile-identity"><div className="profile-photo">{profilePicture ? <img src={profilePicture} alt="Your profile" /> : <FaUser />}</div><span><strong>{user.full_name}</strong><small>{user.role} · {user.email}</small><span className="profile-photo-actions"><input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={selectPicture} /><button type="button" className="ui-button ui-button--secondary" onClick={() => fileRef.current?.click()}><FaCamera /> {profilePicture ? "Change picture" : "Add profile picture"}</button>{profilePicture && <button type="button" className="ui-button ui-button--danger" onClick={() => { setProfilePicture(null); setMessage("Profile picture removed."); }}><FaTrash /> Remove</button>}</span></span><PasswordButton onClick={onChangePassword} /></div>{error && <p className="profile-error">{error}</p>}{message && <p className="profile-success">{message}</p>}<div className="profile-grid"><label>Full name<input name="full_name" value={form.full_name} onChange={change} required /></label><label>Email<input value={user.email} disabled /></label><label>Role<input value={user.role} disabled /></label><label>Institution<input name="institution" value={form.institution} onChange={change} /></label><label>Department<input name="department" value={form.department} onChange={change} /></label><label className="profile-wide">Bio<textarea name="bio" value={form.bio} onChange={change} rows="4" /></label><label>Research interests<input name="research_interests" value={form.research_interests} onChange={change} placeholder="AI, Healthcare" /></label><label>Skills / expertise<input name="skills" value={form.skills} onChange={change} placeholder="Python, Data Analysis" /></label></div><button className="ui-button ui-button--primary">Save profile</button></form></>;
}

function Profile() {
  const { user } = useAuth();
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);
  return <DashboardLayout><div className="profile-page">{isSystemAdmin(user.role) ? <AdminAccount user={user} onChangePassword={() => setPasswordModalOpen(true)} /> : <UserProfile user={user} onChangePassword={() => setPasswordModalOpen(true)} />}<SessionControl /><PasswordChangeModal open={passwordModalOpen} onClose={() => setPasswordModalOpen(false)} user={user} /></div></DashboardLayout>;
}

export default Profile;
