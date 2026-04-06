"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Briefcase,
  CreditCard,
  LayoutDashboard,
  Loader2,
  LogOut,
  MessageSquare,
  Settings,
  Shield,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/projects", label: "Projects", icon: Briefcase },
  { href: "/dashboard/payments", label: "Payments", icon: CreditCard },
  { href: "/dashboard/disputes", label: "Disputes", icon: MessageSquare },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isLoading, isAuthenticated, logout } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <motion.aside
        initial={{ x: -20, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="fixed inset-y-0 left-0 z-30 w-64 border-r border-gray-200 bg-white"
      >
        <div className="flex h-full flex-col">
          <div className="flex items-center gap-2 border-b border-gray-100 px-6 py-5">
            <Shield className="h-6 w-6 text-blue-600" />
            <span className="text-lg font-bold text-gray-900">ShieldPay</span>
          </div>

          <nav className="flex-1 px-3 py-4">
            <ul className="space-y-1">
              {navItems.map((item) => {
                const isActive =
                  item.href === "/dashboard"
                    ? pathname === "/dashboard"
                    : pathname.startsWith(item.href);
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={`relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                        isActive
                          ? "bg-blue-50 text-blue-700"
                          : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                      }`}
                    >
                      <item.icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          <div className="border-t border-gray-100 px-3 py-4">
            {user && (
              <div className="mb-3 px-3">
                <p className="truncate text-sm font-medium text-gray-900">
                  {user.fullName}
                </p>
                <p className="truncate text-xs text-gray-500">{user.email}</p>
              </div>
            )}
            <button
              onClick={logout}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-50 hover:text-gray-900"
            >
              <LogOut className="h-4 w-4" />
              Log out
            </button>
          </div>
        </div>
      </motion.aside>

      <main className="ml-64 flex-1">
        <div className="mx-auto max-w-5xl px-8 py-8">
          <motion.div
            key={pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {children}
          </motion.div>
        </div>
      </main>
    </div>
  );
}
