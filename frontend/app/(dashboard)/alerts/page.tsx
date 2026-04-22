"use client";

import { useState, useEffect } from "react";
import { AlertCard } from "@/components/AlertCard";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Modal, ModalContent, ModalHeader, ModalTitle, ModalDescription, ModalClose, ModalFooter } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { createClient } from "@/lib/supabase";
import { api, type Alert } from "@/lib/api";
import { Shield, Filter } from "lucide-react";

const mockAlerts: Alert[] = [
  { id: "1", org_id: "1", severity: "critical", type: "Injection", title: "SQL Injection Attempt", description: "SQL injection pattern detected in request to /api/users", status: "open", remediation_hint: "Validate and sanitize all user inputs. Use parameterized queries.", created_at: new Date().toISOString() },
  { id: "2", org_id: "1", severity: "high", type: "Rate Limit", title: "Rate Limit Exceeded", description: "Exceeded 1000 requests/minute threshold", status: "open", remediation_hint: "Implement rate limiting middleware.", created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: "3", org_id: "1", severity: "high", type: "Auth", title: "Failed Login Attempts", description: "Multiple failed login attempts detected", status: "open", remediation_hint: "Consider implementing account lockout.", created_at: new Date(Date.now() - 7200000).toISOString() },
  { id: "4", org_id: "1", severity: "medium", type: "Health", title: "High Latency Detected", description: "Response time exceeded 500ms threshold", status: "open", created_at: new Date(Date.now() - 10800000).toISOString() },
  { id: "5", org_id: "1", severity: "medium", type: "CORS", title: "CORS Violation", description: "Cross-origin request blocked", status: "open", created_at: new Date(Date.now() - 14400000).toISOString() },
  { id: "6", org_id: "1", severity: "low", type: "Info", title: "Unusual Request Pattern", description: "Request pattern differs from baseline", status: "open", created_at: new Date(Date.now() - 18000000).toISOString() },
  { id: "7", org_id: "1", severity: "low", type: "Health", title: "Slow Response Time", description: "Response time > 300ms", status: "resolved", resolved_at: new Date(Date.now() - 900000).toISOString(), created_at: new Date(Date.now() - 21600000).toISOString() },
];

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [activeTab, setActiveTab] = useState("all");

  useEffect(() => {
    const getUser = async () => {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (user?.user_metadata?.org_id) {
        try {
          const data = await api.getAlerts(user.user_metadata.org_id);
          if (data.length > 0) setAlerts(data);
        } catch {
          // Use mock data
        }
      }
    };
    getUser();
  }, []);

  const handleResolve = async (id: string) => {
    try {
      const updated = await api.resolveAlert(id);
      setAlerts((prev) => prev.map((a) => (a.id === id ? updated : a)));
    } catch {
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === id ? { ...a, status: "resolved" as const, resolved_at: new Date().toISOString() } : a
        )
      );
    }
    setSelectedAlert(null);
  };

  const filteredAlerts = alerts.filter((alert) => {
    if (activeTab === "all") return true;
    if (activeTab === "resolved") return alert.status === "resolved";
    return alert.severity === activeTab;
  });

  const counts = {
    all: alerts.filter(a => a.status === "open").length,
    critical: alerts.filter(a => a.severity === "critical" && a.status === "open").length,
    high: alerts.filter(a => a.severity === "high" && a.status === "open").length,
    medium: alerts.filter(a => a.severity === "medium" && a.status === "open").length,
    low: alerts.filter(a => a.severity === "low" && a.status === "open").length,
    resolved: alerts.filter(a => a.status === "resolved").length,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Alerts</h1>
          <p className="text-slate-400">Monitor and manage security alerts</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-slate-900 border border-slate-800">
          <TabsTrigger value="all" className="data-[state=active]:bg-slate-800">
            All ({counts.all})
          </TabsTrigger>
          <TabsTrigger value="critical" className="data-[state=active]:bg-red-500/20 data-[state=active]:text-red-400">
            Critical ({counts.critical})
          </TabsTrigger>
          <TabsTrigger value="high" className="data-[state=active]:bg-orange-500/20 data-[state=active]:text-orange-400">
            High ({counts.high})
          </TabsTrigger>
          <TabsTrigger value="medium" className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400">
            Medium ({counts.medium})
          </TabsTrigger>
          <TabsTrigger value="low" className="data-[state=active]:bg-blue-500/20 data-[state=active]:text-blue-400">
            Low ({counts.low})
          </TabsTrigger>
          <TabsTrigger value="resolved" className="data-[state=active]:bg-green-500/20 data-[state=active]:text-green-400">
            Resolved ({counts.resolved})
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-4">
          {filteredAlerts.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <Shield className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No alerts in this category</p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredAlerts.map((alert) => (
                <AlertCard
                  key={alert.id}
                  alert={alert}
                  onResolve={handleResolve}
                  onClick={setSelectedAlert}
                />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Alert Detail Modal */}
      <Modal open={!!selectedAlert} onOpenChange={() => setSelectedAlert(null)}>
        <ModalContent className="bg-slate-900 border-slate-800 max-w-2xl">
          <ModalHeader>
            <div className="flex items-center gap-3">
              <ModalTitle className="text-white">{selectedAlert?.title}</ModalTitle>
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                selectedAlert?.severity === "critical" ? "bg-red-500 text-white" :
                selectedAlert?.severity === "high" ? "bg-orange-500 text-white" :
                selectedAlert?.severity === "medium" ? "bg-amber-500 text-black" :
                "bg-blue-500 text-white"
              }`}>
                {selectedAlert?.severity?.toUpperCase()}
              </span>
            </div>
            <ModalDescription className="text-slate-400">
              {selectedAlert && new Date(selectedAlert.created_at).toLocaleString()}
            </ModalDescription>
          </ModalHeader>
          
          {selectedAlert && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-slate-500 mb-1">Type</p>
                  <p className="text-white">{selectedAlert.type}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Status</p>
                  <p className={selectedAlert.status === "resolved" ? "text-green-400" : "text-amber-400"}>
                    {selectedAlert.status.toUpperCase()}
                  </p>
                </div>
              </div>
              
              <div>
                <p className="text-xs text-slate-500 mb-1">Description</p>
                <p className="text-slate-300">{selectedAlert.description}</p>
              </div>
              
              {selectedAlert.remediation_hint && (
                <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-md">
                  <p className="text-xs text-amber-400 mb-1 font-medium">Remediation Hint</p>
                  <p className="text-sm text-amber-200">{selectedAlert.remediation_hint}</p>
                </div>
              )}

              {selectedAlert.resolved_at && (
                <div>
                  <p className="text-xs text-slate-500 mb-1">Resolved At</p>
                  <p className="text-green-400">{new Date(selectedAlert.resolved_at).toLocaleString()}</p>
                </div>
              )}
            </div>
          )}

          <ModalFooter>
            {selectedAlert?.status === "open" && (
              <Button
                onClick={() => selectedAlert && handleResolve(selectedAlert.id)}
                className="bg-green-600 hover:bg-green-700"
              >
                Resolve Alert
              </Button>
            )}
            <ModalClose asChild>
              <Button variant="outline" className="border-slate-700 text-slate-300">
                Close
              </Button>
            </ModalClose>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
}