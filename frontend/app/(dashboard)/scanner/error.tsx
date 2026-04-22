"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-6">
      <div className="text-red-500 text-4xl mb-4">⚠</div>
      <h1 className="text-xl font-semibold text-white mb-2">Scanner error</h1>
      <p className="text-slate-400 mb-4">{error.message || "An unexpected error occurred"}</p>
      <button
        onClick={reset}
        className="px-4 py-2 bg-slate-800 text-white rounded-md hover:bg-slate-700 transition-colors"
      >
        Try again
      </button>
    </div>
  );
}