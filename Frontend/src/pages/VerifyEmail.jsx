import { useState } from "react";
import { FaEnvelopeOpenText } from "react-icons/fa";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { resendVerification, verifyEmail } from "../services/authService";
import "../styles/login.css";

function VerifyEmail() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState(searchParams.get("email") || "");
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("error");
  const [submitting, setSubmitting] = useState(false);
  const [resending, setResending] = useState(false);
  const verify = async (event) => { event.preventDefault(); setSubmitting(true); setMessage(""); try { const result = await verifyEmail(email, code); setMessageType("success"); setMessage(result.message); window.setTimeout(() => navigate("/"), 1200); } catch (error) { setMessageType("error"); setMessage(error.response?.data?.detail || "We could not verify this code."); } finally { setSubmitting(false); } };
  const resend = async () => { if (!email) { setMessageType("error"); setMessage("Enter your email address first."); return; } setResending(true); setMessage(""); try { const result = await resendVerification(email); setMessageType("success"); setMessage(result.message); } catch (error) { setMessageType("error"); setMessage(error.response?.data?.detail || "Could not resend the code."); } finally { setResending(false); } };
  return <main className="login-container"><section className="login-card"><div className="logo"><FaEnvelopeOpenText /></div><h1 className="title">Verify your email</h1><p className="subtitle">Enter the six-digit code sent to your email address.</p><form onSubmit={verify}><div className="input-group"><label>Email</label><div className="input-box"><input required type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" /></div></div><div className="input-group"><label>Verification code</label><div className="input-box"><input required inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength="6" value={code} onChange={(event) => setCode(event.target.value.replace(/\D/g, ""))} placeholder="123456" /></div><p className="password-hint">The code expires in 10 minutes. You have five attempts.</p></div>{message && <div className={`auth-message auth-message--${messageType}`} role="alert"><strong>{messageType === "success" ? "Email verified" : "Verification unsuccessful"}</strong><span>{message}</span></div>}<button className="login-btn" disabled={submitting}>{submitting ? "Verifying..." : "Verify email"}</button></form><p className="register-text">Did not receive a code? <button type="button" className="auth-inline-button" disabled={resending} onClick={resend}>{resending ? "Sending..." : "Resend code"}</button></p><p className="register-text"><Link to="/">Back to Login</Link></p></section></main>;
}
export default VerifyEmail;
