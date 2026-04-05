"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { api } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { ProjectStatusBadge, TrustBadge } from "@/components/ui/Badge";
import type { ClientScore, Project, TrustTier } from "@/types";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [clientTiers, setClientTiers] = useState<Record<string, TrustTier>>({});

  useEffect(() => {
    api
      .get<Project[]>("/api/projects/")
      .then(({ data }) => {
        setProjects(data);
        // Fetch trust tiers for unique client emails
        const emails = Array.from(new Set(data.map((p) => p.clientEmail)));
        emails.forEach((email) => {
          api
            .get<ClientScore>(
              `/api/ratings/client-score/${encodeURIComponent(email)}`,
            )
            .then(({ data: score }) => {
              if (score.totalProjects > 0) {
                setClientTiers((prev) => ({
                  ...prev,
                  [email]: score.trustTier,
                }));
              }
            })
            .catch(() => {});
        });
      })
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
        <Link
          href="/dashboard/projects/new"
          className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" /> New Project
        </Link>
      </div>

      {isLoading ? (
        <div className="mt-8 text-center text-gray-500">Loading...</div>
      ) : projects.length === 0 ? (
        <div className="mt-12 text-center">
          <p className="text-gray-500">No projects yet.</p>
          <Link
            href="/dashboard/projects/new"
            className="mt-2 inline-block text-sm font-medium text-blue-600 hover:text-blue-700"
          >
            Create your first project
          </Link>
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {projects.map((p) => (
            <Link
              key={p.id}
              href={`/dashboard/projects/${p.id}`}
              className="block rounded-xl border bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">{p.title}</h3>
                  <div className="mt-0.5 flex items-center gap-2">
                    <span className="text-sm text-gray-500">
                      {p.clientEmail}
                    </span>
                    {clientTiers[p.clientEmail] && (
                      <TrustBadge tier={clientTiers[p.clientEmail]} />
                    )}
                  </div>
                </div>
                <ProjectStatusBadge status={p.status} />
              </div>
              <div className="mt-3 flex items-center gap-4 text-sm text-gray-500">
                <span className="font-medium text-gray-900">
                  {formatCurrency(p.totalAmountCents)}
                </span>
                <span>Created {formatDate(p.createdAt)}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
