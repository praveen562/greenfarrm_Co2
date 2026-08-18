import type { RecommendationItem, RecommendationPlan } from "../types";
import { Badge, Card } from "./ui";

const PRIORITY_TONE: Record<RecommendationItem["priority"], "bad" | "moderate" | "neutral"> = {
  High: "bad",
  Medium: "moderate",
  Low: "neutral",
};

const CATEGORY_ICON: Record<string, string> = {
  Fertilizer: "🌱",
  Fuel: "⛽",
  Water: "💧",
  Electricity: "⚡",
  General: "🌾",
};

function RecommendationItemCard({ item, farmArea }: { item: RecommendationItem; farmArea?: number }) {
  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <span className="text-lg leading-none">{CATEGORY_ICON[item.category] ?? "🌾"}</span>
          <div>
            <Badge tone={PRIORITY_TONE[item.priority]}>{item.priority.toUpperCase()} PRIORITY</Badge>
            <p className="mt-1 font-display text-sm font-semibold text-ink">{item.title}</p>
          </div>
        </div>
        <div className="shrink-0 text-right">
          <p className="font-data text-lg font-semibold text-canopy-700">
            ~{item.estimated_reduction_percent}%
          </p>
          <p className="text-[11px] text-ink/50">est. reduction</p>
        </div>
      </div>

      <p className="text-sm text-ink/70">{item.problem}</p>

      <div className="rounded-lg bg-canopy-50/70 px-3 py-2">
        <p className="text-xs font-medium uppercase tracking-wide text-canopy-700">Recommended action</p>
        <p className="mt-1 text-sm text-ink/80">{item.action}</p>
      </div>

      <p className="text-xs text-ink/60">{item.advice}</p>

      <div className="flex flex-wrap gap-x-6 gap-y-1 border-t border-canopy-100 pt-2 text-xs text-ink/60">
        <span>
          Potential reduction:{" "}
          <span className="font-data font-medium text-ink">
            {item.estimated_reduction_kg_co2e_per_ha.toLocaleString()} kg CO2e/ha
          </span>
        </span>
        <span>
          Projected footprint:{" "}
          <span className="font-data font-medium text-ink">
            {item.projected_footprint_kg_co2e_per_ha.toLocaleString()} kg CO2e/ha
          </span>
        </span>
        {farmArea != null && (
          <span>
            For {farmArea} ha:{" "}
            <span className="font-data font-medium text-ink">
              {(item.estimated_reduction_kg_co2e_per_ha * farmArea).toLocaleString()} kg CO2e
            </span>
          </span>
        )}
      </div>
    </Card>
  );
}

export default function CarbonReductionPlan({
  plan,
  farmArea,
}: {
  plan: RecommendationPlan;
  farmArea?: number;
}) {
  return (
    <div className="flex flex-col gap-4">
      <Card className="bg-canopy-800 text-white">
        <p className="font-display text-sm font-semibold uppercase tracking-wide text-canopy-200">
          Carbon reduction plan
        </p>
        <div className="mt-3 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div>
            <p className="text-[11px] uppercase tracking-wide text-canopy-200/80">Current footprint</p>
            <p className="font-data text-xl font-semibold">
              {plan.baseline_carbon_footprint.toLocaleString()}
            </p>
            <p className="text-[11px] text-canopy-200/70">kg CO2e/ha</p>
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-wide text-canopy-200/80">Estimated reduction</p>
            <p className="font-data text-xl font-semibold">{plan.estimated_total_reduction_percent}%</p>
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-wide text-canopy-200/80">Potential reduction</p>
            <p className="font-data text-xl font-semibold">
              {plan.estimated_total_reduction_kg_co2e_per_ha.toLocaleString()}
            </p>
            <p className="text-[11px] text-canopy-200/70">kg CO2e/ha</p>
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-wide text-canopy-200/80">Projected footprint</p>
            <p className="font-data text-xl font-semibold">
              {plan.projected_carbon_footprint.toLocaleString()}
            </p>
            <p className="text-[11px] text-canopy-200/70">kg CO2e/ha</p>
          </div>
        </div>
        {farmArea != null && (
          <p className="mt-3 border-t border-white/10 pt-3 text-xs text-canopy-100/90">
            For a {farmArea} ha farm: potential reduction of{" "}
            <span className="font-data font-semibold text-white">
              {plan.estimated_total_reduction_kg_co2e_per_farm.toLocaleString()} kg CO2e
            </span>
          </p>
        )}
      </Card>

      {plan.recommendations.length === 0 ? (
        <Card className="bg-canopy-50/60">
          <p className="text-sm text-ink/70">
            All major inputs are already within a typical range for this crop — no specific reduction actions
            triggered this time. Keep monitoring year over year.
          </p>
        </Card>
      ) : (
        <div className="flex flex-col gap-3">
          {plan.recommendations.map((item, idx) => (
            <RecommendationItemCard key={idx} item={item} farmArea={farmArea} />
          ))}
        </div>
      )}

      <p className="rounded-lg border border-clay/30 bg-clay/5 px-3 py-2 text-xs text-soil-700">
        ⚠️ Simulation only. {plan.simulation_notice}
      </p>
    </div>
  );
}
