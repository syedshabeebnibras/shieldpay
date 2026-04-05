"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Check,
  Clock,
  Copy,
  DollarSign,
  RefreshCw,
  Send,
  Star,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { MilestoneStatusBadge, ProjectStatusBadge } from "@/components/ui/Badge";
import { RatingModal } from "@/components/ratings/RatingModal";
import type { Milestone, ProjectDetail } from "@/types";

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const { user } = useAuth();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [ratingOpen, setRatingOpen] = useState(false);
  const [hasRated, setHasRated] = useState(false);
  const [disputeModal, setDisputeModal] = useState<string | null>(null);
  const [disputeReason, setDisputeReason] = useState("");
  const [disputeSubmitting, setDisputeSubmitting] = useState(false);

  const fetchProject = useCallback(async () => {
    try {
      const { data } = await api.get<ProjectDetail>(
        `/api/projects/${params.id}`,
      );
      setProject(data);
    } catch {
      /* handled by interceptor */
    } finally {
      setIsLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    fetchProject();
    const interval = setInterval(fetchProject, 30000);
    return () => clearInterval(interval);
  }, [fetchProject]);

  const isFreelancer = user && project && user.id === project.freelancerId;
  const isClient =
    user &&
    project &&
    (user.id === project.clientId || user.email === project.clientEmail);

  async function milestoneAction(milestoneId: string, action: string) {
    setActionLoading(milestoneId);
    try {
      await api.post(`/api/milestones/${milestoneId}/${action}`);
      await fetchProject();
    } catch {
      /* error handled */
    } finally {
      setActionLoading(null);
    }
  }

  async function openDispute(milestoneId: string) {
    if (disputeReason.length < 50) return;
    setDisputeSubmitting(true);
    try {
      await api.post(`/api/disputes/milestones/${milestoneId}/dispute`, {
        reason: disputeReason,
      });
      setDisputeModal(null);
      setDisputeReason("");
      await fetchProject();
    } catch {
      /* error handled */
    } finally {
      setDisputeSubmitting(false);
    }
  }

  async function copyLink() {
    if (!project) return;
    await navigator.clipboard.writeText(project.paymentLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (isLoading) return <div className="text-gray-500">Loading project...</div>;
  if (!project) return <div className="text-red-500">Project not found</div>;

  return (
    <div className="mx-auto max-w-3xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{project.title}</h1>
          {project.description && (
            <p className="mt-1 text-gray-500">{project.description}</p>
          )}
          <p className="mt-1 text-sm text-gray-400">
            Client: {project.clientEmail}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ProjectStatusBadge status={project.status} />
          {isFreelancer && project.status === "completed" && !hasRated && (
            <button
              onClick={() => setRatingOpen(true)}
              className="flex items-center gap-1 rounded-lg bg-yellow-50 px-3 py-1.5 text-xs font-medium text-yellow-700 hover:bg-yellow-100"
            >
              <Star className="h-3.5 w-3.5" />
              Rate Client
            </button>
          )}
        </div>
      </div>

      {/* Payment link */}
      {isFreelancer && (
        <div className="mt-4 flex items-center gap-2 rounded-lg border bg-gray-50 px-4 py-2.5">
          <span className="text-xs font-medium text-gray-500">Payment Link:</span>
          <code className="flex-1 truncate text-xs text-gray-600">
            {project.paymentLink}
          </code>
          <button onClick={copyLink} className="text-gray-400 hover:text-gray-600">
            {copied ? (
              <Check className="h-4 w-4 text-emerald-500" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </button>
        </div>
      )}

      {/* Summary cards */}
      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="text-xs font-medium text-gray-500">Total Value</div>
          <div className="mt-1 text-lg font-bold text-gray-900">
            {formatCurrency(project.totalAmountCents)}
          </div>
        </div>
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="text-xs font-medium text-gray-500">Milestones</div>
          <div className="mt-1 text-lg font-bold text-gray-900">
            {project.milestones.length}
          </div>
        </div>
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="text-xs font-medium text-gray-500">Released</div>
          <div className="mt-1 text-lg font-bold text-emerald-600">
            {formatCurrency(
              project.milestones
                .filter((m) => m.status === "released")
                .reduce((s, m) => s + m.amountCents, 0),
            )}
          </div>
        </div>
      </div>

      {/* Milestone Timeline */}
      <div className="mt-8">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Milestones</h2>
        <div className="space-y-0">
          {project.milestones.map((m, i) => (
            <MilestoneCard
              key={m.id}
              milestone={m}
              isLast={i === project.milestones.length - 1}
              isFreelancer={!!isFreelancer}
              isClient={!!isClient}
              actionLoading={actionLoading}
              onAction={milestoneAction}
              onDispute={(id) => setDisputeModal(id)}
            />
          ))}
        </div>
      </div>

      {/* Dispute modal */}
      {disputeModal && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          onClick={() => setDisputeModal(null)}
        >
          <motion.div
            initial={{ scale: 0.95 }}
            animate={{ scale: 1 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl"
          >
            <h2 className="text-lg font-semibold text-gray-900">
              Raise a Dispute
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Funds will be frozen until the dispute is resolved. Min 50 characters.
            </p>
            <textarea
              value={disputeReason}
              onChange={(e) => setDisputeReason(e.target.value)}
              rows={4}
              className="mt-3 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500"
              placeholder="Describe the issue in detail..."
            />
            <div className="mt-1 text-right text-xs text-gray-400">
              {disputeReason.length}/50 min
            </div>
            <div className="mt-3 flex gap-3">
              <button
                onClick={() => openDispute(disputeModal)}
                disabled={disputeReason.length < 50 || disputeSubmitting}
                className="flex-1 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              >
                {disputeSubmitting ? "Submitting..." : "Open Dispute"}
              </button>
              <button
                onClick={() => {
                  setDisputeModal(null);
                  setDisputeReason("");
                }}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}

      {/* Rating modal */}
      <RatingModal
        projectId={project.id}
        clientEmail={project.clientEmail}
        isOpen={ratingOpen}
        onClose={() => setRatingOpen(false)}
        onSuccess={() => {
          setRatingOpen(false);
          setHasRated(true);
        }}
      />
    </div>
  );
}

function MilestoneCard({
  milestone: m,
  isLast,
  isFreelancer,
  isClient,
  actionLoading,
  onAction,
  onDispute,
}: {
  milestone: Milestone;
  isLast: boolean;
  isFreelancer: boolean;
  isClient: boolean;
  actionLoading: string | null;
  onAction: (id: string, action: string) => void;
  onDispute: (id: string) => void;
}) {
  const isActing = actionLoading === m.id;
  const canDispute =
    (isFreelancer || isClient) &&
    ["funded", "in_progress", "delivered"].includes(m.status);

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex gap-4"
    >
      {/* Timeline connector */}
      <div className="flex flex-col items-center">
        <div
          className={`flex h-8 w-8 items-center justify-center rounded-full border-2 ${
            m.status === "released"
              ? "border-emerald-500 bg-emerald-50"
              : m.status === "approved"
                ? "border-green-500 bg-green-50"
                : m.status === "delivered"
                  ? "border-amber-500 bg-amber-50"
                  : m.status === "funded" || m.status === "in_progress"
                    ? "border-blue-500 bg-blue-50"
                    : m.status === "disputed"
                      ? "border-red-500 bg-red-50"
                      : "border-gray-300 bg-white"
          }`}
        >
          {m.status === "released" || m.status === "approved" ? (
            <Check className="h-4 w-4 text-emerald-600" />
          ) : m.status === "delivered" ? (
            <Send className="h-4 w-4 text-amber-600" />
          ) : m.status === "funded" || m.status === "in_progress" ? (
            <DollarSign className="h-4 w-4 text-blue-600" />
          ) : m.status === "disputed" ? (
            <AlertTriangle className="h-4 w-4 text-red-600" />
          ) : (
            <Clock className="h-4 w-4 text-gray-400" />
          )}
        </div>
        {!isLast && <div className="w-px flex-1 bg-gray-200" />}
      </div>

      {/* Content */}
      <div className="flex-1 pb-6">
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-medium text-gray-900">{m.title}</h3>
              {m.description && (
                <p className="mt-0.5 text-sm text-gray-500">{m.description}</p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-gray-900">
                {formatCurrency(m.amountCents)}
              </span>
              <MilestoneStatusBadge status={m.status} />
            </div>
          </div>

          {/* Timestamps */}
          <div className="mt-2 flex flex-wrap gap-3 text-xs text-gray-400">
            {m.fundedAt && <span>Funded {formatDate(m.fundedAt)}</span>}
            {m.deliveredAt && <span>Delivered {formatDate(m.deliveredAt)}</span>}
            {m.approvedAt && <span>Approved {formatDate(m.approvedAt)}</span>}
            {m.releasedAt && <span>Released {formatDate(m.releasedAt)}</span>}
            {m.dueDate && <span>Due {m.dueDate}</span>}
          </div>

          {/* Actions */}
          <div className="mt-3 flex flex-wrap gap-2">
            {isFreelancer &&
              (m.status === "funded" || m.status === "in_progress") && (
                <button
                  onClick={() => onAction(m.id, "deliver")}
                  disabled={isActing}
                  className="flex items-center gap-1.5 rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-amber-600 disabled:opacity-50"
                >
                  <Send className="h-3.5 w-3.5" />
                  {isActing ? "..." : "Mark as Delivered"}
                </button>
              )}
            {isClient && m.status === "delivered" && (
              <>
                <button
                  onClick={() => onAction(m.id, "approve")}
                  disabled={isActing}
                  className="flex items-center gap-1.5 rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-600 disabled:opacity-50"
                >
                  <Check className="h-3.5 w-3.5" />
                  {isActing ? "..." : "Approve & Release"}
                </button>
                <button
                  onClick={() => onAction(m.id, "request-revision")}
                  disabled={isActing}
                  className="flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  Revision
                </button>
              </>
            )}
            {canDispute && (
              <button
                onClick={() => onDispute(m.id)}
                className="flex items-center gap-1.5 rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50"
              >
                <AlertTriangle className="h-3.5 w-3.5" />
                Dispute
              </button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
