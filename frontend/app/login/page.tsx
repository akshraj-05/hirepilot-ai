"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { loginUser, signupUser } from "@/utils/api";
import { setUser } from "@/utils/auth";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: { preventDefault(): void }) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = mode === "login"
        ? await loginUser(email, password)
        : await signupUser(email, password, name);
      setUser(user);
      router.replace("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : mode === "login" ? "Login failed" : "Signup failed");
    } finally {
      setLoading(false);
    }
  }

  function switchMode() {
    setMode(m => m === "login" ? "signup" : "login");
    setError("");
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--hp-surface)] px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--hp-accent)] text-lg font-bold text-white">
            HP
          </div>
          <div className="text-center">
            <h1 className="text-xl font-semibold text-[var(--hp-text)]">HirePilot AI</h1>
            <p className="text-sm text-[var(--hp-text-muted)]">
              {mode === "login" ? "Sign in to your workspace" : "Create your account"}
            </p>
          </div>
        </div>

        <div
          className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] p-6"
          style={{ boxShadow: "var(--hp-shadow)" }}
        >
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {mode === "signup" && (
              <div className="flex flex-col gap-1.5">
                <label htmlFor="name" className="text-sm font-medium text-[var(--hp-text)]">
                  Name
                </label>
                <input
                  id="name"
                  type="text"
                  autoComplete="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your full name"
                  className="rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface)] px-3 py-2 text-sm text-[var(--hp-text)] placeholder:text-[var(--hp-text-muted)] outline-none focus:border-[var(--hp-accent)] focus:ring-2 focus:ring-[var(--hp-accent-muted)] transition-colors"
                />
              </div>
            )}

            <div className="flex flex-col gap-1.5">
              <label htmlFor="email" className="text-sm font-medium text-[var(--hp-text)]">
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface)] px-3 py-2 text-sm text-[var(--hp-text)] placeholder:text-[var(--hp-text-muted)] outline-none focus:border-[var(--hp-accent)] focus:ring-2 focus:ring-[var(--hp-accent-muted)] transition-colors"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="password" className="text-sm font-medium text-[var(--hp-text)]">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface)] px-3 py-2 text-sm text-[var(--hp-text)] placeholder:text-[var(--hp-text-muted)] outline-none focus:border-[var(--hp-accent)] focus:ring-2 focus:ring-[var(--hp-accent-muted)] transition-colors"
              />
            </div>

            {error && (
              <p className="rounded-lg bg-[var(--hp-reject-bg)] px-3 py-2 text-sm text-[var(--hp-reject)]">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="mt-1 flex items-center justify-center gap-2 rounded-lg bg-[var(--hp-accent)] px-4 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading && (
                <svg className="hp-spinner h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
              )}
              {loading ? (mode === "login" ? "Signing in…" : "Creating account…") : (mode === "login" ? "Sign in" : "Create account")}
            </button>

            <p className="text-center text-sm text-[var(--hp-text-muted)]">
              {mode === "login" ? "Don't have an account?" : "Already have an account?"}{" "}
              <button
                type="button"
                onClick={switchMode}
                className="font-medium text-[var(--hp-accent)] hover:underline"
              >
                {mode === "login" ? "Sign up" : "Sign in"}
              </button>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
