import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import AppShell from "../components/AppShell";
import { Card, EmptyState, ErrorBanner, LoadingBlock } from "../components/ui";
import * as api from "../services/api";
import { ApiRequestError } from "../services/api";
import type { CropStat, DashboardSummary, HistoryPoint } from "../types";

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <Card>
      <p className="text-xs uppercase tracking-wide text-ink/40">{label}</p>
      <p className="font-data mt-1 text-2xl font-semibold text-ink">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-ink/50">{sub}</p>}
    </Card>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [history, setHistory] = useState<HistoryPoint[] | null>(null);
  const [cropStats, setCropStats] = useState<CropStat[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.getDashboardSummary(), api.getDashboardHistory(), api.getCropStats()])
      .then(([summaryData, historyData, cropData]) => {
        setSummary(summaryData);
        setHistory(historyData);
        setCropStats(cropData);
      })
      .catch((err) => setError(err instanceof ApiRequestError ? err.message : "Could not load dashboard."));
  }, []);

  if (error) {
    return (
      <AppShell>
        <ErrorBanner message={error} />
      </AppShell>
    );
  }

  if (!summary || !history || !cropStats) {
    return (
      <AppShell>
        <LoadingBlock label="Loading dashboard…" />
      </AppShell>
    );
  }

  const chartHistory = history.map((h) => ({
    date: new Date(h.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
    footprint: h.carbon_footprint_kg_co2e_per_ha,
  }));

  return (
    <AppShell>
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink">Dashboard</h1>
          <p className="text-sm text-ink/60">A summary of your farms' carbon predictions.</p>
        </div>

        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard
            label="Latest footprint"
            value={
              summary.latest_carbon_footprint_kg_co2e_per_ha != null
                ? `${summary.latest_carbon_footprint_kg_co2e_per_ha.toLocaleString()}`
                : "—"
            }
            sub="kg CO2e/ha"
          />
          <StatCard
            label="Average footprint"
            value={
              summary.average_carbon_footprint_kg_co2e_per_ha != null
                ? `${summary.average_carbon_footprint_kg_co2e_per_ha.toLocaleString()}`
                : "—"
            }
            sub="kg CO2e/ha"
          />
          <StatCard
            label="Avg. sustainability score"
            value={summary.average_sustainability_score != null ? `${summary.average_sustainability_score}` : "—"}
            sub="out of 100"
          />
          <StatCard label="Predictions made" value={String(summary.total_predictions)} sub={`${summary.total_farms} farm(s)`} />
        </div>

        {summary.total_predictions === 0 ? (
          <EmptyState
            title="No predictions yet"
            description="Add a farm and run your first carbon prediction to see your dashboard come to life."
          />
        ) : (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card>
              <p className="mb-3 font-display text-sm font-semibold text-ink">Carbon footprint history</p>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={chartHistory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E4F2E9" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#5FAD82" />
                  <YAxis tick={{ fontSize: 11 }} stroke="#5FAD82" width={40} />
                  <Tooltip
                    formatter={(value) => [`${value} kg CO2e/ha`, "Footprint"]}
                    contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: "#C3E4D0" }}
                  />
                  <Line type="monotone" dataKey="footprint" stroke="#2C7350" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </Card>

            <Card>
              <p className="mb-3 font-display text-sm font-semibold text-ink">Crop-wise average footprint</p>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={cropStats}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E4F2E9" />
                  <XAxis dataKey="crop_type" tick={{ fontSize: 11 }} stroke="#5FAD82" />
                  <YAxis tick={{ fontSize: 11 }} stroke="#5FAD82" width={40} />
                  <Tooltip
                    formatter={(value) => [`${value} kg CO2e/ha`, "Avg. footprint"]}
                    contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: "#C3E4D0" }}
                  />
                  <Bar dataKey="average_carbon_footprint_kg_co2e_per_ha" fill="#3B8F65" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </div>
        )}

        {summary.recent_predictions.length > 0 && (
          <Card>
            <p className="mb-3 font-display text-sm font-semibold text-ink">Recent predictions</p>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-canopy-100 text-xs uppercase tracking-wide text-ink/40">
                    <th className="py-2 pr-4">Farm</th>
                    <th className="py-2 pr-4">Crop</th>
                    <th className="py-2 pr-4">Footprint</th>
                    <th className="py-2 pr-4">Category</th>
                    <th className="py-2">Score</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.recent_predictions.map((p) => (
                    <tr key={p.prediction_id} className="border-b border-canopy-50 last:border-0">
                      <td className="py-2 pr-4">{p.farm_name}</td>
                      <td className="py-2 pr-4">{p.crop_type}</td>
                      <td className="py-2 pr-4 font-data">{p.carbon_footprint_kg_co2e_per_ha} kg/ha</td>
                      <td className="py-2 pr-4">{p.carbon_category}</td>
                      <td className="py-2 font-data">{p.sustainability_score ?? "—"}</td>
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
