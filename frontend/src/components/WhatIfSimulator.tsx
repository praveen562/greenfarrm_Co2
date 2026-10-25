import { useEffect, useMemo, useState } from "react";
import * as api from "../services/api";
import { ApiRequestError } from "../services/api";
import type { CarbonPredictionRequest, CropType, PredictionExplanation, WhatIfResponse } from "../types";
import { Badge, Card, ErrorBanner } from "./ui";

type InputKey =
  | "fertilizer_usage_kg_per_ha"
  | "fuel_consumption_liters_per_ha"
  | "water_consumption_m3_per_ha"
  | "electricity_consumption_kwh_per_ha";

type Inputs = Record<InputKey, number>;

interface SliderSpec {
  key: InputKey;
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
  /** [DATA-DERIVED] min/max of this input in ml/datasets/train.csv. */
  trainRange: [number, number];
  /** True when 0 itself is rejected (fertilizer must be > 0), matching the backend schema. */
  lowerExclusive: boolean;
  /** Hard server-side ceiling (backend/app/schemas/prediction.py); the API rejects anything above. */
  apiMax: number;
}

const SLIDERS: SliderSpec[] = [
  { key: "fertilizer_usage_kg_per_ha", label: "Fertilizer", unit: "kg/ha", min: 1, max: 400, step: 1, trainRange: [31.65, 280.05], lowerExclusive: true, apiMax: 2000 },
  { key: "fuel_consumption_liters_per_ha", label: "Fuel", unit: "L/ha", min: 0, max: 200, step: 1, trainRange: [28, 125.15], lowerExclusive: false, apiMax: 1000 },
  { key: "water_consumption_m3_per_ha", label: "Water", unit: "m³/ha", min: 0, max: 25000, step: 50, trainRange: [3050.79, 18885.6], lowerExclusive: false, apiMax: 100000 },
  { key: "electricity_consumption_kwh_per_ha", label: "Electricity", unit: "kWh/ha", min: 0, max: 1200, step: 5, trainRange: [105, 749.56], lowerExclusive: false, apiMax: 7500 },
];

const DEBOUNCE_MS = 250;

function fmt(n: number, digits = 1): string {
  return n.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function signed(n: number, digits = 1): string {
  if (Math.abs(n) < 0.5 * 10 ** -digits) return "0";
  return `${n > 0 ? "+" : "−"}${fmt(Math.abs(n), digits)}`;
}

function isValid(spec: SliderSpec, value: number): boolean {
  if (!Number.isFinite(value) || value > spec.apiMax) return false;
  return spec.lowerExclusive ? value > 0 : value >= 0;
}

function outsideTrainingRange(spec: SliderSpec, value: number): boolean {
  return value < spec.trainRange[0] || value > spec.trainRange[1];
}

function contributionOf(expl: PredictionExplanation, feature: string): number {
  return expl.factors.find((f) => f.feature === feature)?.contribution_kg_co2e_per_ha ?? 0;
}

/**
 * What-if simulator. Every slider move runs the *real* trained model on the
 * hypothetical inputs via POST /predictions/what-if (stateless: nothing is
 * stored, history is untouched). Requests are debounced, and a response is
 * ignored if the sliders have moved on since it was sent.
 */
export default function WhatIfSimulator({
  farmId,
  crop,
  farmArea,
  baselineInputs,
  baseline,
}: {
  farmId: number;
  crop: CropType;
  farmArea: number | undefined;
  baselineInputs: Inputs;
  baseline: {
    footprint: number;
    score: number;
    category: string;
    explanation: PredictionExplanation;
  };
}) {
  const [values, setValues] = useState<Inputs>(baselineInputs);
  const [scenario, setScenario] = useState<WhatIfResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const allValid = SLIDERS.every((s) => isValid(s, values[s.key]));
  const changed = SLIDERS.some((s) => values[s.key] !== baselineInputs[s.key]);

  useEffect(() => {
    if (!allValid || !changed) return;
    let cancelled = false;
    const timer = setTimeout(() => {
      setIsLoading(true);
      const payload: CarbonPredictionRequest = { farm_id: farmId, ...values };
      api
        .whatIf(payload)
        .then((res) => {
          if (cancelled) return;
          setScenario(res);
          setError(null);
        })
        .catch((err) => {
          if (cancelled) return;
          setError(err instanceof ApiRequestError ? err.message : "Could not run the scenario.");
        })
        .finally(() => {
          if (!cancelled) setIsLoading(false);
        });
    }, DEBOUNCE_MS);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [values, farmId, allValid, changed]);

  const shown = changed && allValid ? scenario : null;
  const delta = shown ? shown.carbon_footprint_kg_co2e_per_ha - baseline.footprint : 0;
  const deltaPct = shown && baseline.footprint !== 0 ? (delta / baseline.footprint) * 100 : 0;
  const farmDelta = farmArea != null ? delta * farmArea : null;

  const rows = useMemo(
    () =>
      baseline.explanation.factors.map((f) => {
        const before = f.contribution_kg_co2e_per_ha;
        const after = shown ? contributionOf(shown.explanation, f.feature) : before;
        return { feature: f.feature, label: f.label, before, after, change: after - before };
      }),
    [baseline.explanation, shown],
  );

  const totalChange = rows.reduce((sum, r) => sum + r.change, 0);

  function setValue(key: InputKey, value: number) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  function reset() {
    setValues(baselineInputs);
    setScenario(null);
    setError(null);
  }

  const better = shown != null && delta < -0.005;
  const worse = shown != null && delta > 0.005;

  return (
    <Card>
      <div className="flex flex-col gap-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-display text-lg font-semibold text-ink">What-if simulator</h2>
            <p className="text-sm text-ink/60">
              Change this {crop} farm's inputs and the trained model re-predicts instantly. Scenarios are{" "}
              <span className="font-medium text-ink">not saved</span> and don't touch your history.
            </p>
          </div>
          <button
            type="button"
            onClick={reset}
            disabled={!changed}
            className="rounded-lg border border-canopy-200 px-3 py-1.5 text-sm font-medium text-canopy-800 transition-colors hover:bg-canopy-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Reset to my inputs
          </button>
        </div>

        <div className="grid grid-cols-1 gap-x-8 gap-y-4 sm:grid-cols-2">
          {SLIDERS.map((spec) => {
            const value = values[spec.key];
            const base = baselineInputs[spec.key];
            const valid = isValid(spec, value);
            const max = Math.max(spec.max, base, Number.isFinite(value) ? Math.min(value, spec.apiMax) : 0);
            const outside = valid && outsideTrainingRange(spec, value);
            const inputId = `whatif-${spec.key}`;
            return (
              <div key={spec.key} className="flex flex-col gap-1.5">
                <div className="flex items-baseline justify-between gap-2">
                  <label htmlFor={inputId} className="text-sm font-medium text-ink/80">
                    {spec.label} <span className="text-xs font-normal text-ink/40">{spec.unit}</span>
                  </label>
                  <span className="font-data text-[11px] text-ink/40">yours: {base.toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    aria-label={`${spec.label} (${spec.unit})`}
                    min={spec.min}
                    max={max}
                    step={spec.step}
                    value={Number.isFinite(value) ? Math.min(Math.max(value, spec.min), max) : spec.min}
                    onChange={(e) => setValue(spec.key, Number(e.target.value))}
                    className="h-2 flex-1 cursor-pointer accent-canopy-600"
                  />
                  <input
                    id={inputId}
                    type="number"
                    min={spec.min}
                    step={spec.step}
                    value={Number.isFinite(value) ? value : ""}
                    onChange={(e) => setValue(spec.key, e.target.value === "" ? NaN : Number(e.target.value))}
                    className="w-24 rounded-lg border border-canopy-200 bg-paper px-2 py-1 text-right font-data text-sm text-ink outline-none focus:border-canopy-500 focus:ring-2 focus:ring-canopy-100"
                  />
                </div>
                {!valid && (
                  <p className="text-xs text-rust" role="alert">
                    {spec.lowerExclusive ? "Must be above 0" : "Must be 0 or more"} and at most{" "}
                    {spec.apiMax.toLocaleString()} {spec.unit}.
                  </p>
                )}
                {outside && (
                  <p className="text-xs text-soil-700">
                    Outside the model's training data ({spec.trainRange[0].toLocaleString()}–
                    {spec.trainRange[1].toLocaleString()} {spec.unit}), so treat this estimate as less reliable.
                  </p>
                )}
              </div>
            );
          })}
        </div>

        {error && <ErrorBanner message={error} />}

        <div
          className="rounded-xl border border-canopy-100 bg-canopy-50/60 p-4"
          aria-live="polite"
          aria-busy={isLoading}
        >
          {!shown ? (
            <p className="text-sm text-ink/60">
              {allValid
                ? "Move a slider to see how the footprint changes."
                : "Fix the highlighted value to run the scenario."}
            </p>
          ) : (
            <div className="flex flex-col gap-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div>
                  <p className="text-xs uppercase tracking-wide text-ink/40">Your prediction</p>
                  <p className="font-data text-xl font-semibold text-ink/70">{fmt(baseline.footprint, 2)}</p>
                  <p className="text-xs text-ink/50">
                    kg CO2e/ha · score {baseline.score} · {baseline.category}
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-ink/40">This scenario</p>
                  <p className={`font-data text-xl font-semibold text-ink ${isLoading ? "opacity-50" : ""}`}>
                    {fmt(shown.carbon_footprint_kg_co2e_per_ha, 2)}
                  </p>
                  <p className="text-xs text-ink/50">
                    kg CO2e/ha · score {shown.sustainability_score} · {shown.carbon_category}
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-ink/40">Change</p>
                  <p
                    className={`font-data text-xl font-semibold ${better ? "text-canopy-700" : worse ? "text-rust" : "text-ink/70"}`}
                  >
                    {better && <span aria-hidden="true">▼ </span>}
                    {worse && <span aria-hidden="true">▲ </span>}
                    {signed(delta, 2)}
                  </p>
                  <p className="text-xs text-ink/50">
                    {signed(deltaPct, 1)}%
                    {farmDelta != null && ` · ${signed(farmDelta, 0)} kg CO2e across ${farmArea} ha`}
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {shown.sustainability_score !== baseline.score && (
                  <Badge tone={shown.sustainability_score > baseline.score ? "good" : "bad"}>
                    Sustainability score {baseline.score} → {shown.sustainability_score}
                  </Badge>
                )}
                {shown.carbon_category !== baseline.category && (
                  <Badge tone={better ? "good" : "bad"}>
                    {baseline.category} → {shown.carbon_category}
                  </Badge>
                )}
              </div>

              <div className="overflow-x-auto">
                <table className="w-full min-w-[22rem] text-sm">
                  <caption className="mb-1 text-left text-xs text-ink/50">
                    How each factor's contribution (kg CO2e/ha) changed
                  </caption>
                  <thead>
                    <tr className="border-b border-canopy-100 text-left text-xs uppercase tracking-wide text-ink/40">
                      <th scope="col" className="py-1.5 pr-3 font-medium">Factor</th>
                      <th scope="col" className="py-1.5 pr-3 text-right font-medium">Yours</th>
                      <th scope="col" className="py-1.5 pr-3 text-right font-medium">Scenario</th>
                      <th scope="col" className="py-1.5 text-right font-medium">Change</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r) => (
                      <tr key={r.feature} className="border-b border-canopy-100/60 last:border-0">
                        <th scope="row" className="py-1.5 pr-3 text-left font-medium text-ink/80">{r.label}</th>
                        <td className="py-1.5 pr-3 text-right font-data text-ink/60">{signed(r.before)}</td>
                        <td className="py-1.5 pr-3 text-right font-data text-ink">{signed(r.after)}</td>
                        <td
                          className={`py-1.5 text-right font-data font-medium ${
                            r.change < -0.05 ? "text-canopy-700" : r.change > 0.05 ? "text-rust" : "text-ink/40"
                          }`}
                        >
                          {Math.abs(r.change) < 0.05 ? "—" : `${r.change < 0 ? "▼ " : "▲ "}${signed(r.change)}`}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="border-t border-canopy-200">
                      <th scope="row" className="py-1.5 pr-3 text-left font-medium text-ink">All factors</th>
                      <td className="py-1.5 pr-3" />
                      <td className="py-1.5 pr-3" />
                      <td className="py-1.5 text-right font-data font-semibold text-ink">{signed(totalChange)}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
              <p className="text-xs text-ink/50">
                Changing one input can shift how much the model credits the others, because it combines inputs
                rather than adding them separately. The factor changes always add up to the total change in
                footprint.
              </p>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
