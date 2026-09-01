import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  FaUserGraduate,
  FaUser,
  FaEnvelope,
  FaLock,
  FaEye,
  FaEyeSlash,
} from "react-icons/fa";
import { registerUser } from "../services/authService";
import "./../styles/login.css";

function Register() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
    role: "Researcher",
    institution: "",
    department: "",
  });

  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("error");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const passwordsDoNotMatch = Boolean(formData.confirmPassword) && formData.password !== formData.confirmPassword;

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleRegister = async (event) => {
    event.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      setMessageType("error");
      setMessage("The passwords do not match. Please type the same password in both fields.");
      return;
    }

    setIsSubmitting(true);
    setMessage("");
    try {
      await registerUser({ full_name: formData.fullName, email: formData.email, password: formData.password, role: formData.role, institution: formData.institution || null, department: formData.department || null });
      setMessageType("success");
      setMessage("Verification code sent. Verify your email before your account can be approved.");

      setTimeout(() => {
        navigate(`/verify-email?email=${encodeURIComponent(formData.email)}`);
      }, 1000);

    } catch (error) {
      setMessageType("error");
      setMessage(
        error.response?.data?.detail || (error.request
          ? "Cannot reach the backend. Start FastAPI at http://127.0.0.1:8000, then try again."
          : "Registration failed. Please try again.")
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="login-container">
      <section className="login-card">
        <div className="logo">
          <FaUserGraduate />
        </div>

        <h1 className="title">Create an account</h1>

        <p className="subtitle">
          Join the Scientific Collaboration Network Analyzer
        </p>

        <form onSubmit={handleRegister}>
          <div className="input-group">
            <label>Full Name</label>

            <div className="input-box">
              <FaUser className="icon" />

              <input
                type="text"
                name="fullName"
                placeholder="Enter your full name"
                value={formData.fullName}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="input-group">
            <label>Role / User Type</label>
            <div className="input-box"><select name="role" value={formData.role} onChange={handleChange}><option>Researcher</option><option>Student</option><option>Collaborator</option><option>Institution Admin</option><option>Reviewer</option><option>Publisher</option></select></div>
          </div>

          <div className="input-group">
            <label>Institution <small>(optional)</small></label>
            <div className="input-box"><input type="text" name="institution" value={formData.institution} onChange={handleChange} placeholder="Your institution" /></div>
          </div>

          <div className="input-group">
            <label>Department <small>(optional)</small></label>
            <div className="input-box"><input type="text" name="department" value={formData.department} onChange={handleChange} placeholder="Your department" /></div>
          </div>

          <div className="input-group">
            <label>Email</label>

            <div className="input-box">
              <FaEnvelope className="icon" />

              <input
                type="email"
                name="email"
                placeholder="Enter your email"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="input-group">
            <label>Password</label>

            <div className="input-box">
              <FaLock className="icon" />

              <input
                type={showPassword ? "text" : "password"}
                name="password"
                placeholder="Enter password"
                value={formData.password}
                onChange={handleChange}
                required
                minLength="8"
              />
              <button className="password-toggle" type="button" aria-label={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword((current) => !current)}>{showPassword ? <FaEyeSlash /> : <FaEye />}</button>
            </div>
            <p className="password-hint">Use at least 8 characters and one special symbol, such as @, #, ! or $.</p>
          </div>

          <div className="input-group">
            <label>Confirm Password</label>

            <div className={`input-box ${passwordsDoNotMatch ? "input-box--error" : ""}`}>
              <FaLock className="icon" />

              <input
                type={showConfirmPassword ? "text" : "password"}
                name="confirmPassword"
                placeholder="Confirm password"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
              />
              <button className="password-toggle" type="button" aria-label={showConfirmPassword ? "Hide confirm password" : "Show confirm password"} onClick={() => setShowConfirmPassword((current) => !current)}>{showConfirmPassword ? <FaEyeSlash /> : <FaEye />}</button>
            </div>
            {passwordsDoNotMatch && <p className="field-error" role="alert">Passwords do not match.</p>}
          </div>

          {message && (
            <div className={`auth-message auth-message--${messageType}`} role="alert"><strong>{messageType === "success" ? "Registration successful" : "Please check your details"}</strong><span>{message}</span></div>
          )}

          <button type="submit" className="login-btn" disabled={isSubmitting || passwordsDoNotMatch}>
            {isSubmitting ? "Creating account..." : "Create Account"}
          </button>
        </form>

        <p className="register-text">
          Already have an account? <Link to="/">Login</Link>
        </p>
      </section>
    </main>
  );
}

export default Register;
