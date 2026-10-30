"use client";

import { useState } from "react";
import { QRCodeSVG } from "qrcode.react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";

export function QrDialog({
  open,
  onOpenChange,
  url,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  url: string;
}) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    await navigator.clipboard?.writeText(url);
    setCopied(true);
  }
  return <Dialog open={open} onOpenChange={onOpenChange} title="Scan verification link" description="The QR contains only an opaque link token, not the disclosed claims." footer={<><Button variant="secondary" onClick={() => onOpenChange(false)}>Close</Button><Button onClick={copy}>{copied ? "Copied" : "Copy link"}</Button></>}><div className="flex flex-col items-center gap-4"><div className="rounded-[12px] border border-border bg-white p-4"><QRCodeSVG value={url} size={224} level="M" includeMargin /></div><p className="max-w-sm break-all text-center font-mono text-[10px] leading-4 text-ink-soft">{url}</p><p className="text-center text-[11px] leading-5 text-ink-soft/75">Share only with the named recipient. Access expires server-side and can be revoked.</p></div></Dialog>;
}
