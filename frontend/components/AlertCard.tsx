"use client";

import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Alert, AlertTriangle, Info, AlertCircle } from "lucide-react";
import type { Alert as AlertType } from "@/lib/api";

interface AlertCardProps {
  alert: AlertType;
  onResolve?: (id: string) => void;
  onClick?: (alert: AlertType) => void;
  expanded?: boolean;
}

const severityConfig = {
  critical: {
    color: "bg-red-500",
    textColor: "text-red-400",
    borderColor: "border-red-500/50",
    bgHover: "hover:bg-red-500/10",
    icon: AlertTriangle,
  },
  high: {
    color: "bg-orange-500",
    textColor: "text-orange-400",
    borderColor: "border-orange-500/50",
    bgHover: "hover:bg-orange-500/10",
    icon: AlertCircle,
  },
  medium: {
    color: "bg-amber-500",
    textColor: "text-amber-400",
    borderColor: "border-amber-500/50",
    bgHover: "hover:bg-amber-500/10",
    icon: Alert,
  },
  low: {
    color: "bg-blue-500",
    textColor: "text-blue-400",
    borderColor: "border-blue-500/50",
    bgHover: "hover:bg-blue-500/10",
    icon: Info,
  },
};

export function AlertCard({ alert, onResolve, onClick, expanded = false }: AlertCardProps) {
  const config = severityConfig[alert.severity];
  const SeverityIcon = config.icon;

  return (
    <Card
      className={`bg-slate-900 border-slate-800 ${config.bgHover} transition-colors cursor-pointer ${config.borderColor}`}
      onClick={() => onClick?.(alert)}
    >
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          <SeverityIcon className={`h-4 w-4 ${config.textColor}`} />
          <CardTitle className="text-sm font-medium text-white">
            {alert.title}
          </CardTitle>
        </div>
        <Badge
          className={`${config.color} text-white border-0`}
        >
          {alert.severity.toUpperCase()}
        </Badge>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-slate-400 mb-2">{alert.description}</p>
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">
            {new Date(alert.created_at).toLocaleString()}
          </span>
          {alert.status === "open" && onResolve && (
            <Button
              size="sm"
              variant="outline"
              className="h-7 text-xs border-slate-700 text-slate-300 hover:bg-slate-800"
              onClick={(e) => {
                e.stopPropagation();
                onResolve(alert.id);
              }}
            >
              Resolve
            </Button>
          )}
        </div>
        {expanded && alert.remediation_hint && (
          <div className="mt-3 p-3 bg-slate-800/50 rounded-md">
            <p className="text-xs font-medium text-slate-300 mb-1">Remediation</p>
            <p className="text-xs text-slate-400">{alert.remediation_hint}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}