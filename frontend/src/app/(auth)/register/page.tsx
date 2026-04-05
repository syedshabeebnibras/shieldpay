"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Shield, User, Briefcase } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import type { OnboardingLinkResponse, UserRole } from "@/types";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState<UserRole>("freelancer");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<
    Record<string, string>
  >({});

  function validate(): boolean {
    const errors: Record<string, string> = {};
    if (!fullName.trim()) errors.fullName = "Full name is required";
    if (!email.trim()) errors.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
      errors.email = "Invalid email address";
    if (!password) errors.password = "Password is required";
    else if (password.length < 8)
      errors.password = "Password must be at least 8 characters";
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const data = await register({ email, password, fullName, role });

      if (role === "freelancer" && data?.user.stripeAccountId) {
        try {
          const { data: link } = await api.post<OnboardingLinkResponse>(
            "/api/auth/stripe/onboarding-link",
          );
          window.location.href = link.url;
          return;
        } catch {
          // Stripe onboarding can be done later from settings
        }
      }

      router.push("/dashboard");
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
      else setError("Registration failed");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md"
      >
        <div className="mb-8 text-center">
          <Link href="/" className="inline-flex items-center gap-2 text-xl font-bold">
            <Shield className="h-6 w-6 text-blue-600" />
            ShieldPay
          </Link>
          <h1 className="mt-4 text-2xl font-bold text-gray-900">
            Create your account
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Start protecting your payments today
          </p>
        </div>

        <div className="rounded-xl border bg-white p-8 shadow-sm">
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700"
            >
              {error}
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Role selector */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">
                I am a
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setRole("freelancer")}
                  className={`flex items-center gap-2 rounded-lg border-2 p-3 text-sm font-medium transition-colors ${
                    role === "freelancer"
                      ? "border-blue-600 bg-blue-50 text-blue-700"
                      : "border-gray-200 text-gray-600 hover:border-gray-300"
                  }`}
                >
                  <Briefcase className="h-4 w-4" />
                  Freelancer
                </button>
                <button
                  type="button"
                  onClick={() => setRole("client")}
                  className={`flex items-center gap-2 rounded-lg border-2 p-3 text-sm font-medium transition-colors ${
                    role === "client"
                      ? "border-blue-600 bg-blue-50 text-blue-700"
                      : "border-gray-200 text-gray-600 hover:border-gray-300"
                  }`}
                >
                  <User className="h-4 w-4" />
                  Client
                </button>
              </div>
            </div>

            {/* Full name */}
            <div>
              <label
                htmlFor="fullName"
                className="mb-1.5 block text-sm font-medium text-gray-700"
              >
                Full name
              </label>
              <input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className={`w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors focus:border-blue-500 focus:ring-1 focus:ring-blue-500 ${
                  validationErrors.fullName
                    ? "border-red-300"
                    : "border-gray-300"
                }`}
                placeholder="John Doe"
              />
              {validationErrors.fullName && (
                <p className="mt-1 text-xs text-red-600">
                  {validationErrors.fullName}
                </p>
              )}
            </div>

            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="mb-1.5 block text-sm font-medium text-gray-700"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={`w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors focus:border-blue-500 focus:ring-1 focus:ring-blue-500 ${
                  validationErrors.email
                    ? "border-red-300"
                    : "border-gray-300"
                }`}
                placeholder="you@example.com"
              />
              {validationErrors.email && (
                <p className="mt-1 text-xs text-red-600">
                  {validationErrors.email}
                </p>
              )}
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="mb-1.5 block text-sm font-medium text-gray-700"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={`w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors focus:border-blue-500 focus:ring-1 focus:ring-blue-500 ${
                  validationErrors.password
                    ? "border-red-300"
                    : "border-gray-300"
                }`}
                placeholder="Min. 8 characters"
              />
              {validationErrors.password && (
                <p className="mt-1 text-xs text-red-600">
                  {validationErrors.password}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSubmitting ? "Creating account..." : "Create account"}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-gray-500">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-blue-600 hover:text-blue-700">
              Log in
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
