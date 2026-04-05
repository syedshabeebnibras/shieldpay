"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  Elements,
  PaymentElement,
  useStripe,
  useElements,
} from "@stripe/react-stripe-js";
import { Shield, Check, Loader2 } from "lucide-react";
import { stripePromise } from "@/lib/stripe";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { MilestoneStatusBadge } from "@/components/ui/Badge";
import type { CheckoutData, Milestone, PaymentIntentData } from "@/types";

export default function PaymentPage() {
  const params = useParams<{ token: string }>();
  const [checkout, setCheckout] = useState<CheckoutData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [payingMilestone, setPayingMilestone] = useState<Milestone | null>(null);
  const [clientSecret, setClientSecret] = useState<string | null>(null);

  const fetchCheckout = useCallback(async () => {
    try {
      const { data } = await api.get<CheckoutData>(
        `/api/payments/checkout/${params.token}`,
      );
      setCheckout(data);
    } catch {
      setError("Project not found or link has expired.");
    } finally {
      setIsLoading(false);
    }
  }, [params.token]);

  useEffect(() => {
    fetchCheckout();
  }, [fetchCheckout]);

  async function startPayment(milestone: Milestone) {
    try {
      const { data } = await api.post<PaymentIntentData>(
        `/api/payments/create-intent/${milestone.id}`,
      );
      setClientSecret(data.clientSecret);
      setPayingMilestone(milestone);
    } catch {
      setError("Failed to start payment. Please try again.");
    }
  }

  function handlePaymentComplete() {
    setClientSecret(null);
    setPayingMilestone(null);
    fetchCheckout();
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !checkout) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
        <div className="max-w-md text-center">
          <Shield className="mx-auto h-12 w-12 text-gray-300" />
          <h1 className="mt-4 text-xl font-bold text-gray-900">
            {error || "Something went wrong"}
          </h1>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-3xl items-center gap-2 px-6 py-4">
          <Shield className="h-5 w-5 text-blue-600" />
          <span className="text-sm font-bold">ShieldPay</span>
          <span className="ml-auto text-xs text-gray-400">Secure Payment</span>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-2xl font-bold text-gray-900">
            {checkout.projectTitle}
          </h1>
          {checkout.projectDescription && (
            <p className="mt-1 text-gray-500">{checkout.projectDescription}</p>
          )}
          <p className="mt-1 text-sm text-gray-400">
            From {checkout.freelancerName} &middot; Total{" "}
            {formatCurrency(checkout.totalAmountCents)}
          </p>

          {/* Stripe Payment Form */}
          {clientSecret && payingMilestone && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="mt-6"
            >
              <div className="rounded-xl border bg-white p-6 shadow-sm">
                <h2 className="mb-4 font-semibold text-gray-900">
                  Pay for: {payingMilestone.title} —{" "}
                  {formatCurrency(payingMilestone.amountCents)}
                </h2>
                <Elements
                  stripe={stripePromise}
                  options={{ clientSecret, appearance: { theme: "stripe" } }}
                >
                  <CheckoutForm
                    onSuccess={handlePaymentComplete}
                    onCancel={() => {
                      setClientSecret(null);
                      setPayingMilestone(null);
                    }}
                  />
                </Elements>
              </div>
            </motion.div>
          )}

          {/* Milestone list */}
          <div className="mt-6 space-y-3">
            {checkout.milestones.map((m) => (
              <div
                key={m.id}
                className="flex items-center justify-between rounded-xl border bg-white p-4 shadow-sm"
              >
                <div>
                  <h3 className="font-medium text-gray-900">{m.title}</h3>
                  {m.description && (
                    <p className="mt-0.5 text-sm text-gray-500">
                      {m.description}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold">
                    {formatCurrency(m.amountCents)}
                  </span>
                  {m.status === "draft" ? (
                    <button
                      onClick={() => startPayment(m)}
                      disabled={!!clientSecret}
                      className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                    >
                      Fund
                    </button>
                  ) : (
                    <MilestoneStatusBadge status={m.status} />
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Rating notice */}
          <p className="mt-6 text-center text-xs text-gray-400">
            After this project is completed, the freelancer may rate your
            payment experience. Timely approvals help build your trust score.
          </p>
        </motion.div>
      </main>
    </div>
  );
}

function CheckoutForm({
  onSuccess,
  onCancel,
}: {
  onSuccess: () => void;
  onCancel: () => void;
}) {
  const stripe = useStripe();
  const elements = useElements();
  const [isProcessing, setIsProcessing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [succeeded, setSucceeded] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!stripe || !elements) return;

    setIsProcessing(true);
    setMessage(null);

    const { error, paymentIntent } = await stripe.confirmPayment({
      elements,
      confirmParams: { return_url: window.location.href },
      redirect: "if_required",
    });

    if (error) {
      setMessage(error.message || "Payment failed");
      setIsProcessing(false);
    } else if (paymentIntent?.status === "succeeded") {
      setSucceeded(true);
      setTimeout(onSuccess, 2000);
    } else {
      setMessage("Payment is processing...");
      setIsProcessing(false);
    }
  }

  if (succeeded) {
    return (
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="py-6 text-center"
      >
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100">
          <Check className="h-6 w-6 text-emerald-600" />
        </div>
        <p className="font-semibold text-emerald-700">Payment Successful!</p>
        <p className="mt-1 text-sm text-gray-500">
          Funds are now held securely in escrow.
        </p>
      </motion.div>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <PaymentElement />
      {message && (
        <p className="mt-3 text-sm text-red-600">{message}</p>
      )}
      <div className="mt-4 flex gap-3">
        <button
          type="submit"
          disabled={!stripe || isProcessing}
          className="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {isProcessing ? "Processing..." : "Pay Now"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
