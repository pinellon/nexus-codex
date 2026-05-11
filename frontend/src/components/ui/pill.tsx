import { cn } from "@/lib/utils";

const toneClasses: Record<string, string> = {
  cyan: "border-accent-cyan/30 bg-accent-cyan/10 text-accent-cyan",
  amber: "border-accent-amber/30 bg-accent-amber/10 text-accent-amber",
  lime: "border-accent-lime/30 bg-accent-lime/10 text-accent-lime",
  orange: "border-accent-orange/30 bg-accent-orange/10 text-accent-orange",
  rose: "border-accent-rose/30 bg-accent-rose/10 text-accent-rose",
  sky: "border-accent-sky/30 bg-accent-sky/10 text-accent-sky",
};

type PillProps = {
  label: string;
  tone?: keyof typeof toneClasses;
  className?: string;
};

export function Pill({ label, tone = "cyan", className }: PillProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-3 py-1 font-mono text-[11px] uppercase tracking-[0.28em]",
        toneClasses[tone],
        className,
      )}
    >
      {label}
    </span>
  );
}
