import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { Badge, Card, EmptyState, ErrorBanner, LoadingBlock } from "../components/ui";
import * as api from "../services/api";
import { ApiRequestError } from "../services/api";
import type { CarbonPredictionResponse } from "../types";

const CATEGORY_TONE: Record<string, "good" | "moderate" | "bad"> = {
  Low: "good",
  Moderate: "moderate",
  High: "bad",
  "Very High": "bad",
};

export default function HistoryPage() {
  const [predictions, setPredictions] = useState<CarbonPredictionResponse[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getPredictionHistory()
      .then(setPredictions)
      .catch((err) => setError(err instanceof ApiRequestError ? err.message : "Could not load history."));
  }, []);

  return (
    <AppShell>
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink">Prediction history</h1>
          <p className="text-sm text-ink/60">Every carbon prediction you've made, across all your farms.</p>
        </div>

        {error && <ErrorBanner message={error} />}
        {predictions === null && !error && <LoadingBlock label="Loading history…" />}

        {predictions !== null && predictions.length === 0 && (
          <EmptyState
            title="No predictions yet"
            description="Run a prediction from the Predict page to see it show up here."
          />
        )}

        {predictions !== null && predictions.length > 0 && (
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-canopy-100 text-xs uppercase tracking-wide text-ink/40">
                    <th className="py-2 pr-4">Date</th>
                    <th className="py-2 pr-4">Crop</th>
                    <th className="py-2 pr-4">Footprint</th>
                    <th className="py-2 pr-4">Total emissions</th>
                    <th className="py-2 pr-4">Score</th>
                    <th className="py-2">Category</th>
                  </tr>
                </thead>
                <tbody>
                  {predictions.map((p) => (
                    <tr key={p.prediction_id} className="border-b border-canopy-50 last:border-0">
                      <td className="py-2 pr-4">{new Date(p.created_at).toLocaleDateString()}</td>
                      <td className="py-2 pr-4">{p.crop_type}</td>
                      <td className="py-2 pr-4 font-data">
                        {p.carbon_footprint_kg_co2e_per_ha.toLocaleString()} kg/ha
                      </td>
                      <td className="py-2 pr-4 font-data">{p.total_farm_emissions_kg_co2e.toLocaleString()} kg</td>
                      <td className="py-2 pr-4 font-data">{p.sustainability_score}</td>
                      <td className="py-2">
                        <Badge tone={CATEGORY_TONE[p.carbon_category] ?? "neutral"}>{p.carbon_category}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
