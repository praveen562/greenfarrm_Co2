import { useEffect, useState, type FormEvent } from "react";
import AppShell from "../components/AppShell";
import {
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
import { CROP_TYPES, type CropType, type Farm } from "../types";

export default function FarmsPage() {
  const [farms, setFarms] = useState<Farm[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [farmName, setFarmName] = useState("");
  const [location, setLocation] = useState("");
  const [area, setArea] = useState("");
  const [cropType, setCropType] = useState(CROP_TYPES[0]);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function loadFarms() {
    try {
      const data = await api.listFarms();
      setFarms(data);
    } catch (err) {
      setLoadError(err instanceof ApiRequestError ? err.message : "Could not load farms.");
    }
  }

  useEffect(() => {
    loadFarms();
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    setIsSubmitting(true);
    try {
      await api.createFarm({
        farm_name: farmName,
        location,
        area: Number(area),
        crop_type: cropType,
      });
      setFarmName("");
      setLocation("");
      setArea("");
      setCropType(CROP_TYPES[0]);
      await loadFarms();
    } catch (err) {
      setFormError(err instanceof ApiRequestError ? err.message : "Could not create farm.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDelete(farmId: number) {
    try {
      await api.deleteFarm(farmId);
      await loadFarms();
    } catch (err) {
      setLoadError(err instanceof ApiRequestError ? err.message : "Could not delete farm.");
    }
  }

  return (
    <AppShell>
      <div className="mx-auto flex max-w-3xl flex-col gap-6">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink">Farms</h1>
          <p className="text-sm text-ink/60">Add a farm before running a carbon prediction.</p>
        </div>

        <Card>
          <h2 className="mb-4 font-display text-base font-semibold text-ink">Add a new farm</h2>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {formError && <ErrorBanner message={formError} />}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field label="Farm name">
                <TextInput
                  required
                  value={farmName}
                  onChange={(e) => setFarmName(e.target.value)}
                  placeholder="Green Acres"
                />
              </Field>
              <Field label="Location">
                <TextInput
                  required
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Punjab, India"
                />
              </Field>
              <Field label="Area (hectares)">
                <TextInput
                  type="number"
                  required
                  min={0.01}
                  step="0.01"
                  value={area}
                  onChange={(e) => setArea(e.target.value)}
                  placeholder="10.5"
                />
              </Field>
              <Field label="Crop type">
                <Select value={cropType} onChange={(e) => setCropType(e.target.value as CropType)}>
                  {CROP_TYPES.map((crop) => (
                    <option key={crop} value={crop}>
                      {crop}
                    </option>
                  ))}
                </Select>
              </Field>
            </div>
            <div>
              <PrimaryButton type="submit" isLoading={isSubmitting}>
                Add farm
              </PrimaryButton>
            </div>
          </form>
        </Card>

        <div>
          <h2 className="mb-3 font-display text-base font-semibold text-ink">Your farms</h2>
          {loadError && <ErrorBanner message={loadError} />}
          {farms === null && !loadError && <LoadingBlock label="Loading farms…" />}
          {farms !== null && farms.length === 0 && (
            <EmptyState
              title="No farms yet"
              description="Add your first farm above to start predicting its carbon footprint."
            />
          )}
          {farms !== null && farms.length > 0 && (
            <div className="flex flex-col gap-3">
              {farms.map((farm) => (
                <Card key={farm.id} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-ink">{farm.farm_name}</p>
                    <p className="text-sm text-ink/60">
                      {farm.crop_type} · {farm.area} ha · {farm.location}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDelete(farm.id)}
                    className="text-xs font-medium text-rust hover:underline"
                  >
                    Delete
                  </button>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
