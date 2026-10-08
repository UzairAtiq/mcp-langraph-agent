import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold tracking-wide transition-colors",
  {
    variants: {
      variant: {
        default:
          "bg-neutral-900 text-white",
        secondary:
          "bg-neutral-100 text-neutral-800",
        approved:
          "bg-accent/25 text-neutral-900 border border-accent/60",
        pending:
          "bg-neutral-200 text-neutral-700",
        discarded:
          "bg-danger/15 text-danger border border-danger/30",
        outline:
          "text-neutral-900 border border-neutral-300",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
