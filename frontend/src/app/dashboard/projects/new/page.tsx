"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Plus, Trash2, Copy, Check } from "lucide-react";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { ClientScoreCard } from "@/components/ratings/ClientScoreCard";
import type { Project } from "@/types";

interface MilestoneInput {
  title: string;
  description: string;
  amountCents: number;
}

const PLATFORM_FEE_RATE = 0.035;

export default function NewProjectPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [clientEmail, setClientEmail] = useState("");
  const [milestones, setMilestones] = useState<MilestoneInput[]>([
    { title: "", description: "", amountCents: 0 },
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdProject, setCreatedProject] = useState<Project | null>(null);
  const [copied, setCopied] = useState(false);

  const totalCents = milestones.reduce((s, m) => s + m.amountCents, 0);
  const platformFee = Math.round(totalCents * PLATFORM_FEE_RATE);
  const freelancerReceives = totalCents - platformFee;

  function addMilestone() {
    setMilestones([...milestones, { title: "", description: "", amountCents: 0 }]);
  }

  function removeMilestone(index: number) {
    if (milestones.length <= 1) return;
    setMilestones(milestones.filter((_, i) => i !== index));
  }

  function updateMilestone(index: number, field: keyof MilestoneInput, value: string | number) {
    const updated = [...milestones];
    if (field === "amountCents") {
      updated[index][field] = Math.round(Number(value) * 100);
    } else {
      updated[index][field] = value as string;
    }
    setMilestones(updated);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (!title.trim()) { setError("Project title is required"); return; }
    if (!clientEmail.trim()) { setError("Client email is required"); return; }
    if (milestones.some((m) => !m.title.trim())) { setError("All milestones need a title"); return; }
    if (milestones.some((m) => m.amountCents <= 0)) { setError("All milestones need a positive amount"); return; }

    setIsSubmitting(true);
    try {
      const { data } = await api.post<Project>("/api/projects/", {
        title,
        description: description || null,
        client_email: clientEmail,
        milestones: milestones.map((m) => ({
          title: m.title,
          description: m.description || null,
          amount_cents: m.amountCents,
        })),
      });
      setCreatedProject(data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to create project");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function copyLink() {
    if (!createdProject) return;
    await navigator.clipboard.writeText(createdProject.paymentLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (createdProject) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mx-auto max-w-lg"
      >
        <div className="rounded-xl border bg-white p-8 text-center shadow-sm">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100">
            <Check className="h-6 w-6 text-emerald-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Project Created!</h1>
          <p className="mt-2 text-gray-500">
            Share this payment link with your client:
          </p>
          <div className="mt-4 flex items-center gap-2 rounded-lg border bg-gray-50 p-3">
            <code className="flex-1 truncate text-sm text-gray-700">
              {createdProject.paymentLink}
            </code>
            <button
              onClick={copyLink}
              className="rounded-md p-1.5 text-gray-500 hover:bg-gray-200"
            >
              {copied ? (
                <Check className="h-4 w-4 text-emerald-600" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </button>
          </div>
          <p className="mt-2 text-xs text-gray-400">
            An email has also been sent to {createdProject.clientEmail}
          </p>
          <div className="mt-6 flex gap-3 justify-center">
            <button
              onClick={() => router.push(`/dashboard/projects/${createdProject.id}`)}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              View Project
            </button>
            <button
              onClick={() => router.push("/dashboard/projects")}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              All Projects
            </button>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900">Create Project</h1>
      <p className="mt-1 text-sm text-gray-500">
        Define your project and milestones, then send the payment link to your client.
      </p>

      {error && (
        <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-6 space-y-6">
        {/* Project info */}
        <div className="rounded-xl border bg-white p-6 shadow-sm space-y-4">
          <h2 className="font-semibold text-gray-900">Project Details</h2>
          <div>
            <label htmlFor="title" className="mb-1 block text-sm font-medium text-gray-700">
              Title
            </label>
            <input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              placeholder="Website Redesign"
            />
          </div>
          <div>
            <label htmlFor="desc" className="mb-1 block text-sm font-medium text-gray-700">
              Description (optional)
            </label>
            <textarea
              id="desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              placeholder="Describe the project scope..."
            />
          </div>
          <div>
            <label htmlFor="email" className="mb-1 block text-sm font-medium text-gray-700">
              Client Email
            </label>
            <input
              id="email"
              type="email"
              value={clientEmail}
              onChange={(e) => setClientEmail(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              placeholder="client@company.com"
            />
            {clientEmail.includes("@") && (
              <ClientScoreCard email={clientEmail} />
            )}
          </div>
        </div>

        {/* Milestones */}
        <div className="rounded-xl border bg-white p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">Milestones</h2>
            <button
              type="button"
              onClick={addMilestone}
              className="flex items-center gap-1 rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
            >
              <Plus className="h-3.5 w-3.5" /> Add Milestone
            </button>
          </div>

          {milestones.map((m, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="rounded-lg border border-gray-200 bg-gray-50 p-4 space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-500">
                  Milestone {i + 1}
                </span>
                {milestones.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeMilestone(i)}
                    className="text-gray-400 hover:text-red-500"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <input
                  value={m.title}
                  onChange={(e) => updateMilestone(i, "title", e.target.value)}
                  placeholder="Milestone title"
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
                <div className="relative">
                  <span className="absolute left-3 top-2 text-sm text-gray-400">$</span>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={m.amountCents ? (m.amountCents / 100).toFixed(2) : ""}
                    onChange={(e) => updateMilestone(i, "amountCents", e.target.value)}
                    placeholder="0.00"
                    className="w-full rounded-lg border border-gray-300 pl-7 pr-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Summary */}
        <div className="rounded-xl border bg-white p-6 shadow-sm">
          <h2 className="mb-3 font-semibold text-gray-900">Summary</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Total Amount</span>
              <span className="font-medium">{formatCurrency(totalCents)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Platform Fee (3.5%)</span>
              <span className="text-gray-500">-{formatCurrency(platformFee)}</span>
            </div>
            <div className="border-t pt-2 flex justify-between">
              <span className="font-medium text-gray-900">You Receive</span>
              <span className="font-bold text-emerald-600">
                {formatCurrency(freelancerReceives)}
              </span>
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {isSubmitting ? "Creating..." : "Create Project & Send Link"}
        </button>
      </form>
    </div>
  );
}
