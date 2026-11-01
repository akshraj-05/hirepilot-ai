"use client";

import { useState, useEffect } from "react";
import {
  testNaukriConnection,
  connectNaukri,
  listIntegrations,
  disconnectIntegration,
} from "@/utils/api";

interface NaukriConfig {
  client_id: string;
  client_secret: string;
}

export function NaukriConfiguration() {
  const [credentials, setCredentials] = useState<NaukriConfig>({
    client_id: "",
    client_secret: "",
  });
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [connected, setConnected] = useState(false);
  const [integrationId, setIntegrationId] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");

  // Check if already connected on mount
  const checkConnection = async () => {
    try {
      const integrations = await listIntegrations();
      console.log("Integrations:", integrations);
      const naukriIntegration = integrations.find(
        (i: any) => i.platform === "naukri"
      );
      if (naukriIntegration) {
        console.log("Found Naukri integration:", naukriIntegration);
        setConnected(true);
        setIntegrationId(naukriIntegration.id);
        setMessage("Successfully connected to Naukri");
      } else {
        console.log("No Naukri integration found");
        setConnected(false);
        setIntegrationId("");
      }
    } catch (err) {
      console.error("Failed to check connection:", err);
      setConnected(false);
      setIntegrationId("");
    }
  };

  // Call checkConnection on component mount
  useEffect(() => {
    checkConnection();
  }, []);

  const handleTestConnection = async () => {
    if (!credentials.client_id || !credentials.client_secret) {
      setError("Please enter Client ID and Client Secret");
      return;
    }

    setTesting(true);
    setError("");
    setMessage("");

    try {
      const result = await testNaukriConnection(credentials);
      if (result.success) {
        setMessage("Connection test successful!");
      } else {
        setError(result.error || "Connection test failed");
      }
    } catch (err: any) {
      setError(err.message || "Failed to test connection");
    } finally {
      setTesting(false);
    }
  };

  const handleConnect = async () => {
    if (!credentials.client_id || !credentials.client_secret) {
      setError("Please enter Client ID and Client Secret");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const result = await connectNaukri(credentials);
      setConnected(true);
      setIntegrationId(result.id);
      setMessage("Successfully connected to Naukri!");
      setCredentials({ client_id: "", client_secret: "" });
    } catch (err: any) {
      setError(err.message || "Failed to connect");
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (!integrationId) return;

    try {
      await disconnectIntegration(integrationId);
      setConnected(false);
      setIntegrationId("");
      setMessage("");
      setError("Integration disconnected");
      setTimeout(() => setError(""), 3000);
    } catch (err: any) {
      setError(err.message || "Failed to disconnect");
    }
  };

  if (connected) {
    return (
      <div className="space-y-4">
        <div className="rounded-lg bg-green-50 p-4 text-green-800">
          <p className="text-sm font-medium">✓ Naukri is connected</p>
          <p className="text-xs opacity-75">
            You can now sync candidates from Naukri
          </p>
        </div>
        <button
          onClick={handleDisconnect}
          className="rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface)] px-4 py-2 text-sm font-medium text-[var(--hp-text)] hover:bg-[var(--hp-surface-elevated)]"
        >
          Disconnect
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <label
          htmlFor="naukri-client-id"
          className="block text-sm font-medium text-[var(--hp-text)] mb-1"
        >
          Client ID
        </label>
        <input
          id="naukri-client-id"
          type="text"
          value={credentials.client_id}
          onChange={(e) =>
            setCredentials({ ...credentials, client_id: e.target.value })
          }
          placeholder="Enter your Naukri Client ID"
          className="w-full rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface)] px-3 py-2 text-sm text-[var(--hp-text)] placeholder-[var(--hp-text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--hp-accent)]"
        />
      </div>

      <div>
        <label
          htmlFor="naukri-client-secret"
          className="block text-sm font-medium text-[var(--hp-text)] mb-1"
        >
          Client Secret
        </label>
        <input
          id="naukri-client-secret"
          type="password"
          value={credentials.client_secret}
          onChange={(e) =>
            setCredentials({ ...credentials, client_secret: e.target.value })
          }
          placeholder="Enter your Naukri Client Secret"
          className="w-full rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface)] px-3 py-2 text-sm text-[var(--hp-text)] placeholder-[var(--hp-text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--hp-accent)]"
        />
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-red-800 text-sm">
          {error}
        </div>
      )}

      {message && (
        <div className="rounded-lg bg-green-50 p-3 text-green-800 text-sm">
          {message}
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={handleTestConnection}
          disabled={testing || loading}
          className="flex-1 rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface)] px-4 py-2 text-sm font-medium text-[var(--hp-text)] hover:bg-[var(--hp-surface-elevated)] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {testing ? "Testing..." : "Test Connection"}
        </button>

        <button
          onClick={handleConnect}
          disabled={loading || testing}
          className="flex-1 rounded-lg bg-[var(--hp-accent)] px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Connecting..." : "Connect"}
        </button>
      </div>
    </div>
  );
}
