"use client";

import { useState, useRef, useEffect } from "react";

type Message = {
  role: "user" | "bot";
  text: string;
};

/** Returns a mock reply based on keywords in the user's message */
function getMockReply(input: string): string {
  const q = input.toLowerCase();

  if (q.includes("candidate") || q.includes("resume"))
    return "You can view all candidates in the Candidates section. Each profile shows match score, skills, and AI feedback.";
  if (q.includes("job") || q.includes("position") || q.includes("role"))
    return "Jobs are listed in the Jobs section. You can filter by status: open, closed, or paused.";
  if (q.includes("upload") || q.includes("resume") || q.includes("cv"))
    return "Go to the Upload page to upload resumes. HirePilot AI will analyse them and score candidates automatically.";
  if (q.includes("score") || q.includes("match"))
    return "Match scores are calculated by the AI based on how well a candidate's skills align with the job requirements.";
  if (q.includes("shortlist"))
    return "You can shortlist a candidate by clicking the Shortlist button on their profile page.";
  if (q.includes("reject"))
    return "Rejecting a candidate removes them from active consideration. You can always review them again later.";
  if (q.includes("help"))
    return "I can help with candidates, jobs, uploads, scores, and more. Just ask!";
  if (q.includes("hello") || q.includes("hi") || q.includes("hey"))
    return "Hi there! I'm HirePilot's assistant. Ask me anything about the platform.";

  return "I'm not sure about that yet — the AI backend is coming soon! For now, try asking about candidates, jobs, or uploads.";
}

export function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: "bot", text: "Hi! I'm HirePilot's assistant. Ask me anything about candidates, jobs, or uploads." },
  ]);
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSend() {
    const trimmed = inputValue.trim();
    if (!trimmed) return;

    // Add user message
    const userMsg: Message = { role: "user", text: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");

    // Add bot reply after a short delay (feels more natural)
    setTimeout(() => {
      const botMsg: Message = { role: "bot", text: getMockReply(trimmed) };
      setMessages((prev) => [...prev, botMsg]);
    }, 600);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") handleSend();
  }

  return (
    <>
      {/* ── Chat Panel ─────────────────────────────────────────────── */}
      {isOpen && (
        <div
          style={{
            position: "fixed",
            bottom: "80px",
            right: "24px",
            width: "340px",
            zIndex: 1000,
            background: "var(--hp-surface-elevated)",
            border: "1px solid var(--hp-border)",
            borderRadius: "var(--hp-radius)",
            boxShadow: "0 8px 30px rgb(15 23 42 / 0.15)",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          {/* Header */}
          <div
            style={{
              background: "var(--hp-accent)",
              color: "#fff",
              padding: "12px 16px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "18px" }}>🤖</span>
              <span style={{ fontWeight: 600, fontSize: "14px" }}>HirePilot Assistant</span>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              style={{
                background: "transparent",
                border: "none",
                color: "#fff",
                cursor: "pointer",
                fontSize: "18px",
                lineHeight: 1,
                padding: "2px 4px",
              }}
              aria-label="Close chat"
            >
              ×
            </button>
          </div>

          {/* Messages */}
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "12px 14px",
              display: "flex",
              flexDirection: "column",
              gap: "10px",
              maxHeight: "320px",
              background: "var(--hp-surface)",
            }}
          >
            {messages.map((msg, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                }}
              >
                <div
                  style={{
                    maxWidth: "80%",
                    padding: "8px 12px",
                    borderRadius: "12px",
                    fontSize: "13px",
                    lineHeight: "1.5",
                    background:
                      msg.role === "user"
                        ? "var(--hp-accent)"
                        : "var(--hp-surface-elevated)",
                    color: msg.role === "user" ? "#fff" : "var(--hp-text)",
                    border:
                      msg.role === "bot"
                        ? "1px solid var(--hp-border)"
                        : "none",
                  }}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div
            style={{
              padding: "10px 12px",
              borderTop: "1px solid var(--hp-border)",
              display: "flex",
              gap: "8px",
              background: "var(--hp-surface-elevated)",
            }}
          >
            <input
              type="text"
              placeholder="Ask something..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              style={{
                flex: 1,
                padding: "8px 12px",
                fontSize: "13px",
                border: "1px solid var(--hp-border)",
                borderRadius: "8px",
                outline: "none",
                color: "var(--hp-text)",
                background: "var(--hp-surface)",
              }}
            />
            <button
              onClick={handleSend}
              disabled={!inputValue.trim()}
              style={{
                padding: "8px 14px",
                background: "var(--hp-accent)",
                color: "#fff",
                border: "none",
                borderRadius: "8px",
                cursor: inputValue.trim() ? "pointer" : "not-allowed",
                fontSize: "13px",
                fontWeight: 600,
                opacity: inputValue.trim() ? 1 : 0.5,
              }}
            >
              Send
            </button>
          </div>
        </div>
      )}

      {/* ── Floating Toggle Button ──────────────────────────────────── */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        style={{
          position: "fixed",
          bottom: "24px",
          right: "24px",
          zIndex: 1001,
          width: "52px",
          height: "52px",
          borderRadius: "50%",
          background: "var(--hp-accent)",
          color: "#fff",
          border: "none",
          cursor: "pointer",
          fontSize: "22px",
          boxShadow: "0 4px 14px rgb(37 99 235 / 0.4)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transition: "transform 0.2s",
        }}
        aria-label="Toggle chat"
      >
        {isOpen ? "×" : "💬"}
      </button>
    </>
  );
}
