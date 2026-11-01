"use client";

import { useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { IntegrationCard } from "@/components/integrations/IntegrationCard";
import { IntegrationModal } from "@/components/integrations/IntegrationModal";

interface Integration {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  status: "available" | "coming-soon";
  statusLabel?: string;
}

export default function IntegrationsPage() {
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);

  const integrations: Integration[] = [
    {
      id: "naukri",
      name: "Naukri",
      description: "Connect to Naukri to automatically source top candidates for your open positions",
      icon: "briefcase",
      color: "#6366f1",
      status: "available",
      statusLabel: "Connected",
    },
    {
      id: "Drive",
      name: "Drive",
      description: "Connect to Drive for advanced candidate sourcing and professional networking",
      icon: "network",
      color: "#7c3aed",
      status: "available",
      statusLabel: "Connect Now",
    },
    {
      id: "indeed",
      name: "Indeed",
      description: "Connect to Indeed to access a large pool of qualified candidates and job applicants",
      icon: "briefcase",
      color: "#7c3aed",
      status: "coming-soon",
    },
    {
      id: "unstop",
      name: "Unstop",
      description: "Connect to Unstop to source candidates from campus recruiting and talent pool",
      icon: "network",
      color: "#7c3aed",
      status: "coming-soon",
    },

    {
      id: "linkedin",
      name: "LinkedIn",
      description: "Connect to LinkedIn for advanced candidate sourcing and professional networking",
      icon: "network",
      color: "#7c3aed",
      status: "coming-soon",
    },
  ];

  return (
    <>
      <TopBar
        title="Integrations"
        subtitle="Choose the data source tools you want to configure"
      />

      <div className="w-full">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {integrations.map((integration) => (
            <IntegrationCard
              key={integration.id}
              integration={integration}
              onClick={() => setSelectedIntegration(integration)}
            />
          ))}
        </div>

        {/* Coming Soon Notice */}
        <div className="mt-12 text-center">
          <p className="text-sm text-[var(--hp-text-muted)]">
            More integrations coming soon. Stay tuned!
          </p>
        </div>
      </div>

      {/* Integration Modal */}
      {selectedIntegration && (
        <IntegrationModal
          integration={selectedIntegration}
          onClose={() => setSelectedIntegration(null)}
        />
      )}
    </>
  );
}
