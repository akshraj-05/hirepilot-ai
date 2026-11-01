"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type FileUploaderProps = {
  /** Called when user selects or drops files */
  onFilesSelected?: (files: File[]) => void;
  accept?: string;
  multiple?: boolean;
  className?: string;
  /** When true, clears the file picker and resets to empty state */
  reset?: boolean;
};

/**
 * Drag-and-drop + click file picker for resume uploads.
 */
export function FileUploader({
  onFilesSelected,
  accept = ".pdf,.doc,.docx",
  multiple = true,
  className = "",
  reset = false,
}: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [fileNames, setFileNames] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (reset) {
      setFileNames([]);
      if (inputRef.current) inputRef.current.value = "";
    }
  }, [reset]);

  const handleFiles = useCallback(
    (list: FileList | null) => {
      if (!list?.length) return;
      const files = Array.from(list);
      setFileNames(files.map((f) => f.name));
      onFilesSelected?.(files);
    },
    [onFilesSelected],
  );

  return (
    <div className={className}>
      <label
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-[var(--hp-radius)] border-2 border-dashed px-6 py-12 transition-colors ${
          isDragging
            ? "border-[var(--hp-accent)] bg-[var(--hp-accent-muted)]"
            : "border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] hover:border-[var(--hp-accent)]"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          className="sr-only"
          accept={accept}
          multiple={multiple}
          onChange={(e) => handleFiles(e.target.files)}
        />
        <span className="text-sm font-medium text-[var(--hp-text)]">
          Drop resumes here or click to browse
        </span>
        <span className="mt-1 text-xs text-[var(--hp-text-muted)]">
          PDF or DOCX — uploaded to the backend for AI analysis
        </span>
      </label>
      {fileNames.length > 0 && (
        <ul className="mt-3 space-y-1 text-sm text-[var(--hp-text-muted)]">
          {fileNames.map((name) => (
            <li key={name} className="truncate">
              {name}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
