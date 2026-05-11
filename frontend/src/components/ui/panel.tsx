import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

const glowMap: Record<string, string> = {
  cyan: "shadow-[0_0_0_1px_rgba(56,218,255,0.08),0_25px_90px_rgba(4,20,36,0.68)]",
  amber: "shadow-[0_0_0_1px_rgba(255,191,71,0.08),0_25px_90px_rgba(4,20,36,0.68)]",
  lime: "shadow-[0_0_0_1px_rgba(120,242,146,0.08),0_25px_90px_rgba(4,20,36,0.68)]",
  orange: "shadow-[0_0_0_1px_rgba(255,136,62,0.08),0_25px_90px_rgba(4,20,36,0.68)]",
  rose: "shadow-[0_0_0_1px_rgba(255,110,128,0.08),0_25px_90px_rgba(4,20,36,0.68)]",
  sky: "shadow-[0_0_0_1px_rgba(102,192,255,0.08),0_25px_90px_rgba(4,20,36,0.68)]",
};

const beamMap: Record<string, string> = {
  cyan: "from-accent-cyan/0 via-accent-cyan/90 to-accent-cyan/0",
  amber: "from-accent-amber/0 via-accent-amber/90 to-accent-amber/0",
  lime: "from-accent-lime/0 via-accent-lime/90 to-accent-lime/0",
  orange: "from-accent-orange/0 via-accent-orange/90 to-accent-orange/0",
  rose: "from-accent-rose/0 via-accent-rose/90 to-accent-rose/0",
  sky: "from-accent-sky/0 via-accent-sky/90 to-accent-sky/0",
};

type PanelProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  tone?: keyof typeof glowMap;
};

export function Panel({ children, className, tone = "cyan", ...props }: PanelProps) {
  return (
    <div
      className={cn(
        "glass-outline relative overflow-hidden rounded-[28px] border border-white/8 bg-panel/75 backdrop-blur-xl",
        glowMap[tone],
        className,
      )}
      {...props}
    >
      <div className={cn("scanline animate-scan bg-gradient-to-r", beamMap[tone])} />
      <div className="absolute inset-x-8 top-0 h-px bg-white/8" />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
