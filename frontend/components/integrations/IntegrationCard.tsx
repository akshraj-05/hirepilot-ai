"use client";

import React from "react";

interface Integration {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  status: "available" | "coming-soon";
  statusLabel?: string;
}

interface IntegrationCardProps {
  integration: Integration;
  onClick: () => void;
}

const IconComponent: React.FC<{ icon: string; color: string }> = ({ icon, color }) => {
  const icons: Record<string, React.ReactNode> = {
    briefcase: (
      <svg className="w-full h-full" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 6h-2.18c.11-.31.18-.645.18-1a2.996 2.996 0 0 0-5.824-1h-2.235A2.996 2.996 0 0 0 3.82 5c0 .355.07.69.18 1H4c-1.1 0-1.99.9-1.99 2v14c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-5-2c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm-5 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1z" />
      </svg>
    ),
    database: (
      <svg className="w-full h-full" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2c-5.33 4.55-8 6.75-8 11.8.0 5.23 3.582 8.2 8 8.2s8-2.97 8-8.2c0-5.05-2.67-7.25-8-11.8zm0 18c-3.35 0-6-1.57-6-3.5S8.65 13 12 13s6 1.5 6 3.5-2.65 3.5-6 3.5z" />
      </svg>
    ),
    cloud: (
      <svg className="w-full h-full" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4c-1.48 0-2.85.43-4.01 1.17l1.46 1.46C10.21 5.23 11.08 5 12 5c3.04 0 5.5 2.46 5.5 5.5v.5H19c2.05 0 3.71 1.66 3.71 3.71 0 1.71-1.04 3.17-2.36 3.87L20.88 19c2.11-.78 3.71-2.91 3.71-5.39.0-3.15-2.57-5.74-5.74-5.74l-.37-.01zM6.64 16.02C4.79 14.87 3.5 12.73 3.5 10.5c0-2.64 2.05-4.78 4.65-4.78.29 0 .57.02.85.07C9.16 4.3 10.63 3 12.5 3c2.05 0 3.71 1.66 3.71 3.71 0 .38-.06.75-.16 1.1 2.31.94 3.99 3.08 3.99 5.69C20 18.08 16.84 21 13.29 21H5.27c-2.04 0-3.71-1.66-3.71-3.71.01-1.73 1.05-3.22 2.58-3.89l1.5 1.62z" />
      </svg>
    ),
    shield: (
      <svg className="w-full h-full" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z" />
      </svg>
    ),
    target: (
      <svg className="w-full h-full" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5z" />
      </svg>
    ),
    network: (
      <svg className="w-full h-full" viewBox="0 0 24 24" fill="currentColor">
        <path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z" />
      </svg>
    ),
  };

  return (
    <div style={{ color }} className="flex items-center justify-center">
      {icons[icon] || icons.briefcase}
    </div>
  );
};

export function IntegrationCard({ integration, onClick }: IntegrationCardProps) {
  const isComingSoon = integration.status === "coming-soon";

  return (
    <div
      onClick={!isComingSoon ? onClick : undefined}
      className={`group relative rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] p-6 transition-all duration-200 ${
        !isComingSoon
          ? "cursor-pointer hover:border-[var(--hp-accent)] hover:shadow-lg hover:shadow-[var(--hp-accent-muted)]"
          : "opacity-60"
      }`}
    >
      {/* Icon */}
      <div className="mb-4 flex items-center justify-center">
        <div className="w-16 h-16 rounded-xl bg-white flex items-center justify-center overflow-hidden p-1">
    <img
      src={`/logos/${integration.id}.png`}
      alt={integration.name}
      className="w-full h-full object-contain"
    />
  </div>
      </div>

      {/* Content */}
      <div className="space-y-2">
        <h3 className="text-lg font-semibold text-[var(--hp-text)]">
          {integration.name}
        </h3>
        <p className="text-sm text-[var(--hp-text-muted)] leading-relaxed">
          {integration.description}
        </p>
      </div>

      {/* Status Badge */}
      <div className="mt-4">
        {isComingSoon ? (
          <div className="inline-block px-3 py-1 rounded-full text-xs font-medium text-[var(--hp-text-muted)] bg-[var(--hp-surface)]">
            Coming Soon
          </div>
        ) : (
          <div className="inline-block px-3 py-1 rounded-full text-xs font-medium text-white bg-[var(--hp-accent)]">
            {integration.statusLabel || "Connect"}
          </div>
        )}
      </div>

      {/* Hover Arrow */}
      {!isComingSoon && (
        <div className="absolute top-4 right-4 text-[var(--hp-text-muted)] group-hover:text-[var(--hp-accent)] transition-colors">
          <svg
            className="w-5 h-5 group-hover:translate-x-1 transition-transform"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 7l5 5m0 0l-5 5m5-5H6"
            />
          </svg>
        </div>
      )}
    </div>
  );
}
