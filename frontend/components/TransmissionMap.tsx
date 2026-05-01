"use client";

import { memo, useCallback, useMemo, useState } from "react";
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import { GitBranch, Info, MoveDiagonal2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type {
  EvidenceType,
  TransmissionEdge,
  TransmissionNode,
} from "@/lib/types";

type MapNodeData = TransmissionNode;

const nodeTone: Record<TransmissionNode["polarity"], string> = {
  positive: "border-emerald-300/45 bg-emerald-400/10 text-emerald-50",
  negative: "border-amber-300/45 bg-amber-400/10 text-amber-50",
  mixed: "border-violet-300/45 bg-violet-400/10 text-violet-50",
  risk: "border-rose-300/45 bg-rose-400/10 text-rose-50",
  neutral: "border-cyan-300/45 bg-cyan-400/10 text-cyan-50",
};

const edgeTone: Record<TransmissionEdge["polarity"], string> = {
  positive: "#34d399",
  negative: "#fbbf24",
  mixed: "#a78bfa",
  risk: "#fb7185",
  neutral: "#67e8f9",
};

const legendItems: Array<{
  label: string;
  polarity: TransmissionEdge["polarity"];
}> = [
  { label: "Positive", polarity: "positive" },
  { label: "Negative", polarity: "negative" },
  { label: "Mixed", polarity: "mixed" },
  { label: "Risk", polarity: "risk" },
];

const mapReadingAidItems = [
  {
    label: "Nodes",
    description: "transmission points in the shock-to-fundamentals chain",
  },
  {
    label: "Links",
    description: "directional pressure paths",
  },
  {
    label: "Use",
    description: "mechanism tracing, not a price forecast or trading signal",
  },
];

function evidenceVariant(type: EvidenceType) {
  if (type === "Data") return "data";
  if (type === "Framework inference") return "inference";
  if (type === "Narrative signal") return "narrative";
  if (type === "Open question") return "question";
  return "outline";
}

const TransmissionNodeCard = memo(function TransmissionNodeCard({
  data,
  selected,
}: NodeProps<Node<MapNodeData>>) {
  return (
    <div
      className={cn(
        "w-64 rounded-lg border p-3.5 shadow-[0_18px_60px_rgba(0,0,0,0.35)] backdrop-blur",
        nodeTone[data.polarity],
        selected && "ring-2 ring-cyan-200/70",
      )}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!size-2 !border-cyan-100 !bg-zinc-950"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!size-2 !border-cyan-100 !bg-zinc-950"
      />
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold leading-5">{data.label}</div>
          <div className="mt-1 text-xs opacity-75">{data.subtitle}</div>
        </div>
        <GitBranch className="size-4 shrink-0 opacity-70" />
      </div>
      <div className="mt-3 flex flex-wrap gap-1.5">
        <Badge variant={evidenceVariant(data.evidenceType)}>
          {data.evidenceType}
        </Badge>
        <Badge variant="outline">{data.confidence}</Badge>
      </div>
    </div>
  );
});

const nodeTypes = {
  transmission: TransmissionNodeCard,
};

type TransmissionMapProps = {
  nodes: TransmissionNode[];
  edges: TransmissionEdge[];
  description: string;
};

export function TransmissionMap({
  nodes,
  edges,
  description,
}: TransmissionMapProps) {
  const [selectedId, setSelectedId] = useState(nodes[0]?.id ?? "");
  const [activeFocus, setActiveFocus] = useState<{
    mapKey: string;
    nodeId: string;
  } | null>(null);

  const selectedNode = useMemo(
    () => nodes.find((node) => node.id === selectedId) ?? nodes[0],
    [nodes, selectedId],
  );

  const selectedNodeId = selectedNode?.id ?? "";
  const mapKey = useMemo(() => nodes.map((node) => node.id).join("|"), [nodes]);
  const activeFocusNodeId = useMemo(
    () =>
      activeFocus?.mapKey === mapKey &&
      nodes.some((node) => node.id === activeFocus.nodeId)
        ? activeFocus.nodeId
        : "",
    [nodes, activeFocus, mapKey],
  );

  const focusedEdgeIds = useMemo(
    () =>
      new Set(
        edges
          .filter(
            (edge) =>
              activeFocusNodeId !== "" &&
              (edge.source === activeFocusNodeId ||
                edge.target === activeFocusNodeId),
          )
          .map((edge) => edge.id),
      ),
    [edges, activeFocusNodeId],
  );

  const flowNodes = useMemo<Node<MapNodeData>[]>(
    () =>
      nodes.map((node) => ({
        id: node.id,
        type: "transmission",
        position: { x: node.x, y: node.y },
        data: node,
        selected: node.id === selectedNodeId,
      })),
    [nodes, selectedNodeId],
  );

  const flowEdges = useMemo<Edge[]>(
    () =>
      edges.map((edge) => {
        const hasActiveFocus = activeFocusNodeId !== "";
        const isFocused = hasActiveFocus && focusedEdgeIds.has(edge.id);

        return {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          label: edge.label,
          type: "smoothstep",
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: edgeTone[edge.polarity],
          },
          style: {
            stroke: edgeTone[edge.polarity],
            strokeWidth: isFocused ? 2.4 : 1.2,
            opacity: hasActiveFocus ? (isFocused ? 0.96 : 0.3) : 0.82,
          },
          labelStyle: {
            fill: "#e2e8f0",
            fontSize: 11,
            fontWeight: isFocused ? 650 : 500,
            opacity: isFocused ? 1 : 0,
          },
          labelBgStyle: {
            fill: "rgba(9, 9, 11, 0.88)",
            opacity: isFocused ? 1 : 0,
          },
          labelBgPadding: [6, 3],
          labelShowBg: isFocused,
          zIndex: isFocused ? 2 : 1,
        };
      }),
    [edges, focusedEdgeIds, activeFocusNodeId],
  );

  const handleNodeClick = useCallback((_: unknown, node: Node<MapNodeData>) => {
    setSelectedId(node.id);
    setActiveFocus({ mapKey, nodeId: node.id });
  }, [mapKey]);

  const handlePaneClick = useCallback(() => {
    setActiveFocus(null);
  }, []);

  return (
    <Card className="overflow-hidden border-cyan-300/15 bg-zinc-950/80">
      <CardHeader className="border-b border-white/10 pb-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <MoveDiagonal2 className="size-5 text-cyan-300" />
              Transmission map
            </CardTitle>
            <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
              {description}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {legendItems.map((item) => (
              <div
                key={item.polarity}
                className="flex items-center gap-1.5 rounded-md border border-white/10 bg-black/25 px-2 py-1 font-mono text-xs text-muted-foreground"
              >
                <span
                  className="h-0.5 w-5 rounded-full"
                  style={{ backgroundColor: edgeTone[item.polarity] }}
                />
                {item.label}
              </div>
            ))}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-md border border-white/10 bg-black/20 px-3 py-2 text-xs leading-5 text-muted-foreground">
          {mapReadingAidItems.map((item) => (
            <div key={item.label} className="flex min-w-0 items-center gap-2">
              <Badge variant="outline" className="shrink-0">
                {item.label}
              </Badge>
              <span>{item.description}</span>
            </div>
          ))}
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="grid min-h-[840px] xl:grid-cols-[1fr_360px]">
          <div className="relative min-h-[780px] border-b border-white/10 bg-[radial-gradient(circle_at_20%_20%,rgba(8,145,178,0.12),transparent_28%),linear-gradient(180deg,rgba(24,24,27,0.92),rgba(9,9,11,0.96))] xl:border-b-0 xl:border-r">
            <ReactFlow
              nodes={flowNodes}
              edges={flowEdges}
              nodeTypes={nodeTypes}
              onNodeClick={handleNodeClick}
              onPaneClick={handlePaneClick}
              fitView
              fitViewOptions={{ padding: 0.12 }}
              minZoom={0.48}
              maxZoom={1.2}
              proOptions={{ hideAttribution: true }}
            >
              <Background color="rgba(103,232,249,0.16)" gap={24} size={1} />
              <Controls
                position="bottom-left"
                className="!border-white/10 !bg-zinc-950/80 !text-cyan-50"
              />
            </ReactFlow>
          </div>
          <aside className="flex flex-col justify-between gap-4 bg-black/25 p-5">
            <div>
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-zinc-50">
                <Info className="size-4 text-cyan-300" />
                Node inspector
              </div>
              {selectedNode ? (
                <div className="space-y-4">
                  <div>
                    <div className="text-lg font-semibold text-zinc-50">
                      {selectedNode.label}
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {selectedNode.subtitle}
                    </p>
                  </div>
                  <div className="grid gap-2 text-sm">
                    <InspectorRow
                      label="Financial driver"
                      value={selectedNode.driver}
                    />
                    <div className="rounded-md border border-white/10 bg-zinc-950/70 p-3">
                      <div className="font-mono text-xs uppercase text-muted-foreground">
                        Evidence label
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2">
                        <Badge variant={evidenceVariant(selectedNode.evidenceType)}>
                          {selectedNode.evidenceType}
                        </Badge>
                        <Badge variant="outline">{selectedNode.confidence}</Badge>
                      </div>
                    </div>
                    <InspectorRow
                      label="Research implication"
                      value={selectedNode.researchImplication}
                    />
                    <InspectorRow
                      label="Why it matters"
                      value={selectedNode.whyItMatters}
                    />
                  </div>
                </div>
              ) : null}
            </div>
          </aside>
        </div>
      </CardContent>
    </Card>
  );
}

function InspectorRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-white/10 bg-zinc-950/70 p-3">
      <div className="font-mono text-xs uppercase text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 text-sm leading-6 text-zinc-100">{value}</div>
    </div>
  );
}
