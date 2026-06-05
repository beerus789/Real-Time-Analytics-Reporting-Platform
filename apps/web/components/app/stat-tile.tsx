import { LucideIcon } from "lucide-react";

import { Panel, PanelBody } from "@/components/ui/panel";

export function StatTile({
  label,
  value,
  helper,
  icon: Icon
}: {
  label: string;
  value: string;
  helper: string;
  icon: LucideIcon;
}) {
  return (
    <Panel>
      <PanelBody className="flex items-center justify-between gap-4">
        <div>
          <div className="text-sm text-muted-foreground">{label}</div>
          <div className="mt-2 text-2xl font-semibold">{value}</div>
          <div className="mt-1 text-xs text-muted-foreground">{helper}</div>
        </div>
        <div className="flex h-11 w-11 items-center justify-center rounded-md bg-primary/10 text-primary">
          <Icon className="h-5 w-5" aria-hidden />
        </div>
      </PanelBody>
    </Panel>
  );
}

