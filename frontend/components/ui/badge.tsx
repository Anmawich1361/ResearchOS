import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex w-fit items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary/15 text-primary ring-1 ring-primary/20",
        secondary:
          "border-border bg-secondary text-secondary-foreground",
        outline: "border-border text-muted-foreground",
        data: "border-cyan-400/30 bg-cyan-400/10 text-cyan-200",
        inference: "border-emerald-400/30 bg-emerald-400/10 text-emerald-200",
        narrative: "border-amber-400/30 bg-amber-400/10 text-amber-200",
        question: "border-violet-400/30 bg-violet-400/10 text-violet-200",
        risk: "border-rose-400/30 bg-rose-400/10 text-rose-200",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div
      data-slot="badge"
      className={cn(badgeVariants({ variant, className }))}
      {...props}
    />
  );
}
