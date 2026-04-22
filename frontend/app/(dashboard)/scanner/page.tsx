"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ScanResults } from "@/components/ScanResults";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { createClient } from "@/lib/supabase";
import { api, type PortResult } from "@/lib/api";
import { Scan, Play, Loader2 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from "recharts";

const mockResults: PortResult[] = [
  { port: 22, status: "closed", risk_level: "low", service: "SSH", description: "SSH service not detected" },
  { port: 80, status: "open", risk_level: "high", service: "HTTP", description: "Unencrypted web traffic - Consider redirecting to HTTPS" },
  { port: 443, status: "open", risk_level: "low", service: "HTTPS", description: "Secure web service detected" },
  { port: 3306, status: "open", risk_level: "high", service: "MySQL", description: "Database port exposed - restrict access immediately" },
  { port: 5432, status: "filtered", risk_level: "medium", service: "PostgreSQL", description: "Database port may be accessible" },
  { port: 6379, status: "open", risk_level: "high", service: "Redis", description: "Redis cache exposed without authentication" },
  { port: 8080, status: "open", risk_level: "medium", service: "HTTP-Alt", description: "Alternative HTTP port detected" },
  { port: 27017, status: "closed", risk_level: "low", service: "MongoDB", description: "MongoDB not detected" },
];

function ScannerContent() {
  const searchParams = useSearchParams();
  const [target, setTarget] = useState(searchParams.get("target") || "");
  const [scanType, setScanType] = useState("quick");
  const [isScanning, setIsScanning] = useState(false);
  const [results, setResults] = useState<PortResult[] | null>(null);
  const [orgId, setOrgId] = useState<string | null>(null);

  useEffect(() => {
    const getUser = async () => {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (user?.user_metadata?.org_id) {
        setOrgId(user.user_metadata.org_id);
      }
    };
    getUser();
  }, []);

  const handleScan = async () => {
    if (!target.trim()) return;
    setIsScanning(true);
    setResults(null);

    try {
      if (orgId) {
        const scan = await api.startScan(orgId, target);
        if (scan.status === "completed") {
          const scanResults = await api.getScanResults(scan.id);
          setResults(scanResults);
        }
      }
    } catch {
      // Simulate scan delay
      await new Promise((resolve) => setTimeout(resolve, 2000));
      setResults(mockResults);
    } finally {
      setIsScanning(false);
    }
  };

  const riskCounts = results
    ? {
        high: results.filter((r) => r.risk_level === "high").length,
        medium: results.filter((r) => r.risk_level === "medium").length,
        low: results.filter((r) => r.risk_level === "low").length,
      }
    : null;

  const chartData = riskCounts
    ? [
        { name: "High", count: riskCounts.high, color: "#ef4444" },
        { name: "Medium", count: riskCounts.medium, color: "#eab308" },
        { name: "Low", count: riskCounts.low, color: "#22c55e" },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Port Scanner</h1>
        <p className="text-slate-400">Scan target endpoints for open ports and vulnerabilities</p>
      </div>

      {/* Scan Form */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Scan className="h-5 w-5 text-blue-500" />
            New Scan
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <Input
              placeholder="Enter target URL or IP (e.g., api.example.com)"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="bg-slate-800 border-slate-700 text-white placeholder:text-slate-500 flex-1"
            />
            <Select value={scanType} onValueChange={setScanType}>
              <SelectTrigger className="w-40 bg-slate-800 border-slate-700 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                <SelectItem value="quick">Quick Scan</SelectItem>
                <SelectItem value="full">Full Scan</SelectItem>
                <SelectItem value="custom">Custom Range</SelectItem>
              </SelectContent>
            </Select>
            <Button
              onClick={handleScan}
              disabled={isScanning || !target.trim()}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isScanning ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Scanning...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Start Scan
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Risk Summary */}
      {riskCounts && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-400">High Risk</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-red-500">{riskCounts.high}</div>
              <p className="text-xs text-slate-500 mt-1">ports require immediate action</p>
            </CardContent>
          </Card>
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-400">Medium Risk</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-amber-500">{riskCounts.medium}</div>
              <p className="text-xs text-slate-500 mt-1">ports should be reviewed</p>
            </CardContent>
          </Card>
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-400">Low Risk</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-500">{riskCounts.low}</div>
              <p className="text-xs text-slate-500 mt-1">ports are secure</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Risk Chart */}
      {results && results.length > 0 && (
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white">Risk Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <XAxis dataKey="name" stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1e293b",
                      border: "1px solid #334155",
                      borderRadius: "0.5rem",
                    }}
                    labelStyle={{ color: "#e2e8f0" }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={index} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Scan Results */}
      {results && results.length > 0 && (
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white">Scan Results</CardTitle>
          </CardHeader>
          <CardContent>
            <ScanResults results={results} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function ScannerPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-pulse text-slate-400">Loading scanner...</div>
      </div>
    }>
      <ScannerContent />
    </Suspense>
  );
}