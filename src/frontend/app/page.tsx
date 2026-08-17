"use client";

import { DragEvent, useEffect, useRef, useState } from "react";

import { analyzeDrawing } from "../services/api";
import type { AnalysisResponse, Shape } from "../types/api";
import { StockFormIcon, type StockFormIconKind } from "./stock-form-icons";

function fieldValue(value: string | null | undefined): string {
  return value?.trim() || "—";
}

function acceptedText(
  field: AnalysisResponse["part_number"] | AnalysisResponse["part_name"],
): string {
  return fieldValue(
    field.value ?? field.candidates.find((candidate) => candidate.value)?.value,
  );
}

function TicketRow({
  icon,
  label,
  value,
}: {
  icon?: StockFormIconKind;
  label: string;
  value: string | null | undefined;
}) {
  return (
    <div className="ticket-row">
      <dt>{label}</dt>
      <span aria-hidden="true" />
      <dd className={icon ? "stock-ticket-value" : undefined}>
        {icon ? (
          <i className="stock-form-icon">
            <StockFormIcon form={icon} />
          </i>
        ) : null}
        {fieldValue(value)}
      </dd>
    </div>
  );
}

function stockStatusMessage(analysis: AnalysisResponse, shape: Shape): string | null {
  if (analysis.recommendation) {
    if (analysis.dimensions.length.status !== "RESOLVED") {
      return "Stock size found. Overall length could not be resolved, so cut length and yield are unavailable.";
    }
    return null;
  }
  if (shape === "FLAT") {
    const missing = [
      analysis.dimensions.thickness.status !== "RESOLVED" ? "thickness" : null,
      analysis.dimensions.width.status !== "RESOLVED" ? "width" : null,
    ].filter((value): value is string => value !== null);
    if (missing.length) {
      return `${missing.join(" and ")} could not be resolved, so stock size cannot yet be calculated.`;
    }
  }
  if (
    shape === "ROUND" &&
    analysis.dimensions.diameter.status !== "RESOLVED"
  ) {
    return "Diameter could not be resolved, so stock size cannot yet be calculated.";
  }
  if (analysis.material.status !== "RESOLVED") {
    return "Material could not be resolved, so stock size cannot yet be calculated.";
  }
  if (shape === "UNKNOWN") {
    return "Stock shape could not be resolved, so stock size cannot yet be calculated.";
  }
  return "Stock size could not be calculated from this drawing.";
}

function ResultTicket({ analysis }: { analysis: AnalysisResponse }) {
  const recommendation = analysis.recommendation;
  const shape = (analysis.shape.value ??
    analysis.shape.candidates.find((candidate) => candidate.value)?.value ??
    "UNKNOWN") as Shape;
  const process =
    recommendation?.dominant_machining_process ??
    (shape === "ROUND" ? "LATHE" : shape === "FLAT" ? "MILL" : null);
  const stock =
    recommendation
      ? recommendation.stock_form.toUpperCase() === "PLATE"
        ? "Plate"
        : recommendation.stock_shape.toUpperCase() === "ROUND"
          ? "Round Bar"
          : "Flat Bar"
      : shape === "ROUND"
        ? "Round Bar"
        : shape === "FLAT"
          ? "Flat Bar or Plate"
          : null;
  const stockIcon: StockFormIconKind | undefined = recommendation
    ? recommendation.stock_form.toUpperCase() === "PLATE"
      ? "plate"
      : recommendation.stock_shape.toUpperCase() === "ROUND"
        ? "round-bar"
        : "flat-bar"
    : shape === "ROUND"
      ? "round-bar"
      : undefined;
  const material =
    recommendation?.material_name ??
    analysis.material.resolved_identity ??
    analysis.material.raw_callout;
  const statusMessage = stockStatusMessage(analysis, shape);

  return (
    <section className="result-ticket" aria-label="Raw stock result">
      <dl>
        <TicketRow label="Part No" value={acceptedText(analysis.part_number)} />
        <TicketRow label="Part Name" value={acceptedText(analysis.part_name)} />
        <TicketRow label="Process" value={process} />
        <TicketRow label="Material" value={material} />
        <TicketRow icon={stockIcon} label="Stock" value={stock} />
        {shape === "ROUND" ? (
          <TicketRow label="Stock Dia" value={recommendation?.stock_diameter} />
        ) : null}
        {shape === "FLAT" ? (
          <>
            <TicketRow label="Stock Thk" value={recommendation?.stock_thickness} />
            <TicketRow label="Stock W" value={recommendation?.stock_width} />
            {recommendation?.stock_form.toUpperCase() === "PLATE" ? (
              <TicketRow label="Stock L" value={recommendation.stock_length} />
            ) : null}
          </>
        ) : null}
        <TicketRow label="Cut Length" value={recommendation?.cut_length} />
        <TicketRow label="Drop Length" value={recommendation?.closest_drop_length} />
        <TicketRow label="12-ft Bar Yield" value={recommendation?.bar_yield} />
      </dl>
      {recommendation?.stock_note ? (
        <p className="stock-status">{recommendation.stock_note}</p>
      ) : null}
      {statusMessage ? <p className="stock-status">{statusMessage}</p> : null}
    </section>
  );
}

export default function HomePage() {
  const fileInput = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  async function runAnalysis(selected: File) {
    if (!selected.name.toLowerCase().endsWith(".pdf")) {
      setError("Choose a digitally generated PDF drawing.");
      return;
    }
    setFile(selected);
    setPreviewUrl(URL.createObjectURL(selected));
    setAnalysis(null);
    setError(null);
    setIsAnalyzing(true);
    try {
      setAnalysis(await analyzeDrawing(selected));
    } catch (requestError: unknown) {
      setError(requestError instanceof Error ? requestError.message : String(requestError));
    } finally {
      setIsAnalyzing(false);
    }
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragActive(false);
    const selected = event.dataTransfer.files[0];
    if (selected) void runAnalysis(selected);
  }

  function reset() {
    setFile(null);
    setPreviewUrl(null);
    setAnalysis(null);
    setError(null);
    if (fileInput.current) fileInput.current.value = "";
  }

  return (
    <main>
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark">M</span>
          <div>
            <strong>Machinable</strong>
            <span>Drawing review for raw stock</span>
          </div>
        </div>
        {file ? (
          <button className="button button-secondary" onClick={reset} type="button">
            New drawing
          </button>
        ) : null}
      </header>

      <input
        ref={fileInput}
        className="visually-hidden"
        type="file"
        accept="application/pdf,.pdf"
        onChange={(event) => {
          const selected = event.target.files?.[0];
          if (selected) void runAnalysis(selected);
        }}
      />

      {!file ? (
        <section className="welcome">
          <div className="welcome-copy">
            <p className="eyebrow">From print to raw stock</p>
            <h1>Know what material to order before the first cut.</h1>
            <p>Upload a digitally generated PDF part drawing.</p>
          </div>
          <div
            className={`dropzone ${dragActive ? "dropzone-active" : ""}`}
            onDragEnter={(event) => {
              event.preventDefault();
              setDragActive(true);
            }}
            onDragOver={(event) => event.preventDefault()}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
          >
            <span className="upload-symbol">↑</span>
            <h2>Drop a PDF drawing here</h2>
            <p>Digitally generated PDFs only · Up to 50 MB</p>
            <button
              className="button button-primary"
              type="button"
              onClick={() => fileInput.current?.click()}
            >
              Choose PDF
            </button>
          </div>
          {error ? <div className="error-banner">{error}</div> : null}
        </section>
      ) : (
        <>
          <div className="file-strip">
            <div>
              <strong>{file.name}</strong>
              <span>{isAnalyzing ? "Analyzing drawing…" : "Analysis complete"}</span>
            </div>
            <button className="text-button" onClick={() => fileInput.current?.click()}>
              Replace
            </button>
          </div>

          {error ? <div className="error-banner workspace-error">{error}</div> : null}

          <div className="workspace">
            <section className="drawing-pane" aria-label="Original drawing">
              {previewUrl ? (
                <iframe className="pdf-frame" src={previewUrl} title={`Drawing: ${file.name}`} />
              ) : null}
            </section>

            <section className="review-pane result-pane" aria-label="Analysis result">
              {isAnalyzing ? (
                <div className="analysis-loading">
                  <span className="spinner" />
                  <h2>Reading the drawing</h2>
                  <p>Finding the material, process, and stock size.</p>
                </div>
              ) : analysis ? (
                <ResultTicket analysis={analysis} />
              ) : null}
            </section>
          </div>
        </>
      )}
    </main>
  );
}
