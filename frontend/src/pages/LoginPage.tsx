import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ApiRequestError } from "../services/api";
import { Card, ErrorBanner, Field, PrimaryButton, TextInput } from "../components/ui";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Login failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-canopy-50 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-2 text-center">
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-canopy-700 font-display text-base font-semibold text-white">
            GF
          </span>
          <h1 className="font-display text-xl font-semibold text-ink">GreenFarm Carbon AI</h1>
          <p className="text-sm text-ink/60">Estimate your farm's carbon footprint.</p>
        </div>

        <Card>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {error && <ErrorBanner message={error} />}
            <Field label="Email">
              <TextInput
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@farm.com"
              />
            </Field>
            <Field label="Password">
              <TextInput
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </Field>
            <PrimaryButton type="submit" isLoading={isSubmitting}>
              Log in
            </PrimaryButton>
          </form>
        </Card>

        <p className="mt-4 text-center text-sm text-ink/60">
          Don't have an account?{" "}
          <Link to="/register" className="font-medium text-canopy-700 hover:underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
