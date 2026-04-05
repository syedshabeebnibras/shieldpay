"use client";

import { FormEvent, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Star, X } from "lucide-react";
import { api } from "@/lib/api";

interface RatingModalProps {
  projectId: string;
  clientEmail: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function RatingModal({
  projectId,
  clientEmail,
  isOpen,
  onClose,
  onSuccess,
}: RatingModalProps) {
  const [score, setScore] = useState(0);
  const [hoveredStar, setHoveredStar] = useState(0);
  const [comment, setComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (score === 0) {
      setError("Please select a rating");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await api.post(`/api/ratings/projects/${projectId}/rate`, {
        score,
        comment: comment.trim() || null,
      });
      onSuccess();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      setError(msg || "Failed to submit rating");
    } finally {
      setIsSubmitting(false);
    }
  }

  const labels = ["", "Poor", "Fair", "Good", "Very Good", "Excellent"];

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl"
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                Rate Client
              </h2>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="mt-1 text-sm text-gray-500">
              How was your experience with {clientEmail}?
            </p>

            {error && (
              <div className="mt-3 rounded-lg bg-red-50 p-2 text-sm text-red-700">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="mt-4 space-y-4">
              {/* Star rating */}
              <div className="flex flex-col items-center gap-2">
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setScore(i)}
                      onMouseEnter={() => setHoveredStar(i)}
                      onMouseLeave={() => setHoveredStar(0)}
                      className="p-1 transition-transform hover:scale-110"
                    >
                      <Star
                        className={`h-8 w-8 ${
                          i <= (hoveredStar || score)
                            ? "fill-yellow-400 text-yellow-400"
                            : "text-gray-300"
                        }`}
                      />
                    </button>
                  ))}
                </div>
                {(hoveredStar || score) > 0 && (
                  <span className="text-sm font-medium text-gray-600">
                    {labels[hoveredStar || score]}
                  </span>
                )}
              </div>

              {/* Comment */}
              <div>
                <label
                  htmlFor="comment"
                  className="mb-1 block text-sm font-medium text-gray-700"
                >
                  Comment (optional)
                </label>
                <textarea
                  id="comment"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  rows={3}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  placeholder="Share your experience..."
                />
              </div>

              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={isSubmitting || score === 0}
                  className="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {isSubmitting ? "Submitting..." : "Submit Rating"}
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
