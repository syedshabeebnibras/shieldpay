"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { TrustBadge, StarRating } from "@/components/ui/Badge";
import type { ClientScore } from "@/types";

export function ClientScoreCard({ email }: { email: string }) {
  const [score, setScore] = useState<ClientScore | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!email || !email.includes("@")) return;
    setLoading(true);
    api
      .get<ClientScore>(`/api/ratings/client-score/${encodeURIComponent(email)}`)
      .then(({ data }) => setScore(data))
      .catch(() => setScore(null))
      .finally(() => setLoading(false));
  }, [email]);

  if (loading) {
    return (
      <div className="text-xs text-gray-400">Checking client reputation...</div>
    );
  }

  if (!score || score.totalProjects === 0) return null;

  return (
    <div className="mt-2 flex items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2">
      <TrustBadge tier={score.trustTier} />
      {score.averageRating !== null && (
        <div className="flex items-center gap-1">
          <StarRating rating={score.averageRating} />
          <span className="text-xs text-gray-500">
            ({score.averageRating.toFixed(1)})
          </span>
        </div>
      )}
      <span className="text-xs text-gray-500">
        {score.totalProjects} project{score.totalProjects !== 1 ? "s" : ""}
      </span>
      {score.onTimePercentage !== null && (
        <span className="text-xs text-gray-500">
          {score.onTimePercentage.toFixed(0)}% on-time
        </span>
      )}
    </div>
  );
}
