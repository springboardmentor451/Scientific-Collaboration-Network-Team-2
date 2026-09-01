import { useEffect, useRef, useState } from "react";
import { FaArrowRight, FaPaperPlane, FaRobot, FaTimes } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";
import "../styles/Assistant.css";

const promptsFor = (role) => {
  if (["Admin", "System Admin"].includes(role)) return ["Show system statistics", "List publications", "Summarize collaborations", "How do reports work?"];
  if (role === "Institution Admin") return ["Summarize my institution", "Show institution publications", "List institution projects", "How do reports work?"];
  if (role === "Reviewer") return ["Show my pending reviews", "List my review decisions"];
  return ["List my publications", "How many projects do I have?", "Summarize my collaboration activity", "How do reports work?"];
};

function Assistant() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [messages, setMessages] = useState([]);
  const panelRef = useRef(null);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const onMouseDown = (event) => { if (panelRef.current && !panelRef.current.contains(event.target)) setOpen(false); };
    const onKeyDown = (event) => { if (event.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onMouseDown);
    document.addEventListener("keydown", onKeyDown);
    window.setTimeout(() => inputRef.current?.focus(), 0);
    return () => { document.removeEventListener("mousedown", onMouseDown); document.removeEventListener("keydown", onKeyDown); };
  }, [open]);

  useEffect(() => { listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" }); }, [messages, isSending]);

  const send = async (question = message) => {
    const trimmed = question.trim();
    if (!trimmed || isSending) return;
    setMessages((current) => [...current, { id: crypto.randomUUID(), type: "user", text: trimmed }]);
    setMessage(""); setIsSending(true);
    try {
      const response = await api.post("/assistant/chat", { message: trimmed });
      setMessages((current) => [...current, { id: crypto.randomUUID(), type: "assistant", text: response.data.answer, link: response.data.link }]);
    } catch (error) {
      const detail = error.response?.status === 401 ? "Your session has expired. Please log in again." : error.response?.data?.detail || "The assistant is temporarily unavailable. Please try again.";
      setMessages((current) => [...current, { id: crypto.randomUUID(), type: "error", text: detail }]);
    } finally { setIsSending(false); }
  };

  if (!user) return null;
  return <div className="scna-assistant" ref={panelRef}>
    {open && <section className="scna-assistant__panel" role="dialog" aria-modal="false" aria-label="SCNA Assistant">
      <header className="scna-assistant__header"><div><span className="scna-assistant__icon"><FaRobot /></span><div><strong>SCNA Assistant</strong><small>Answers from your permitted records</small></div></div><button type="button" aria-label="Close assistant" onClick={() => setOpen(false)}><FaTimes /></button></header>
      <div className="scna-assistant__messages" ref={listRef} aria-live="polite">
        {!messages.length && <div className="scna-assistant__welcome"><FaRobot /><p>Ask about your SCNA work. I only use records your account is allowed to access.</p><div>{promptsFor(user.role).map((prompt) => <button key={prompt} type="button" onClick={() => send(prompt)}>{prompt}</button>)}</div></div>}
        {messages.map((item) => <article className={`scna-assistant__message scna-assistant__message--${item.type}`} key={item.id}><p>{item.text}</p>{item.link && <button type="button" onClick={() => { setOpen(false); navigate(item.link); }}>Open related page <FaArrowRight /></button>}</article>)}
        {isSending && <div className="scna-assistant__typing"><span /><span /><span /> Finding permitted records…</div>}
      </div>
      <form className="scna-assistant__composer" onSubmit={(event) => { event.preventDefault(); send(); }}><input ref={inputRef} value={message} maxLength="500" onChange={(event) => setMessage(event.target.value)} placeholder="Ask about your SCNA records…" aria-label="Ask SCNA Assistant" disabled={isSending} /><button type="submit" aria-label="Send question" disabled={isSending || !message.trim()}><FaPaperPlane /></button></form>
    </section>}
    <button type="button" className="scna-assistant__launcher" onClick={() => setOpen((current) => !current)} aria-label={open ? "Close SCNA Assistant" : "Open SCNA Assistant"} aria-expanded={open}><FaRobot /><span>Assistant</span></button>
  </div>;
}

export default Assistant;
