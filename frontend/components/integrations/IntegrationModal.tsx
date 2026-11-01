"use client";

import React from "react";
import { NaukriConfiguration } from "./NaukriConfiguration";
import { GoogleDriveConfiguration } from "./GoogleDriveConfiguration";

interface Integration {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  status: "available" | "coming-soon";
}

interface IntegrationModalProps {
  integration: Integration;
  onClose: () => void;
}

export function IntegrationModal({ integration, onClose }: IntegrationModalProps) {
  const renderIntegrationConfig = () => {
    switch (integration.id) {
      case "naukri":
        return <NaukriConfiguration />;
      case "Drive":
        return <GoogleDriveConfiguration />;
      default:
        return (
          <div className="rounded-lg bg-[var(--hp-surface)] px-4 py-3 text-sm text-[var(--hp-text-muted)]">
            This integration is coming soon. Please check back later!
          </div>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="relative max-h-[90vh] max-w-2xl w-full mx-4 rounded-lg bg-[var(--hp-surface-elevated)] shadow-xl overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 border-b border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-[var(--hp-text)]">
              {integration.name}
            </h2>
            <p className="mt-1 text-sm text-[var(--hp-text-muted)]">
              {integration.description}
            </p>
          </div>
          <button
            onClick={onClose}
            className="absolute top-4 right-4 rounded-lg p-1 text-[var(--hp-text-muted)] hover:text-[var(--hp-text)] hover:bg-[var(--hp-surface)] transition-colors"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-6">
          {renderIntegrationConfig()}
        </div>
      </div>
    </div>
  );
}
