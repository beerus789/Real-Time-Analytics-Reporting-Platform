"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { Badge } from "@/components/ui/badge";
import { Table, Td, Th } from "@/components/ui/table";
import type { Widget, WidgetData } from "@/types/api";

const colors = ["#0f766e", "#f97316", "#4f46e5", "#16a34a", "#dc2626"];

function normalizedRows(data?: WidgetData) {
  return data?.rows.map((row, index) => ({
    name: String(row.bucket ?? row.group ?? `Row ${index + 1}`),
    value: Number(row.value ?? 0)
  })) ?? [];
}

export function WidgetChart({ widget, data }: { widget: Widget; data?: WidgetData }) {
  const rows = normalizedRows(data);
  if (widget.kind === "kpi") {
    return (
      <div className="flex h-full min-h-32 flex-col justify-center">
        <div className="text-4xl font-semibold">{rows[0]?.value ?? 0}</div>
        <div className="mt-3 flex flex-wrap gap-2">
          <Badge tone="success">{widget.query.aggregate}</Badge>
          {widget.query.event_name ? <Badge tone="accent">{widget.query.event_name}</Badge> : null}
        </div>
      </div>
    );
  }

  if (widget.kind === "table") {
    return (
      <Table className="min-w-full">
        <thead>
          <tr>
            <Th>Dimension</Th>
            <Th>Value</Th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.name}>
              <Td>{row.name}</Td>
              <Td>{row.value}</Td>
            </tr>
          ))}
        </tbody>
      </Table>
    );
  }

  if (widget.kind === "pie") {
    return (
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Tooltip />
          <Pie data={rows} dataKey="value" nameKey="name" innerRadius={52} outerRadius={88}>
            {rows.map((_row, index) => (
              <Cell key={index} fill={colors[index % colors.length]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (widget.kind === "bar") {
    return (
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" tickLine={false} axisLine={false} minTickGap={24} />
          <YAxis tickLine={false} axisLine={false} />
          <Tooltip />
          <Bar dataKey="value" fill="#f97316" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={rows}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="name" tickLine={false} axisLine={false} minTickGap={24} />
        <YAxis tickLine={false} axisLine={false} />
        <Tooltip />
        <Line type="monotone" dataKey="value" stroke="#0f766e" strokeWidth={3} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

