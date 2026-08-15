import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ApiRequestError } from "../services/api";
import { Card, ErrorBanner, Field, PrimaryButton, TextInput } from "../components/ui";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await register(email, password, fullName);
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Registration failed.");
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
          <h1 className="font-display text-xl font-semibold text-ink">Create your account</h1>
          <p className="text-sm text-ink/60">Start tracking your farm's carbon footprint.</p>
        </div>

        <Card>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {error && <ErrorBanner message={error} />}
            <Field label="Full name">
              <TextInput
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Praveen Kumar"
              />
            </Field>
            <Field label="Email">
              <TextInput
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@farm.com"
              />
            </Field>
            <Field label="Password" hint="Minimum 8 characters">
              <TextInput
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </Field>
            <PrimaryButton type="submit" isLoading={isSubmitting}>
              Create account
            </PrimaryButton>
          </form>
        </Card>

        <p className="mt-4 text-center text-sm text-ink/60">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-canopy-700 hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
