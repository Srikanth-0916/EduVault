import { AlertTriangle } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

export function RiskCallout({ title, children }: { title: string; children: React.ReactNode }) {
  return <Card className="border-accent/25 bg-accent-soft/30"><CardContent className="flex items-start gap-3 p-4 text-xs leading-5 text-[#92400e]"><AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden="true" /><div><p className="font-semibold">{title}</p><p className="mt-1">{children}</p></div></CardContent></Card>;
}
