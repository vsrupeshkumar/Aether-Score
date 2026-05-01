import { ReactNode } from "react";
import { motion, HTMLMotionProps } from "framer-motion";
import { cn } from "@/app/lib/utils";

interface GlassCardProps extends Omit<HTMLMotionProps<"div">, "children"> {
  children: ReactNode;
  variant?: "default" | "glow" | "gradient-border";
  hover?: boolean;
  className?: string;
}

export function GlassCard({ 
  children, 
  variant = "default", 
  hover = true,
  className,
  ...props 
}: GlassCardProps) {
  const baseClasses = cn(
    "relative rounded-2xl p-6",
    "glass border border-border/30",
    hover && "transition-all duration-300 hover:-translate-y-1 hover:border-primary/30 hover:shadow-[0_20px_40px_-12px_hsl(var(--primary)/0.15)]",
    className
  );

  if (variant === "glow") {
    return (
      <motion.div {...props} className={cn(baseClasses, "glow-cyan")}>
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-primary/5 to-secondary/5" />
        <div className="relative z-10">{children}</div>
      </motion.div>
    );
  }

  if (variant === "gradient-border") {
    return (
      <motion.div {...props} className={cn("relative rounded-2xl p-[1px]", hover && "transition-transform duration-300 hover:-translate-y-1")}>
        <div className="absolute inset-0 rounded-2xl bg-gradient-primary opacity-50" />
        <div className={cn("relative rounded-2xl p-6 glass", className?.includes("h-") ? "" : "h-full")}>
          {children}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div {...props} className={baseClasses}>
      {children}
    </motion.div>
  );
}
