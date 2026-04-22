"use client";

import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { createClient } from "@/lib/supabase";
import { api, type Org } from "@/lib/api";
import { Copy, Check, Key, Mail, Webhook, CreditCard, Plus, Trash2 } from "lucide-react";

const mockOrg: Org = {
  id: "1",
  name: "Acme Corp",
  plan: "pro",
  api_key: "sk_live_xxxxxxxxxxxxxx_xxxxxxxx",
  endpoints: [
    { id: "1", url: "https://api.acme.com", name: "Production API", status: "connected", last_seen: new Date().toISOString() },
    { id: "2", url: "https://staging.acme.com", name: "Staging API", status: "connected", last_seen: new Date(Date.now() - 300000).toISOString() },
    { id: "3", url: "https://dev.acme.com", name: "Dev API", status: "disconnected", last_seen: new Date(Date.now() - 3600000).toISOString() },
  ],
  notification_channels: [
    { id: "1", type: "email", value: "security@acme.com", enabled: true },
    { id: "2", type: "slack", value: "https://hooks.slack.com/services/xxx", enabled: true },
  ],
};

export default function SettingsPage() {
  const [org, setOrg] = useState<Org | null>(null);
  const [email, setEmail] = useState("");
  const [slackUrl, setSlackUrl] = useState("");
  const [copied, setCopied] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const getOrg = async () => {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (user?.user_metadata?.org_id) {
        try {
          const data = await api.getOrg(user.user_metadata.org_id);
          setOrg(data);
          const emailChannel = data.notification_channels?.find((c) => c.type === "email");
          const slackChannel = data.notification_channels?.find((c) => c.type === "slack");
          setEmail(emailChannel?.value || "");
          setSlackUrl(slackChannel?.value || "");
        } catch {
          setOrg(mockOrg);
          setEmail(mockOrg.notification_channels[0].value);
          setSlackUrl(mockOrg.notification_channels[1].value);
        }
      } else {
        setOrg(mockOrg);
        setEmail(mockOrg.notification_channels[0].value);
        setSlackUrl(mockOrg.notification_channels[1].value);
      }
    };
    getOrg();
  }, []);

  const handleCopyApiKey = () => {
    if (org?.api_key) {
      navigator.clipboard.writeText(org.api_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleSaveNotifications = async () => {
    setSaving(true);
    // Simulate save
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setSaving(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-slate-400">Manage your organization settings</p>
      </div>

      {/* API Key */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Key className="h-5 w-5 text-blue-500" />
            API Key
          </CardTitle>
          <CardDescription className="text-slate-500">
            Use this key to authenticate with the SentinelAPI
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <Input
              value={org?.api_key || ""}
              readOnly
              className="bg-slate-800 border-slate-700 text-slate-400 font-mono"
            />
            <Button
              variant="outline"
              size="icon"
              onClick={handleCopyApiKey}
              className="border-slate-700 text-slate-300 hover:bg-slate-800"
            >
              {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Endpoints */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-white">Monitored Endpoints</CardTitle>
            <CardDescription className="text-slate-500">
              API endpoints being monitored for threats
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" className="border-slate-700 text-slate-300 hover:bg-slate-800">
            <Plus className="h-4 w-4 mr-2" />
            Add Endpoint
          </Button>
        </CardHeader>
        <CardContent>
          {org?.endpoints && org.endpoints.length > 0 ? (
            <div className="space-y-2">
              {org.endpoints.map((endpoint) => (
                <div
                  key={endpoint.id}
                  className="flex items-center justify-between p-3 bg-slate-800/50 rounded-md border border-slate-800"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${endpoint.status === "connected" ? "bg-green-500" : "bg-slate-600"}`} />
                    <div>
                      <p className="text-white font-medium">{endpoint.name}</p>
                      <p className="text-sm text-slate-500 font-mono">{endpoint.url}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={endpoint.status === "connected" ? "bg-green-500/20 text-green-400 border-green-500/50" : "bg-slate-700 text-slate-400 border-slate-600"}>
                      {endpoint.status}
                    </Badge>
                    <Button variant="ghost" size="icon" className="text-slate-400 hover:text-red-400">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-500 text-center py-8">No endpoints configured</p>
          )}
        </CardContent>
      </Card>

      {/* Notification Channels */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Mail className="h-5 w-5 text-purple-500" />
            Notification Channels
          </CardTitle>
          <CardDescription className="text-slate-500">
            Configure where to receive security alerts
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm text-slate-400 mb-2 block">Email Address</label>
            <Input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="security@yourcompany.com"
              className="bg-slate-800 border-slate-700 text-white"
            />
          </div>
          <div>
            <label className="text-sm text-slate-400 mb-2 block flex items-center gap-2">
              <Webhook className="h-4 w-4" />
              Slack Webhook URL
            </label>
            <Input
              value={slackUrl}
              onChange={(e) => setSlackUrl(e.target.value)}
              placeholder="https://hooks.slack.com/services/..."
              className="bg-slate-800 border-slate-700 text-white"
            />
          </div>
          <Button
            onClick={handleSaveNotifications}
            disabled={saving}
            className="bg-purple-600 hover:bg-purple-700"
          >
            {saving ? "Saving..." : "Save Notifications"}
          </Button>
        </CardContent>
      </Card>

      {/* Plan & Billing */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-green-500" />
            Plan & Billing
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-md border border-slate-800">
            <div>
              <p className="text-white font-medium capitalize">{org?.plan || "pro"} Plan</p>
              <p className="text-sm text-slate-500">$99/month • Renews on Dec 1, 2026</p>
            </div>
            <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800">
              Manage Subscription
            </Button>
          </div>
          <div className="mt-4 grid grid-cols-3 gap-4 text-center">
            <div className="p-3 bg-slate-800/30 rounded-md">
              <p className="text-2xl font-bold text-white">5</p>
              <p className="text-xs text-slate-500">Endpoints</p>
            </div>
            <div className="p-3 bg-slate-800/30 rounded-md">
              <p className="text-2xl font-bold text-white">10K</p>
              <p className="text-xs text-slate-500">API Calls/mo</p>
            </div>
            <div className="p-3 bg-slate-800/30 rounded-md">
              <p className="text-2xl font-bold text-white">3</p>
              <p className="text-xs text-slate-500">Users</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}