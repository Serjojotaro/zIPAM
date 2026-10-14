// SPDX-License-Identifier: Apache-2.0
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/context";
import { ApiError } from "../api/client";

const schema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
});

type FormData = z.infer<typeof schema>;

export function LoginPage() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  if (user !== null) {
    navigate("/", { replace: true });
    return null;
  }

  const onSubmit = handleSubmit(async (values) => {
    try {
      await login(values.username, values.password);
      navigate("/", { replace: true });
    } catch (error) {
      if (error instanceof ApiError && error.code === "INVALID_CREDENTIALS") {
        setError("root", { message: "Invalid username or password." });
      } else {
        setError("root", { message: "Login failed. Try again later." });
      }
    }
  });

  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-950 text-zinc-100">
      <form onSubmit={onSubmit} className="w-80 space-y-4 rounded-lg border border-zinc-800 p-6">
        <h1 className="text-xl font-semibold">Sign in to zIPAM</h1>
        <div>
          <label htmlFor="username" className="block text-sm text-zinc-400">
            Username
          </label>
          <input
            id="username"
            {...register("username")}
            className="mt-1 w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-sm"
          />
          {errors.username && <p className="mt-1 text-xs text-red-400">{errors.username.message}</p>}
        </div>
        <div>
          <label htmlFor="password" className="block text-sm text-zinc-400">
            Password
          </label>
          <input
            id="password"
            type="password"
            {...register("password")}
            className="mt-1 w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-sm"
          />
          {errors.password && <p className="mt-1 text-xs text-red-400">{errors.password.message}</p>}
        </div>
        {errors.root && <p className="text-sm text-red-400">{errors.root.message}</p>}
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded bg-emerald-600 px-3 py-1.5 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
        >
          {isSubmitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </main>
  );
}
