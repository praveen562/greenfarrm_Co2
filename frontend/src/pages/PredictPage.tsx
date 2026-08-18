import { useEffect, useState, type FormEvent } from "react";
import AppShell from "../components/AppShell";
import GrowthRing from "../components/GrowthRing";
import CarbonReductionPlan from "../components/CarbonReductionPlan";
import {
  Badge,
  Card,
  EmptyState,
  ErrorBanner,
  Field,
  LoadingBlock,
  PrimaryButton,
  Select,
  TextInput,
} from "../components/ui";
import * as api from "../services/api";
import { ApiRequestError } from "../services/api";
import type { CarbonPredictionResponse, Farm } from "../types";

const CATEGORY_TONE: Record<string, "good" | "moderate" | "bad"> = {
  Low: "good",
  Moderate: "moderate",
  High: "bad",
  "Very High": "bad",
};

export default function PredictPage() {
  const [farms, setFarms] = useState<Farm[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [farmId, setFarmId] = useState<string>("");
  const [fertilizer, setFertilizer] = useState("");
  const [fuel, setFuel] = useState("");
  const [water, setWater] = useState("");
  const [electricity, setElectricity] = useState("");

  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<CarbonPredictionResponse | null>(null);

  useEffect(() => {
    api
      .listFarms()
      .then((data) => {
        setFarms(data);
        if (data.length > 0) setFarmId(String(data[0].id));
      })
      .catch((err) => setLoadError(err instanceof ApiRequestError ? err.message : "Could not load farms."));
  }, []);

  const selectedFarm = farms?.find((f) => String(f.id) === farmId) ?? null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    setResult(null);
    setIsSubmitting(true);
    try {
      const prediction = await api.predictCarbon({
        farm_id: Number(farmId),
        fertilizer_usage_kg_per_ha: Number(fertilizer),
        fuel_consumption_liters_per_ha: Number(fuel),
        water_consumption_m3_per_ha: Number(water),
        electricity_consumption_kwh_per_ha: Number(electricity),
      });
      setResult(prediction);
    } catch (err) {
      setFormError(err instanceof ApiRequestError ? err.message : "Prediction failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (farms === null && !loadError) {
    return (
      <AppShell>
        <LoadingBlock label="Loading farms…" />
      </AppShell>
    );
  }

  if (farms !== null && farms.length === 0) {
    return (
      <AppShell>
        <EmptyState
          title="Add a farm first"
          description="You need at least one farm before you can run a carbon prediction. Head to the Farms page to add one."
        />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mx-auto flex max-w-3xl flex-col gap-6">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink">Predict carbon footprint</h1>
          <p className="text-sm text-ink/60">
            Enter this season's farm inputs. Crop type and area come from the selected farm.
          </p>
        </div>

        {loadError && <ErrorBanner message={loadError} />}

        <Card>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {formError && <ErrorBanner message={formError} />}
            <Field label="Farm">
              <Select value={farmId} onChange={(e) => setFarmId(e.target.value)}>
                {farms?.map((farm) => (
                  <option key={farm.id} value={farm.id}>
                    {farm.farm_name} — {farm.crop_type} ({farm.area} ha)
                  </option>
                ))}
              </Select>
            </Field>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field label="Fertilizer usage" hint="kg / ha">
                <TextInput
                  type="number"
                  required
                  min={0.01}
                  step="0.01"
                  value={fertilizer}
                  onChange={(e) => setFertilizer(e.target.value)}
                  placeholder="180"
                />
              </Field>
              <Field label="Fuel consumption" hint="liters / ha">
                <TextInput
                  type="number"
                  required
                  min={0}
                  step="0.01"
                  value={fuel}
                  onChange={(e) => setFuel(e.target.value)}
                  placeholder="60"
                />
              </Field>
              <Field label="Water consumption" hint="m³ / ha">
                <TextInput
                  type="number"
                  required
                  min={0}
                  step="0.01"
                  value={water}
                  onChange={(e) => setWater(e.target.value)}
                  placeholder="8000"
                />
              </Field>
              <Field label="Electricity consumption" hint="kWh / ha">
                <TextInput
                  type="number"
                  required
                  min={0}
                  step="0.01"
                  value={electricity}
                  onChange={(e) => setElectricity(e.target.value)}
                  placeholder="400"
                />
              </Field>
            </div>

            <div>
              <PrimaryButton type="submit" isLoading={isSubmitting}>
                Predict carbon footprint
              </PrimaryButton>
            </div>
          </form>
        </Card>

        {result && (
          <Card>
            <div className="flex flex-col gap-6">
              <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-xs uppercase tracking-wide text-ink/40">Carbon footprint</p>
                  <p className="font-data text-3xl font-semibold text-ink">
                    {result.carbon_footprint_kg_co2e_per_ha.toLocaleString()}{" "}
                    <span className="text-base font-normal text-ink/50">kg CO2e/ha</span>
                  </p>
                  <p className="mt-1 text-sm text-ink/60">
                    Total farm emissions:{" "}
                    <span className="font-medium text-ink">
                      {result.total_farm_emissions_kg_co2e.toLocaleString()} kg CO2e
                    </span>{" "}
                    ({selectedFarm?.area} ha)
                  </p>
                  <div className="mt-2 flex gap-2">
                    <Badge tone={CATEGORY_TONE[result.carbon_category] ?? "neutral"}>
                      {result.carbon_category}
                    </Badge>
                    <Badge tone="neutral">Model: {result.model_used}</Badge>
                  </div>
                </div>
                <div className="flex flex-col items-center gap-1">
                  <GrowthRing score={result.sustainability_score} category={result.sustainability_category} />
                  <p className="text-sm font-medium text-ink">{result.sustainability_category}</p>
                </div>
              </div>
            </div>
          </Card>
        )}

        {result && <CarbonReductionPlan plan={result.recommendation_plan} farmArea={selectedFarm?.area} />}
      </div>
    </AppShell>
  );
}
