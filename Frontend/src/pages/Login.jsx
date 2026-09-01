import "./../styles/login.css";
import { Link, useNavigate } from "react-router-dom";
import { FaUserGraduate, FaEnvelope, FaLock, FaEye, FaEyeSlash } from "react-icons/fa";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [needsVerification, setNeedsVerification] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => { localStorage.removeItem("scna_remembered_email"); }, []);

  const handleLogin = async (event) => {
    event.preventDefault();
    setIsSubmitting(true);
    setMessage("");
    setNeedsVerification(false);

    try {
      const authenticatedUser = await login(email, password, false);
      navigate(["Admin", "System Admin"].includes(authenticatedUser.role) ? "/admin" : "/dashboard");
    } catch (error) {
      const detail = error.response?.data?.detail || "We could not sign you in. Please check your email and password.";
      setMessage(detail);
      setNeedsVerification(detail.toLowerCase().includes("verify your email"));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="login-container">
      <section className="login-card" aria-labelledby="login-title">
        <div className="logo" aria-hidden="true">
          <FaUserGraduate />
        </div>

        <h1 id="login-title" className="title">
          Scientific Collaboration
        </h1>

        <p className="subtitle">Network Analyzer</p>

        <form onSubmit={handleLogin}>
          <div className="input-group">
            <label htmlFor="email">Email</label>

            <div className="input-box">
              <FaEnvelope className="icon" aria-hidden="true" />

              <input
                id="email"
                name="email"
                type="email"
                placeholder="Enter your email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </div>
          </div>

          <div className="input-group">
            <label htmlFor="password">Password</label>

            <div className="input-box">
              <FaLock className="icon" aria-hidden="true" />

              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
              <button className="password-toggle" type="button" aria-label={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword((current) => !current)}>{showPassword ? <FaEyeSlash /> : <FaEye />}</button>
            </div>
          </div>

          <div className="login-options login-options--single"><Link to="/forgot-password">Forgot password?</Link></div>

          {message && (
            <div className="auth-message auth-message--error" role="alert"><strong>Login unsuccessful</strong><span>{message}</span></div>
          )}

          {needsVerification && <p className="register-text">Already received a code? <Link to={`/verify-email?email=${encodeURIComponent(email)}`}>Verify email</Link></p>}

          <button type="submit" className="login-btn" disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Log in"}
          </button>
        </form>

        <p className="register-text">
          Don&apos;t have an account? <Link to="/register">Register</Link>
        </p>
      </section>
    </main>
  );
}

export default Login;
