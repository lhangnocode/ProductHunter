import React, { useMemo, useState } from "react";
import { Lock, Loader2, ArrowLeft } from "lucide-react";
import { authService } from "../services/auth";
import { useToast } from "./Toast";

export function ResetPasswordPage() {
  const { showToast } = useToast();
  const token = useMemo(
    () => new URLSearchParams(window.location.search).get("token") || "",
    [],
  );
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      showToast("Reset token is missing", "error");
      return;
    }
    if (!password || !confirmPassword) {
      showToast("Please fill in all fields", "error");
      return;
    }
    if (password !== confirmPassword) {
      showToast("Passwords do not match", "error");
      return;
    }

    setIsSubmitting(true);
    try {
      await authService.resetPassword(token, password);
      setIsSuccess(true);
      showToast("Password reset successful", "success");
    } catch (error: any) {
      showToast(error.message || "Failed to reset password", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-sm">
        <button
          type="button"
          onClick={() => {
            window.location.href = "/";
          }}
          className="mb-5 inline-flex items-center gap-2 text-sm font-semibold text-slate-600 dark:text-slate-300 hover:text-brand-primary"
        >
          <ArrowLeft size={16} />
          Back to home
        </button>

        <h1 className="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tight">
          Reset Password
        </h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Enter your new password to complete the reset process.
        </p>

        {!token && (
          <p className="mt-4 text-sm text-rose-600 dark:text-rose-400">
            Invalid reset link: token is missing.
          </p>
        )}

        {!isSuccess ? (
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-bold uppercase tracking-wide text-slate-600 dark:text-slate-300">
                New password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isSubmitting || !token}
                  className="w-full rounded-xl bg-slate-50 dark:bg-slate-950/50 py-3 pl-10 pr-3 text-sm ring-1 ring-inset ring-slate-200 dark:ring-slate-700 focus:ring-2 focus:ring-brand-primary outline-none"
                  placeholder="Enter new password"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold uppercase tracking-wide text-slate-600 dark:text-slate-300">
                Confirm password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={isSubmitting || !token}
                  className="w-full rounded-xl bg-slate-50 dark:bg-slate-950/50 py-3 pl-10 pr-3 text-sm ring-1 ring-inset ring-slate-200 dark:ring-slate-700 focus:ring-2 focus:ring-brand-primary outline-none"
                  placeholder="Re-enter new password"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !token}
              className="w-full rounded-xl bg-brand-primary py-3 text-sm font-black uppercase tracking-wider text-white hover:bg-brand-secondary disabled:opacity-60"
            >
              {isSubmitting ? (
                <span className="inline-flex items-center gap-2">
                  <Loader2 size={14} className="animate-spin" />
                  Processing...
                </span>
              ) : (
                "Reset password"
              )}
            </button>
          </form>
        ) : (
          <div className="mt-6 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 p-4 text-sm text-emerald-800 dark:text-emerald-200">
            Password has been reset successfully. You can now go back and log in with your new password.
          </div>
        )}
      </div>
    </div>
  );
}
