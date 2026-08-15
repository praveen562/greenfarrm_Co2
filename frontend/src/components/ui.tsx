import type { InputHTMLAttributes, LabelHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl2 border border-canopy-100 bg-white p-5 shadow-soft ${className}`}>
      {children}
    </div>
  );
}

export function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: ReactNode;
  hint?: string;
}) {
  return (
    <label className="flex flex-col gap-1.5 text-sm">
      <span className="font-medium text-ink/80">{label}</span>
      {children}
      {hint && <span className="text-xs text-ink/40">{hint}</span>}
    </label>
  );
}

export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`rounded-lg border border-canopy-200 bg-paper px-3 py-2 text-sm text-ink outline-none transition-colors focus:border-canopy-500 focus:ring-2 focus:ring-canopy-100 ${props.className ?? ""}`}
    />
  );
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={`rounded-lg border border-canopy-200 bg-paper px-3 py-2 text-sm text-ink outline-none transition-colors focus:border-canopy-500 focus:ring-2 focus:ring-canopy-100 ${props.className ?? ""}`}
    />
  );
}

export function PrimaryButton({
  children,
  isLoading,
  ...rest
}: LabelHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  isLoading?: boolean;
  type?: "button" | "submit";
  disabled?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      {...rest}
      disabled={rest.disabled || isLoading}
      className="inline-flex items-center justify-center gap-2 rounded-lg bg-canopy-700 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-canopy-800 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {isLoading ? "Working…" : children}
    </button>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-rust/30 bg-rust/5 px-3 py-2 text-sm text-rust">
      {message}
    </div>
  );
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl2 border border-dashed border-canopy-200 bg-canopy-50/50 px-6 py-12 text-center">
      <p className="font-display text-base font-semibold text-canopy-800">{title}</p>
      <p className="mt-1.5 max-w-sm text-sm text-ink/60">{description}</p>
    </div>
  );
}

export function LoadingBlock({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center py-12">
      <p className="font-mono text-sm text-canopy-600">{label}</p>
    </div>
  );
}

export function Badge({ tone, children }: { tone: "good" | "moderate" | "bad" | "neutral"; children: ReactNode }) {
  const toneClasses: Record<typeof tone, string> = {
    good: "bg-canopy-100 text-canopy-800",
    moderate: "bg-clay/15 text-soil-700",
    bad: "bg-rust/10 text-rust",
    neutral: "bg-canopy-50 text-ink/60",
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${toneClasses[tone]}`}>
      {children}
    </span>
  );
}
