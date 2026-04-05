import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: {
    default: "ShieldPay — Freelancer Payment Protection",
    template: "%s | ShieldPay",
  },
  description:
    "Escrow-backed payment protection for freelancers. Get paid for every project with milestone-based escrow, client reputation scoring, and instant payouts. Only 3.5% fee.",
  keywords: [
    "freelance payment protection",
    "escrow for freelancers",
    "get paid freelancing",
    "freelancer invoice protection",
    "milestone payments",
    "freelancer escrow",
    "payment protection platform",
  ],
  openGraph: {
    title: "ShieldPay — Get Paid for Every Project. Guaranteed.",
    description:
      "Escrow-backed payment protection for freelancers. No platform lock-in. No 20% fees. Just guaranteed payment.",
    url: "https://shieldpay.io",
    siteName: "ShieldPay",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "ShieldPay — Freelancer Payment Protection",
    description: "Get paid for every project. Guaranteed.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "Organization",
              name: "ShieldPay",
              url: "https://shieldpay.io",
              description:
                "Escrow-backed payment protection platform for freelancers",
              foundingDate: "2024",
              sameAs: [],
            }),
          }}
        />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-[family-name:var(--font-geist-sans)] antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
