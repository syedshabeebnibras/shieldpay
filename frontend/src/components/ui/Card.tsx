"use client";

import { motion } from "framer-motion";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  header?: React.ReactNode;
  footer?: React.ReactNode;
}

export function Card({
  children,
  className = "",
  hover = false,
  header,
  footer,
}: CardProps) {
  const content = (
    <>
      {header && (
        <div className="border-b border-gray-100 px-6 py-4">{header}</div>
      )}
      <div className="p-6">{children}</div>
      {footer && (
        <div className="border-t border-gray-100 px-6 py-4">{footer}</div>
      )}
    </>
  );

  if (hover) {
    return (
      <motion.div
        whileHover={{
          y: -4,
          boxShadow: "0 12px 24px -4px rgba(0,0,0,0.08)",
        }}
        className={`rounded-xl border border-gray-200 bg-white shadow-sm transition-shadow ${className}`}
      >
        {content}
      </motion.div>
    );
  }

  return (
    <div
      className={`rounded-xl border border-gray-200 bg-white shadow-sm ${className}`}
    >
      {content}
    </div>
  );
}
