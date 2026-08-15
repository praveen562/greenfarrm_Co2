import axios, { AxiosError } from "axios";
import type {
  CarbonPredictionRequest,
  CarbonPredictionResponse,
  CropStat,
  DashboardSummary,
  Farm,
  HistoryPoint,
  User,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const TOKEN_STORAGE_KEY = "greenfarm_token";

const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export class ApiRequestError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.status = status;
  }
}

function extractErrorMessage(error: unknown): ApiRequestError {
  if (axios.isAxiosError(error)) {
    const err = error as AxiosError<{ detail?: string | { msg: string }[] }>;
    const status = err.response?.status;
    const detail = err.response?.data?.detail;

    if (!err.response) {
      return new ApiRequestError(
        "Could not reach the server. Check that the backend is running.",
        undefined,
      );
    }
    if (Array.isArray(detail)) {
      return new ApiRequestError(detail.map((d) => d.msg).join("; "), status);
    }
    if (typeof detail === "string") {
      return new ApiRequestError(detail, status);
    }
    return new ApiRequestError("Something went wrong. Please try again.", status);
  }
  return new ApiRequestError("An unexpected error occurred.");
}

async function request<T>(fn: () => Promise<{ data: T }>): Promise<T> {
  try {
    const response = await fn();
    return response.data;
  } catch (error) {
    throw extractErrorMessage(error);
  }
}

// --- Auth ---
export function register(email: string, password: string, fullName: string) {
  return request<User>(() =>
    api.post("/auth/register", { email, password, full_name: fullName }),
  );
}

export function login(email: string, password: string) {
  return request<{ access_token: string; token_type: string }>(() =>
    api.post("/auth/login", { email, password }),
  );
}

export function getCurrentUser() {
  return request<User>(() => api.get("/auth/me"));
}

// --- Farms ---
export function createFarm(payload: {
  farm_name: string;
  location: string;
  area: number;
  crop_type: string;
}) {
  return request<Farm>(() => api.post("/farms/", payload));
}

export function listFarms() {
  return request<Farm[]>(() => api.get("/farms/"));
}

export function deleteFarm(farmId: number) {
  return request<void>(() => api.delete(`/farms/${farmId}`));
}

// --- Predictions ---
export function predictCarbon(payload: CarbonPredictionRequest) {
  return request<CarbonPredictionResponse>(() => api.post("/predictions/carbon", payload));
}

export function getPredictionHistory() {
  return request<CarbonPredictionResponse[]>(() => api.get("/predictions/history"));
}

// --- Dashboard ---
export function getDashboardSummary() {
  return request<DashboardSummary>(() => api.get("/dashboard/summary"));
}

export function getDashboardHistory() {
  return request<HistoryPoint[]>(() => api.get("/dashboard/history"));
}

export function getCropStats() {
  return request<CropStat[]>(() => api.get("/dashboard/crop-stats"));
}

// --- Model info ---
export interface ModelInfo {
  model_name: string;
  metrics: { mae: number; rmse: number; r2: number };
  feature_importance: { feature: string; importance_pct: number }[];
  n_train: number;
  n_test: number;
}

export function getModelInfo() {
  return request<ModelInfo>(() => api.get("/model/info"));
}

export default api;
