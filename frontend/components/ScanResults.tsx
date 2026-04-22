"use client";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { Badge } from "./ui/badge";
import type { PortResult } from "@/lib/api";

interface ScanResultsProps {
  results: PortResult[];
}

const riskConfig = {
  high: { color: "bg-red-500", text: "text-red-400" },
  medium: { color: "bg-amber-500", text: "text-amber-400" },
  low: { color: "bg-green-500", text: "text-green-400" },
};

export function ScanResults({ results }: ScanResultsProps) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-900">
      <Table>
        <TableHeader>
          <TableRow className="border-slate-800 hover:bg-transparent">
            <TableHead className="text-slate-400">Port</TableHead>
            <TableHead className="text-slate-400">Status</TableHead>
            <TableHead className="text-slate-400">Risk</TableHead>
            <TableHead className="text-slate-400">Service</TableHead>
            <TableHead className="text-slate-400">Description</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {results.map((result) => {
            const risk = riskConfig[result.risk_level];
            return (
              <TableRow key={result.port} className="border-slate-800">
                <TableCell className="text-white font-mono">{result.port}</TableCell>
                <TableCell>
                  <Badge
                    className={
                      result.status === "open"
                        ? "bg-green-500/20 text-green-400 border-green-500/50"
                        : result.status === "filtered"
                        ? "bg-amber-500/20 text-amber-400 border-amber-500/50"
                        : "bg-slate-700 text-slate-400 border-slate-600"
                    }
                  >
                    {result.status.toUpperCase()}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge className={`${risk.color} text-white border-0`}>
                    {result.risk_level.toUpperCase()}
                  </Badge>
                </TableCell>
                <TableCell className="text-slate-400">{result.service || "—"}</TableCell>
                <TableCell className="text-slate-400">{result.description}</TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}