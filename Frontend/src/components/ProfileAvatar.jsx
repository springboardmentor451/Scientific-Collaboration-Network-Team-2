import { FaUser } from "react-icons/fa";
import { useProfilePicture } from "../context/ProfilePictureContext";

function ProfileAvatar({ name, className = "profile-avatar" }) {
  const { profilePicture } = useProfilePicture();
  const initials = (name || "User").split(" ").filter(Boolean).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
  return <span className={className} aria-hidden="true">{profilePicture ? <img src={profilePicture} alt="" /> : initials || <FaUser />}</span>;
}
export default ProfileAvatar;
