"use client";

import { FileSpreadsheet, UploadCloud } from "lucide-react";
import { useRef, useState, type DragEvent } from "react";

import { cn } from "@/lib/utils";

const MAX_BYTES = 5 * 1024 * 1024;

export function FileDropzone({
  onFile,
  disabled,
  fileName,
}: {
  onFile: (file: File) => void;
  disabled?: boolean;
  fileName?: string | null;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function accept(file: File | undefined) {
    setError(null);
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("Choose a .csv file.");
      return;
    }
    if (file.size > MAX_BYTES) {
      setError("CSV uploads are limited to 5 MB.");
      return;
    }
    onFile(file);
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    if (!disabled) accept(event.dataTransfer.files[0]);
  }

  return (
    <div className="space-y-2">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          "flex flex-col items-center justify-center gap-2 rounded-[12px] border border-dashed px-6 py-10 text-center transition-colors",
          dragging ? "border-primary bg-primary-soft/40" : "border-border bg-surface-muted/25",
          disabled && "opacity-60",
        )}
      >
        <span className="flex size-11 items-center justify-center rounded-full bg-primary-soft text-primary">
          {fileName ? <FileSpreadsheet className="size-5" /> : <UploadCloud className="size-5" />}
        </span>
        <div>
          <p className="text-sm font-medium text-ink">
            {fileName ?? "Drop a CSV here, or choose a file"}
          </p>
          <p className="mt-0.5 text-xs text-ink-soft/75">UTF-8 CSV · 17 columns · maximum 5 MB and 10,000 rows</p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="sr-only"
          disabled={disabled}
          onChange={(event) => accept(event.target.files?.[0])}
          aria-label="Choose CSV file"
        />
        <button
          type="button"
          disabled={disabled}
          onClick={() => inputRef.current?.click()}
          className="mt-1 rounded-[8px] border border-border bg-surface px-3 py-1.5 text-xs font-semibold text-ink shadow-sm hover:border-primary/40 disabled:cursor-not-allowed"
        >
          Choose file
        </button>
      </div>
      {error ? <p className="text-xs text-danger" role="alert">{error}</p> : null}
    </div>
  );
}
