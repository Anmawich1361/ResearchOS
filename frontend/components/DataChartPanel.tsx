"use client";

import { useSyncExternalStore } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Activity } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ChartSeries } from "@/lib/types";

const chartColor: Record<ChartSeries["tone"], string> = {
  cyan: "#67e8f9",
  emerald: "#34d399",
  amber: "#fbbf24",
  rose: "#fb7185",
};

type DataChartPanelProps = {
  charts: ChartSeries[];
};

const subscribe = () => () => {};
const getClientSnapshot = () => true;
const getServerSnapshot = () => false;

export function DataChartPanel({ charts }: DataChartPanelProps) {
  const mounted = useSyncExternalStore(
    subscribe,
    getClientSnapshot,
    getServerSnapshot,
  );

  return (
    <Card className="bg-zinc-950/70">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="flex items-center gap-2">
            <Activity className="size-4 text-cyan-300" />
            Data cards
          </CardTitle>
          <Badge variant="outline">Placeholder series</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {charts.map((chart, index) => {
            const color = chartColor[chart.tone];
            const Chart = index % 2 === 0 ? AreaChart : LineChart;

            return (
              <div
                key={chart.title}
                className="rounded-md border border-white/10 bg-black/25 p-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="text-sm font-semibold text-zinc-50">
                      {chart.title}
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      {chart.subtitle}
                    </div>
                  </div>
                  <span className="font-mono text-xs text-muted-foreground">
                    {chart.unit}
                  </span>
                </div>
                <div className="mt-3 h-32">
                  {mounted ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <Chart data={chart.data} margin={{ left: -18, right: 6 }}>
                        <CartesianGrid
                          stroke="rgba(255,255,255,0.08)"
                          vertical={false}
                        />
                        <XAxis
                          dataKey="period"
                          tickLine={false}
                          axisLine={false}
                          tick={{ fill: "#a1a1aa", fontSize: 11 }}
                        />
                        <YAxis
                          tickLine={false}
                          axisLine={false}
                          tick={{ fill: "#a1a1aa", fontSize: 11 }}
                        />
                        <Tooltip
                          cursor={{ stroke: "rgba(103,232,249,0.18)" }}
                          contentStyle={{
                            background: "#09090b",
                            border: "1px solid rgba(255,255,255,0.12)",
                            borderRadius: 8,
                            color: "#fafafa",
                          }}
                        />
                        {index % 2 === 0 ? (
                          <Area
                            type="monotone"
                            dataKey="value"
                            stroke={color}
                            fill={color}
                            fillOpacity={0.18}
                            strokeWidth={2}
                          />
                        ) : (
                          <>
                            <Line
                              type="monotone"
                              dataKey="comparison"
                              stroke="rgba(161,161,170,0.55)"
                              strokeWidth={1.5}
                              dot={false}
                            />
                            <Line
                              type="monotone"
                              dataKey="value"
                              stroke={color}
                              strokeWidth={2}
                              dot={false}
                            />
                          </>
                        )}
                      </Chart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full rounded-md border border-white/10 bg-white/[0.03]" />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
