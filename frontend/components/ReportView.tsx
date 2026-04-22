"use client";

import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { FileText, Download, CheckCircle, XCircle, Clock } from "lucide-react";
import type { Report } from "@/lib/api";

interface ReportViewProps {
  report: Report;
  onDownload?: (report: Report) => void;
}

const typeConfig = {
  SOC2: { bg: "bg-blue-500/20", text: "text-blue-400", border: "border-blue-500/50" },
  GDPR: { bg: "bg-purple-500/20", text: "text-purple-400", border: "border-purple-500/50" },
  ISO27001: { bg: "bg-green-500/20", text: "text-green-400", border: "border-green-500/50" },
};

const statusConfig = {
  pending: { icon: Clock, color: "text-slate-400" },
  generating: { icon: Clock, color: "text-amber-400" },
  completed: { icon: CheckCircle, color: "text-green-400" },
  failed: { icon: XCircle, color: "text-red-400" },
};

export function ReportView({ report, onDownload }: ReportViewProps) {
  const type = typeConfig[report.type];
  const status = statusConfig[report.status];
  const StatusIcon = status.icon;

  return (
    <Card className={`bg-slate-900 border-slate-800 ${type.border}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-3">
          <FileText className={`h-5 w-5 ${type.text}`} />
          <div>
            <CardTitle className="text-white">{report.type}</CardTitle>
            <p className="text-xs text-slate-500">
              Generated {new Date(report.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge className={type.bg + " " + type.text + " border-0"}>
            {report.type}
          </Badge>
          <Badge
            className={
              report.status === "completed"
                ? "bg-green-500/20 text-green-400 border-green-500/50"
                : report.status === "failed"
                ? "bg-red-500/20 text-red-400 border-red-500/50"
                : "bg-slate-700 text-slate-400 border-slate-600"
            }
          >
            <StatusIcon className={`h-3 w-3 mr-1 ${status.color}`} />
            {report.status.toUpperCase()}
          </Badge>
        </div>
      </CardHeader>
      {report.status === "completed" && (
        <CardContent className="flex justify-end">
          <Button
            size="sm"
            variant="outline"
            className="border-slate-700 text-slate-300 hover:bg-slate-800"
            onClick={() => onDownload?.(report)}
          >
            <Download className="h-4 w-4 mr-2" />
            Download PDF
          </Button>
        </CardContent>
      )}
    </Card>
  );
}