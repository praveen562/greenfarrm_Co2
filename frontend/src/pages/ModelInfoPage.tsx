import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import AppShell from "../components/AppShell";
import { Card, ErrorBanner, LoadingBlock } from "../components/ui";
import * as api from "../services/api";
import { ApiRequestError } from "../services/api";
import type { ModelInfo } from "../services/api";

function humanizeFeatureName(feature: string): string {
  const cleaned = feature.replace(/^(numeric__|categorical__)/, "").replace(/_/g, " ");
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
}

export default function ModelInfoPage() {
  const [info, setInfo] = useState<ModelInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getModelInfo()
      .then(setInfo)
      .catch((err) => setError(err instanceof ApiRequestError ? err.message : "Could not load model info."));
  }, []);

  if (error) {
    return (
      <AppShell>
        <ErrorBanner message={error} />
      </AppShell>
    );
  }

  if (!info) {
    return (
      <AppShell>
        <LoadingBlock label="Loading model info…" />
      </AppShell>
    );
  }

  const chartData = [...info.feature_importance]
    .sort((a, b) => b.importance_pct - a.importance_pct)
    .map((f) => ({ name: humanizeFeatureName(f.feature), value: f.importance_pct }));

  return (
    <AppShell>
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink">Model information</h1>
          <p className="text-sm text-ink/60">
            Production model: <span className="font-medium text-ink">{info.model_name}</span> — metrics from the
            held-out test set ({info.n_test.toLocaleString()} rows, trained on {info.n_train.toLocaleString()}).
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Card>
            <p className="text-xs uppercase tracking-wide text-ink/40">MAE</p>
            <p className="font-data mt-1 text-2xl font-semibold text-ink">{info.metrics.mae.toFixed(2)}</p>
            <p className="mt-0.5 text-xs text-ink/50">kg CO2e/ha</p>
          </Card>
          <Card>
            <p className="text-xs uppercase tracking-wide text-ink/40">RMSE</p>
            <p className="font-data mt-1 text-2xl font-semibold text-ink">{info.metrics.rmse.toFixed(2)}</p>
            <p className="mt-0.5 text-xs text-ink/50">kg CO2e/ha</p>
          </Card>
          <Card>
            <p className="text-xs uppercase tracking-wide text-ink/40">R²</p>
            <p className="font-data mt-1 text-2xl font-semibold text-ink">{info.metrics.r2.toFixed(4)}</p>
            <p className="mt-0.5 text-xs text-ink/50">held-out test set</p>
          </Card>
        </div>

        <Card>
          <p className="mb-3 font-display text-sm font-semibold text-ink">Feature importance</p>
          <ResponsiveContainer width="100%" height={Math.max(240, chartData.length * 32)}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E4F2E9" />
              <XAxis type="number" tick={{ fontSize: 11 }} stroke="#5FAD82" unit="%" />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} stroke="#5FAD82" width={140} />
              <Tooltip
                formatter={(value) => [`${Number(value).toFixed(2)}%`, "Importance"]}
                contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: "#C3E4D0" }}
              />
              <Bar dataKey="value" fill="#2C7350" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card className="bg-canopy-50/60">
          <p className="text-sm text-ink/70">
            This system provides an estimated farm-level carbon footprint using agricultural activity inputs and a
            trained XGBoost regression model. It is a prototype decision-support system and not a complete Life
            Cycle Assessment.
          </p>
        </Card>
      </div>
    </AppShell>
  );
}
