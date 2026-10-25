import type { PredictionExplanation } from "../types";
import { Card } from "./ui";

function fmt(n: number, digits = 1): string {
  return n.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function signed(n: number): string {
  if (Math.abs(n) < 0.05) return "≈ 0";
  return `${n > 0 ? "+" : "−"}${fmt(Math.abs(n))}`;
}

function inputText(value: number | string, unit: string): string {
  if (typeof value === "string") return value;
  return `${value.toLocaleString()} ${unit}`;
}

/**
 * "Why this footprint?" — a diverging bar chart of exact SHAP values.
 * Bars to the right (▲) push the footprint above the model's average, bars to
 * the left (▼) pull it below. Direction is also written as a sign and an arrow,
 * so the chart never relies on colour alone.
 */
export default function ExplanationChart({
  explanation,
  footprint,
}: {
  explanation: PredictionExplanation;
  footprint: number;
}) {
  const maxAbs = Math.max(...explanation.factors.map((f) => Math.abs(f.contribution_kg_co2e_per_ha)), 1);

  return (
    <Card>
      <div className="flex flex-col gap-4">
        <div>
          <h2 className="font-display text-lg font-semibold text-ink">Why this footprint?</h2>
          <p className="text-sm text-ink/60">
            How each input moved the prediction away from the model's average of{" "}
            <span className="font-data font-medium text-ink">{fmt(explanation.base_value)}</span> kg CO2e/ha, to{" "}
            <span className="font-data font-medium text-ink">{fmt(footprint)}</span> for this farm.
          </p>
        </div>

        <ul className="flex flex-col gap-2.5" aria-label="Contribution of each input to the carbon footprint">
          {explanation.factors.map((f) => {
            const c = f.contribution_kg_co2e_per_ha;
            const widthPct = (Math.abs(c) / maxAbs) * 50;
            const up = c > 0;
            return (
              <li
                key={f.feature}
                className="grid grid-cols-[6.5rem_1fr_5.5rem] items-center gap-3 sm:grid-cols-[9rem_1fr_6rem]"
                aria-label={`${f.label} ${inputText(f.value, f.unit)} ${f.direction} the footprint by ${fmt(Math.abs(c))} kg CO2e per hectare`}
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-ink">{f.label}</p>
                  <p className="truncate font-data text-[11px] text-ink/50">{inputText(f.value, f.unit)}</p>
                </div>
                <div className="relative h-5 rounded bg-canopy-50" aria-hidden="true">
                  <div className="absolute inset-y-0 left-1/2 w-px bg-ink/25" />
                  <div
                    className={`absolute inset-y-0.5 rounded-sm ${up ? "left-1/2 bg-rust/70" : "right-1/2 bg-canopy-500"}`}
                    style={{ width: `${widthPct}%` }}
                  />
                </div>
                <p className={`text-right font-data text-sm font-medium ${up ? "text-rust" : "text-canopy-700"}`}>
                  {Math.abs(c) >= 0.05 && <span aria-hidden="true">{up ? "▲ " : "▼ "}</span>}
                  {signed(c)}
                </p>
              </li>
            );
          })}
        </ul>

        <div className="flex flex-wrap items-center gap-x-5 gap-y-1 border-t border-canopy-100 pt-3 text-xs text-ink/60">
          <span>
            <span className="text-rust" aria-hidden="true">▲</span> raises the footprint
          </span>
          <span>
            <span className="text-canopy-700" aria-hidden="true">▼</span> lowers it
          </span>
          <span>Unit: kg CO2e/ha</span>
        </div>
        <p className="text-[11px] text-ink/40">{explanation.method}. {explanation.note}</p>
      </div>
    </Card>
  );
}
