import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchHealth, fetchLinkedInStatus } from "@/api";
import { Skeleton } from "@/components/ui/skeleton";
import { Link2 } from "lucide-react";

export const ConnectionCard: React.FC = () => {
  const { data: health, isLoading: isHealthLoading } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 30000,
  });

  const { data: status, isLoading: isStatusLoading } = useQuery({
    queryKey: ["linkedin-status"],
    queryFn: fetchLinkedInStatus,
    refetchInterval: 30000,
  });

  const isLoading = isHealthLoading || isStatusLoading;
  const isConnected = status?.authenticated ?? false;

  const formattedExpiry = React.useMemo(() => {
    if (!status?.expires_at || status.expires_at === "None" || status.expires_at === "null") {
      return "—";
    }
    try {
      return new Intl.DateTimeFormat(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }).format(new Date(status.expires_at));
    } catch {
      return status.expires_at;
    }
  }, [status?.expires_at]);

  const databaseType = health?.database === "postgresql" ? "PostgreSQL" : "SQLite";
  const redirectUri =
    status?.redirect_uri ||
    (typeof window !== "undefined"
      ? `${window.location.origin}/linkedin/callback`
      : "/linkedin/callback");

  return (
    <div className="bg-darkcard text-white rounded-3xl p-6 shadow-soft flex flex-col justify-between space-y-6 h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-bold text-lg tracking-tight text-white leading-tight">
            LinkedIn Connection
          </h2>
          <p className="text-xs text-neutral-400 font-normal mt-0.5">
            OAuth authorization and credentials
          </p>
        </div>

        {isLoading ? (
          <Skeleton className="h-6 w-24 bg-neutral-800" />
        ) : (
          <span
            className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${
              isConnected
                ? "bg-accent text-neutral-950 font-bold"
                : "bg-neutral-800 text-neutral-300"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full mr-1.5 ${
                isConnected ? "bg-neutral-950" : "bg-neutral-500"
              }`}
            />
            {isConnected ? "Connected" : "Not connected"}
          </span>
        )}
      </div>

      {/* Details Grid */}
      <div className="space-y-3 bg-neutral-900/80 rounded-2xl p-4 border border-neutral-800/80 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-neutral-400">Person URN</span>
          {isLoading ? (
            <Skeleton className="h-4 w-36 bg-neutral-800" />
          ) : (
            <span className="font-mono text-neutral-200 truncate max-w-[200px]" title={status?.person_urn || "—"}>
              {status?.person_urn || "—"}
            </span>
          )}
        </div>

        <div className="flex items-center justify-between">
          <span className="text-neutral-400">Token Expiry</span>
          {isLoading ? (
            <Skeleton className="h-4 w-28 bg-neutral-800" />
          ) : (
            <span className="text-neutral-200">{formattedExpiry}</span>
          )}
        </div>

        <div className="flex items-center justify-between">
          <span className="text-neutral-400">Database</span>
          {isLoading ? (
            <Skeleton className="h-4 w-20 bg-neutral-800" />
          ) : (
            <span className="text-neutral-200">{databaseType}</span>
          )}
        </div>

        <div className="flex items-center justify-between">
          <span className="text-neutral-400">Redirect URI</span>
          {isLoading ? (
            <Skeleton className="h-4 w-40 bg-neutral-800" />
          ) : (
            <span className="font-mono text-neutral-300 text-[11px] truncate max-w-[200px]" title={redirectUri}>
              {redirectUri}
            </span>
          )}
        </div>
      </div>

      {/* Action Button */}
      <div className="pt-2">
        <a
          href="/linkedin/login"
          className="inline-flex w-full items-center justify-center space-x-2 rounded-full bg-accent px-6 py-3 text-sm font-semibold text-neutral-950 shadow-sm transition-all hover:bg-accent-hover active:scale-[0.98]"
        >
          <Link2 className="w-4 h-4" />
          <span>Connect LinkedIn</span>
        </a>
      </div>
    </div>
  );
};
