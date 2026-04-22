"use client";

import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Shield, AlertTriangle, Activity, CheckCircle } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  icon: "threats" | "alerts" | "endpoints" | "compliance";
}

const icons = {
  threats: AlertTriangle,
  alerts: Shield,
  endpoints: Activity,
  compliance: CheckCircle,
};

const iconColors = {
  threats: "text-red-500",
  alerts: "text-amber-500",
  endpoints: "text-blue-500",
  compliance: "text-green-500",
};

export function DashboardStats({ stats }: { stats: StatCardProps[] }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => {
        const Icon = icons[stat.icon];
        return (
          <Card key={stat.title} className="bg-slate-900 border-slate-800">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-400">
                {stat.title}
              </CardTitle>
              <Icon className={`h-4 w-4 ${iconColors[stat.icon]}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{stat.value}</div>
              {stat.change && (
                <p
                  className={`text-xs ${
                    stat.changeType === "positive"
                      ? "text-green-500"
                      : stat.changeType === "negative"
                      ? "text-red-500"
                      : "text-slate-500"
                  }`}
                >
                  {stat.change}
                </p>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}