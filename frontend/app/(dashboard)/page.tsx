"use client";

import { useState, useEffect } from "react";
import { DashboardStats } from "@/components/DashboardStats";
import { AlertCard } from "@/components/AlertCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Modal, ModalContent, ModalHeader, ModalTitle, ModalDescription, ModalClose } from "@/components/ui/modal";
import { createClient } from "@/lib/supabase";
import { api, type Alert } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";
import { Scan, AlertTriangle, Activity, ShieldCheck } from "lucide-react";

const mockStats = [
  { title: "Active Threats", value: 12, change: "+2 from yesterday", changeType: "negative" as const, icon: "threats" as const },
  { title: "Alerts This Week", value: 47, change: "-12% from last week", changeType: "positive" as const, icon: "alerts" as const },
  { title: "Monitored Endpoints", value: 156, change: "+3 new", changeType: "neutral" as const, icon: "endpoints" as const },
  { title: "Compliance Score", value: "94%", change: "+2%", changeType: "positive" as const, icon: "compliance" as const },
];

const mockAlerts: Alert[] = [
  { id: "1", org_id: "1", severity: "critical", type: "Injection", title: "SQL Injection Attempt", description: "SQL injection pattern detected in request to /api/users", status: "open", remediation_hint: "Validate and sanitize all user inputs. Use parameterized queries.", created_at: new Date().toISOString() },
  { id: "2", org_id: "1", severity: "high", type: "Rate Limit", title: "Rate Limit Exceeded", description: "Exceeded 1000 requests/minute threshold", status: "open", remediation_hint: "Implement rate limiting middleware.", created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: "3", org_id: "1", severity: "medium", type: "Auth", title: "Failed Login Attempts", description: "5 failed login attempts from IP 192.168.1.45", status: "open", remediation_hint: "Consider implementing account lockout.", created_at: new Date(Date.now() - 7200000).toISOString() },
  { id: "4", org_id: "1", severity: "low", type: "Health", title: "High Latency Detected", description: "Response time exceeded 500ms threshold", status: "open", created_at: new Date(Date.now() - 10800000).toISOString() },
];

const mockTimeline = [
  { time: "00:00", critical: 1, high: 2, medium: 5 },
  { time: "04:00", critical: 0, high: 1, medium: 3 },
  { time: "08:00", critical: 2, high: 3, medium: 7 },
  { time: "12:00", critical: 1, high: 4, medium: 6 },
  { time: "16:00", critical: 3, high: 5, medium: 8 },
  { time: "20:00", critical: 1, high: 2, medium: 4 },
];

export default function DashboardPage() {
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts);
  const [scanTarget, setScanTarget] = useState("");
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [orgId, setOrgId] = useState<string | null>(null);

  useEffect(() => {
    const getUser = async () => {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        const orgIdFromMeta = user.user_metadata?.org_id;
        if (orgIdFromMeta) {
          setOrgId(orgIdFromMeta);
          try {
            const data = await api.getAlerts(orgIdFromMeta);
            if (data.length > 0) setAlerts(data);
          } catch {
            // Use mock data if API not available
          }
        }
      }
    };
    getUser();
  }, []);

  const handleResolve = async (id: string) => {
    try {
      const updated = await api.resolveAlert(id);
      setAlerts((prev) =>
        prev.map((a) => (a.id === id ? updated : a))
      );
    } catch {
      // Fallback to optimistic update
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === id ? { ...a, status: "resolved" as const, resolved_at: new Date().toISOString() } : a
        )
      );
    }
  };

  const handleScan = () => {
    if (!scanTarget.trim()) return;
    window.location.href = `/scanner?target=${encodeURIComponent(scanTarget)}`;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-slate-400">Overview of your API security status</p>
      </div>

      {/* Stats */}
      <DashboardStats stats={mockStats} />

      {/* Quick Scan */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Scan className="h-5 w-5 text-blue-500" />
            Quick Scan
          </CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4">
          <Input
            placeholder="Enter URL or IP address (e.g., api.example.com)"
            value={scanTarget}
            onChange={(e) => setScanTarget(e.target.value)}
            className="bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
          />
          <Button
            onClick={handleScan}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            Run Scan
          </Button>
        </CardContent>
      </Card>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Alerts */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Recent Alerts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {alerts.filter(a => a.status === "open").slice(0, 4).map((alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onResolve={handleResolve}
                onClick={setSelectedAlert}
              />
            ))}
          </CardContent>
        </Card>

        {/* Threat Timeline */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Activity className="h-5 w-5 text-green-500" />
              Threat Timeline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={mockTimeline}>
                  <XAxis dataKey="time" stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1e293b",
                      border: "1px solid #334155",
                      borderRadius: "0.5rem",
                    }}
                    labelStyle={{ color: "#e2e8f0" }}
                  />
                  <Bar dataKey="critical" fill="#ef4444" name="Critical" />
                  <Bar dataKey="high" fill="#f97316" name="High" />
                  <Bar dataKey="medium" fill="#eab308" name="Medium" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alert Detail Modal */}
      {selectedAlert && (
        <Modal open={!!selectedAlert} onOpenChange={() => setSelectedAlert(null)}>
          <ModalContent className="bg-slate-900 border-slate-800">
            <ModalHeader>
              <div className="flex items-center justify-between">
                <ModalTitle className="text-white">{selectedAlert.title}</ModalTitle>
              </div>
              <ModalDescription className="text-slate-400">
                {new Date(selectedAlert.created_at).toLocaleString()}
              </ModalDescription>
            </ModalHeader>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-slate-300 mb-1">Description</p>
                <p className="text-white">{selectedAlert.description}</p>
              </div>
              <div>
                <p className="text-sm text-slate-300 mb-1">Type</p>
                <p className="text-white">{selectedAlert.type}</p>
              </div>
              {selectedAlert.remediation_hint && (
                <div>
                  <p className="text-sm text-slate-300 mb-1">Remediation Hint</p>
                  <p className="text-amber-400 text-sm">{selectedAlert.remediation_hint}</p>
                </div>
              )}
            </div>
            <div className="flex justify-end gap-2 mt-4">
              {selectedAlert.status === "open" && (
                <Button
                  onClick={() => {
                    handleResolve(selectedAlert.id);
                    setSelectedAlert(null);
                  }}
                  className="bg-green-600 hover:bg-green-700"
                >
                  Mark Resolved
                </Button>
              )}
              <ModalClose asChild>
                <Button variant="outline" className="border-slate-700 text-slate-300">
                  Close
                </Button>
              </ModalClose>
            </div>
          </ModalContent>
        </Modal>
      )}
    </div>
  );
}