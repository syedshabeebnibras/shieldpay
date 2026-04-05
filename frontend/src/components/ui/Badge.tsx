import { Check, Star } from "lucide-react";
import type { MilestoneStatus, ProjectStatus, TrustTier } from "@/types";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "danger" | "info" | "emerald" | "gold";
}

const variantStyles = {
  default: "bg-gray-100 text-gray-800",
  info: "bg-blue-100 text-blue-800",
  success: "bg-green-100 text-green-800",
  emerald: "bg-emerald-100 text-emerald-800",
  warning: "bg-amber-100 text-amber-800",
  danger: "bg-red-100 text-red-800",
  gold: "bg-yellow-100 text-yellow-800",
};

export function Badge({ children, variant = "default" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${variantStyles[variant]}`}
    >
      {children}
    </span>
  );
}

const milestoneVariantMap: Record<MilestoneStatus, BadgeProps["variant"]> = {
  draft: "default",
  funded: "info",
  in_progress: "warning",
  delivered: "warning",
  approved: "success",
  disputed: "danger",
  released: "emerald",
  refunded: "default",
};

export function MilestoneStatusBadge({ status }: { status: MilestoneStatus }) {
  const label = status.replace("_", " ");
  return (
    <Badge variant={milestoneVariantMap[status]}>
      {label.charAt(0).toUpperCase() + label.slice(1)}
    </Badge>
  );
}

const projectVariantMap: Record<ProjectStatus, BadgeProps["variant"]> = {
  draft: "default",
  active: "info",
  completed: "emerald",
  cancelled: "default",
  disputed: "danger",
};

export function ProjectStatusBadge({ status }: { status: ProjectStatus }) {
  return (
    <Badge variant={projectVariantMap[status]}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
}

const trustTierConfig: Record<
  TrustTier,
  { label: string; variant: BadgeProps["variant"]; icon: "none" | "check" | "star" }
> = {
  new: { label: "New Client", variant: "default", icon: "none" },
  verified: { label: "Verified", variant: "info", icon: "check" },
  trusted: { label: "Trusted", variant: "emerald", icon: "check" },
  premium: { label: "Premium", variant: "gold", icon: "star" },
};

export function TrustBadge({ tier }: { tier: TrustTier }) {
  const config = trustTierConfig[tier];
  return (
    <Badge variant={config.variant}>
      {config.icon === "check" && <Check className="mr-1 h-3 w-3" />}
      {config.icon === "star" && <Star className="mr-1 h-3 w-3" />}
      {config.label}
    </Badge>
  );
}

export function StarRating({
  rating,
  size = "sm",
}: {
  rating: number;
  size?: "sm" | "md";
}) {
  const sizeClass = size === "sm" ? "h-3.5 w-3.5" : "h-5 w-5";
  return (
    <span className="inline-flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          className={`${sizeClass} ${
            i <= Math.round(rating)
              ? "fill-yellow-400 text-yellow-400"
              : "text-gray-300"
          }`}
        />
      ))}
    </span>
  );
}
