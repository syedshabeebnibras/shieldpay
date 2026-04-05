export type UserRole = "freelancer" | "client" | "admin";

export interface User {
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  isVerified: boolean;
  stripeAccountId: string | null;
  stripeCustomerId: string | null;
  createdAt: string;
}

export interface AuthResponse {
  user: User;
  accessToken: string;
  tokenType: string;
}

export interface OnboardingLinkResponse {
  url: string;
}

export interface OnboardingStatusResponse {
  chargesEnabled: boolean;
  payoutsEnabled: boolean;
  detailsSubmitted: boolean;
  isVerified: boolean;
}

export type ProjectStatus =
  | "draft"
  | "active"
  | "completed"
  | "cancelled"
  | "disputed";

export interface Project {
  id: string;
  title: string;
  description: string | null;
  freelancerId: string;
  clientEmail: string;
  clientId: string | null;
  status: ProjectStatus;
  totalAmountCents: number;
  totalAmountDollars: number;
  currency: string;
  paymentToken: string;
  paymentLink: string;
  createdAt: string;
  updatedAt: string | null;
}

export interface ProjectDetail extends Project {
  milestones: Milestone[];
}

export interface CheckoutData {
  projectTitle: string;
  projectDescription: string | null;
  freelancerName: string;
  clientEmail: string;
  currency: string;
  totalAmountCents: number;
  totalAmountDollars: number;
  milestones: Milestone[];
}

export interface PaymentIntentData {
  clientSecret: string;
  paymentIntentId: string;
}

export interface CreateProjectData {
  title: string;
  description?: string;
  clientEmail: string;
  milestones: { title: string; description?: string; amountCents: number; dueDate?: string }[];
}

export type MilestoneStatus =
  | "draft"
  | "funded"
  | "in_progress"
  | "delivered"
  | "approved"
  | "disputed"
  | "released"
  | "refunded";

export interface Milestone {
  id: string;
  projectId: string;
  title: string;
  description: string | null;
  amountCents: number;
  amountDollars: number;
  position: number;
  status: MilestoneStatus;
  dueDate: string | null;
  fundedAt: string | null;
  deliveredAt: string | null;
  approvedAt: string | null;
  releasedAt: string | null;
  stripePaymentIntentId: string | null;
  createdAt: string;
  updatedAt: string | null;
}

export type PaymentStatus =
  | "pending"
  | "succeeded"
  | "failed"
  | "refunded"
  | "partially_refunded";

export interface Payment {
  id: string;
  milestoneId: string;
  stripePaymentIntentId: string;
  stripeChargeId: string | null;
  amountCents: number;
  amountDollars: number;
  currency: string;
  status: PaymentStatus;
  clientEmail: string;
  metadataJson: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string | null;
}

export type DisputeStatus =
  | "open"
  | "under_review"
  | "resolved_freelancer"
  | "resolved_client"
  | "resolved_split";

export interface Dispute {
  id: string;
  milestoneId: string;
  raisedById: string;
  reason: string;
  status: DisputeStatus;
  resolutionNotes: string | null;
  resolvedAt: string | null;
  createdAt: string;
  updatedAt: string | null;
}

export interface Rating {
  id: string;
  projectId: string;
  ratedById: string;
  ratedUserEmail: string;
  score: number;
  comment: string | null;
  createdAt: string;
}

export type TrustTier = "new" | "verified" | "trusted" | "premium";

export interface ClientScore {
  email: string;
  averageRating: number | null;
  totalRatings: number;
  totalProjects: number;
  totalAmountPaidCents: number;
  avgApprovalDays: number | null;
  onTimePercentage: number | null;
  disputeRate: number | null;
  trustTier: TrustTier;
}
