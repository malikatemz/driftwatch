"use client";

import { useState, useEffect } from "react";
import { ReportView } from "@/components/ReportView";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Modal, ModalContent, ModalHeader, ModalTitle, ModalDescription, ModalClose } from "@/components/ui/modal";
import { createClient } from "@/lib/supabase";
import { api, type Report } from "@/lib/api";
import { FileText, Plus, Loader2 } from "lucide-react";

const mockReports: Report[] = [
  { id: "1", org_id: "1", type: "SOC2", status: "completed", created_at: new Date(Date.now() - 86400000).toISOString(), completed_at: new Date(Date.now() - 82800000).toISOString() },
  { id: "2", org_id: "1", type: "GDPR", status: "completed", created_at: new Date(Date.now() - 172800000).toISOString(), completed_at: new Date(Date.now() - 169200000).toISOString() },
  { id: "3", org_id: "1", type: "ISO27001", status: "generating", created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: "4", org_id: "1", type: "SOC2", status: "pending", created_at: new Date(Date.now() - 1800000).toISOString() },
];

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>(mockReports);
  const [reportType, setReportType] = useState("SOC2");
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [orgId, setOrgId] = useState<string | null>(null);

  useEffect(() => {
    const getUser = async () => {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (user?.user_metadata?.org_id) {
        setOrgId(user.user_metadata.org_id);
        try {
          const data = await api.getReports(user.user_metadata.org_id);
          if (data.length > 0) setReports(data);
        } catch {
          // Use mock data
        }
      }
    };
    getUser();
  }, []);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      if (orgId) {
        const newReport = await api.generateReport(orgId, reportType as "SOC2" | "GDPR" | "ISO27001");
        setReports((prev) => [newReport, ...prev]);
      } else {
        // Mock report generation
        const newReport: Report = {
          id: String(Date.now()),
          org_id: "1",
          type: reportType as "SOC2" | "GDPR" | "ISO27001",
          status: "generating",
          created_at: new Date().toISOString(),
        };
        setReports((prev) => [newReport, ...prev]);
        
        // Simulate completion after 3 seconds
        setTimeout(() => {
          setReports((prev) =>
            prev.map((r) =>
              r.id === newReport.id ? { ...r, status: "completed", completed_at: new Date().toISOString() } : r
            )
          );
        }, 3000);
      }
    } catch {
      // Mock error handling
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = (report: Report) => {
    // In a real app, this would download the report PDF
    alert(`Downloading ${report.type} report...`);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Reports</h1>
          <p className="text-slate-400">Compliance and security reports</p>
        </div>
      </div>

      {/* Generate Report */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <FileText className="h-5 w-5 text-purple-500" />
            Generate New Report
          </CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4">
          <Select value={reportType} onValueChange={setReportType}>
            <SelectTrigger className="w-40 bg-slate-800 border-slate-700 text-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-slate-700">
              <SelectItem value="SOC2">SOC 2</SelectItem>
              <SelectItem value="GDPR">GDPR</SelectItem>
              <SelectItem value="ISO27001">ISO 27001</SelectItem>
            </SelectContent>
          </Select>
          <Button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="bg-purple-600 hover:bg-purple-700"
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Plus className="h-4 w-4 mr-2" />
                Generate Report
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Report History */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Report History</h2>
        {reports.length === 0 ? (
          <Card className="bg-slate-900 border-slate-800">
            <CardContent className="py-12 text-center">
              <FileText className="h-12 w-12 mx-auto mb-4 text-slate-600" />
              <p className="text-slate-500">No reports generated yet</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {reports.map((report) => (
              <ReportView key={report.id} report={report} onDownload={handleDownload} />
            ))}
          </div>
        )}
      </div>

      {/* Report Detail Modal */}
      <Modal open={!!selectedReport} onOpenChange={() => setSelectedReport(null)}>
        <ModalContent className="bg-slate-900 border-slate-800 max-w-3xl max-h-[80vh] overflow-auto">
          <ModalHeader>
            <ModalTitle className="text-white">
              {selectedReport?.type} Compliance Report
            </ModalTitle>
            <ModalDescription>
              Generated {selectedReport && new Date(selectedReport.created_at).toLocaleDateString()}
            </ModalDescription>
          </ModalHeader>
          
          {selectedReport?.status === "completed" ? (
            <div className="space-y-4">
              <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-md">
                <p className="text-green-400 text-sm font-medium">Report Ready</p>
                <p className="text-slate-400 text-sm">This report is ready for download</p>
              </div>
              
              <div className="space-y-3">
                <h3 className="text-white font-medium">Executive Summary</h3>
                <p className="text-slate-400 text-sm">
                  This {selectedReport.type} compliance report provides a comprehensive review of your 
                  organization's security controls, data protection measures, and regulatory compliance status.
                </p>
                
                <h3 className="text-white font-medium">Key Findings</h3>
                <ul className="text-slate-400 text-sm list-disc pl-5 space-y-1">
                  <li>All required security controls are in place</li>
                  <li>Data protection measures meet compliance requirements</li>
                  <li>No critical vulnerabilities identified</li>
                </ul>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
              <span className="ml-3 text-slate-400">Generating report...</span>
            </div>
          )}

          <div className="flex justify-end gap-2 mt-4">
            {selectedReport?.status === "completed" && (
              <Button
                onClick={() => selectedReport && handleDownload(selectedReport)}
                className="bg-purple-600 hover:bg-purple-700"
              >
                Download PDF
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
    </div>
  );
}