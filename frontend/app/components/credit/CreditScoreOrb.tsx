import { useEffect, useState, useRef } from "react";
import { motion, useAnimation } from "framer-motion";
import { cn } from "@/app/lib/utils";

interface CreditScoreOrbProps {
  score: number;
  maxScore?: number;
  size?: "sm" | "md" | "lg";
  showBreakdown?: boolean;
  className?: string;
}

function getRiskLevel(score: number): { label: string; color: string; bgColor: string } {
  if (score >= 750) return { label: "Excellent", color: "text-success", bgColor: "bg-success" };
  if (score >= 600) return { label: "Good", color: "text-primary", bgColor: "bg-primary" };
  if (score >= 400) return { label: "Fair", color: "text-warning", bgColor: "bg-warning" };
  return { label: "Needs Work", color: "text-destructive", bgColor: "bg-destructive" };
}

export function CreditScoreOrb({ 
  score, 
  maxScore = 1000, 
  size = "lg",
  showBreakdown = false,
  className 
}: CreditScoreOrbProps) {
  const [displayScore, setDisplayScore] = useState(0);
  const [hasAnimated, setHasAnimated] = useState(false);
  const controls = useAnimation();
  const risk = getRiskLevel(score);
  const percentage = (score / maxScore) * 100;

  const sizeConfig = {
    sm: { container: "w-48 h-48", text: "text-4xl", sub: "text-sm" },
    md: { container: "w-64 h-64", text: "text-5xl", sub: "text-base" },
    lg: { container: "w-80 h-80", text: "text-6xl", sub: "text-lg" },
  };

  useEffect(() => {
    if (!hasAnimated) {
      setHasAnimated(true);
      
      // Animate score count up
      const duration = 2000;
      const steps = 60;
      const increment = score / steps;
      let current = 0;
      
      const timer = setInterval(() => {
        current += increment;
        if (current >= score) {
          setDisplayScore(score);
          clearInterval(timer);
        } else {
          setDisplayScore(Math.floor(current));
        }
      }, duration / steps);

      // Animate the ring
      controls.start({
        strokeDashoffset: 440 - (440 * percentage) / 100,
        transition: { duration: 2, ease: "easeOut" }
      });

      return () => clearInterval(timer);
    }
  }, [score, percentage, controls, hasAnimated]);

  return (
    <div className={cn("relative flex items-center justify-center", className)}>
      {/* Glow effect */}
      <div 
        className="absolute inset-0 rounded-full blur-3xl opacity-40"
        style={{
          background: `radial-gradient(circle, hsl(var(--primary) / 0.4) 0%, transparent 70%)`,
        }}
      />
      
      {/* Outer decorative ring */}
      <motion.div
        className={cn(
          "absolute rounded-full border border-primary/20",
          sizeConfig[size].container
        )}
        style={{ 
          width: size === "lg" ? 360 : size === "md" ? 300 : 220,
          height: size === "lg" ? 360 : size === "md" ? 300 : 220,
        }}
        animate={{ rotate: 360 }}
        transition={{ duration: 60, repeat: Infinity, ease: "linear" }}
      >
        {/* Orbiting particles */}
        {[0, 120, 240].map((rotation, i) => (
          <motion.div
            key={i}
            className="absolute w-2 h-2 bg-primary rounded-full"
            style={{
              top: "50%",
              left: "50%",
              transformOrigin: "center",
            }}
            animate={{
              rotate: 360,
            }}
            transition={{
              duration: 10 + i * 3,
              repeat: Infinity,
              ease: "linear",
              delay: i * 0.5,
            }}
          >
            <div 
              className="absolute w-2 h-2 bg-primary rounded-full shadow-[0_0_10px_hsl(var(--primary))]"
              style={{ 
                transform: `translateX(${size === "lg" ? 180 : size === "md" ? 150 : 110}px) rotate(${rotation}deg)` 
              }}
            />
          </motion.div>
        ))}
      </motion.div>

      {/* Main orb container */}
      <div className={cn(
        "relative flex items-center justify-center",
        sizeConfig[size].container
      )}>
        {/* SVG Ring */}
        <svg 
          className="absolute inset-0 -rotate-90"
          viewBox="0 0 160 160"
        >
          {/* Background ring */}
          <circle
            cx="80"
            cy="80"
            r="70"
            fill="none"
            stroke="hsl(var(--muted))"
            strokeWidth="3"
            strokeLinecap="round"
          />
          
          {/* Gradient definition */}
          <defs>
            <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="hsl(190, 100%, 50%)" />
              <stop offset="100%" stopColor="hsl(262, 83%, 58%)" />
            </linearGradient>
          </defs>
          
          {/* Animated score ring */}
          <motion.circle
            cx="80"
            cy="80"
            r="70"
            fill="none"
            stroke="url(#scoreGradient)"
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray="440"
            initial={{ strokeDashoffset: 440 }}
            animate={controls}
            style={{
              filter: "drop-shadow(0 0 8px hsl(var(--primary) / 0.5))"
            }}
          />
        </svg>

        {/* Inner glass container */}
        <div className={cn(
          "relative flex flex-col items-center justify-center rounded-full",
          "glass border border-border/30",
          size === "lg" ? "w-56 h-56" : size === "md" ? "w-44 h-44" : "w-32 h-32"
        )}>
          {/* Score display */}
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="text-center"
          >
            <span className={cn(
              "font-bold font-mono text-gradient glow-text",
              sizeConfig[size].text
            )}>
              {displayScore}
            </span>
            <p className={cn("text-muted-foreground", sizeConfig[size].sub)}>
              / {maxScore}
            </p>
          </motion.div>
        </div>
      </div>

      {/* Risk badge */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.5, duration: 0.5 }}
        className={cn(
          "absolute -bottom-4 left-1/2 -translate-x-1/2",
          "px-4 py-1.5 rounded-full",
          "glass border border-border/50",
          "flex items-center gap-2"
        )}
      >
        <div className={cn("w-2 h-2 rounded-full animate-pulse", risk.bgColor)} />
        <span className={cn("text-sm font-medium", risk.color)}>
          {risk.label}
        </span>
      </motion.div>
    </div>
  );
}
