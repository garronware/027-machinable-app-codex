"use client";

import { DragEvent, ReactNode, useEffect, useRef, useState } from "react";

import { analyzeDrawing, recalculateStock } from "../services/api";
import type {
  AnalysisResponse,
  CorrectionField,
  DimensionFieldResult,
  FieldResult,
  FieldStatus,
  MaterialClassification,
  RecalculationResponse,
  Shape,
  StockRecommendation,
  Units,
} from "../types/api";

type DimensionName = "diameter" | "thickness" | "width" | "length";

interface EditableFacts {
  part_number: string;
  part_name: string;
  units: Units;
  material: string;
  allowance_class: MaterialClassification;
  shape: Shape;
  dimensions: Record<DimensionName, string>;
}

const EMPTY_FACTS: EditableFacts = {
  part_number: "",
  part_name: "",
  units: "UNKNOWN",
  material: "",
  allowance_class: "NOT_FOUND",
  shape: "UNKNOWN",
  dimensions: { diameter: "", thickness: "", width: "", length: "" },
};

function candidateValue(field: FieldResult): string {
  return field.value ?? field.candidates.find((candidate) => candidate.value)?.value ?? "";
}

function dimensionValue(field: DimensionFieldResult): string {
  const value = field.value ?? field.candidates.find((candidate) => candidate.value)?.value;
  return value === null || value === undefined ? "" : String(value);
}

function factsFromAnalysis(result: AnalysisResponse): EditableFacts {
  return {
    part_number: candidateValue(result.part_number),
    part_name: candidateValue(result.part_name),
    units: (candidateValue(result.units) || "UNKNOWN") as Units,
    material:
      result.material.resolved_identity ??
      result.material.raw_callout ??
      result.material.candidates.find((candidate) => candidate.raw_callout)?.raw_callout ??
      "",
    allowance_class: result.material.allowance_class ?? "NOT_FOUND",
    shape: (candidateValue(result.shape) || "UNKNOWN") as Shape,
    dimensions: {
      diameter: dimensionValue(result.dimensions.diameter),
      thickness: dimensionValue(result.dimensions.thickness),
      width: dimensionValue(result.dimensions.width),
      length: dimensionValue(result.dimensions.length),
    },
  };
}

function parseDimension(value: string): number | null {
  if (!value.trim()) return null;
  const number = Number(value);
  return Number.isFinite(number) && number > 0 ? number : null;
}

function statusLabel(status: FieldStatus): string {
  return {
    RESOLVED: "Resolved",
    NEEDS_REVIEW: "Needs review",
    MISSING: "Missing",
    UNSUPPORTED: "Unsupported",
  }[status];
}

function StatusBadge({ status, corrected = false }: { status: FieldStatus; corrected?: boolean }) {
  return (
    <span className={`status status-${corrected ? "corrected" : status.toLowerCase()}`}>
      {corrected ? "Used for calculation" : statusLabel(status)}
    </span>
  );
}

function CandidateEvidence({ analysis }: { analysis: AnalysisResponse }) {
  const textFields = [
    ["Part number", analysis.part_number],
    ["Part name", analysis.part_name],
    ["Units", analysis.units],
    ["Shape", analysis.shape],
  ] as const;
  const dimensionFields = Object.entries(analysis.dimensions) as Array<
    [DimensionName, DimensionFieldResult]
  >;

  return (
    <div className="candidate-evidence">
      <h3>Field candidates</h3>
      {textFields.map(([label, field]) => (
        <section key={label} className="candidate-group">
          <strong>{label}</strong>
          {field.candidates.map((candidate, index) => (
            <p key={`${candidate.reader_model}-${index}`}>
              <b>{candidate.reader_model}:</b> {candidate.value ?? "not found"}
              {candidate.evidence.length ? ` — ${candidate.evidence.join(" · ")}` : ""}
              {candidate.uncertainty ? ` — ${candidate.uncertainty}` : ""}
            </p>
          ))}
        </section>
      ))}

      <section className="candidate-group">
        <strong>Material</strong>
        {analysis.material.candidates.map((candidate, index) => (
          <p key={`${candidate.reader_model}-${index}`}>
            <b>{candidate.reader_model}:</b> {candidate.raw_callout ?? "not found"}
            {candidate.evidence.length ? ` — ${candidate.evidence.join(" · ")}` : ""}
          </p>
        ))}
      </section>

      {dimensionFields.map(([name, field]) => (
        <section key={name} className="candidate-group">
          <strong>{name[0].toUpperCase() + name.slice(1)}</strong>
          {field.candidates.map((candidate, index) => (
            <p key={`${candidate.reader_model}-${index}`}>
              <b>{candidate.reader_model}:</b>{" "}
              {candidate.value === null ? "not found" : `${candidate.value} ${candidate.units}`}
              {candidate.dimension_path ? ` — ${candidate.dimension_path}` : ""}
              {candidate.evidence ? ` — ${candidate.evidence}` : ""}
              {candidate.uncertainty ? ` — ${candidate.uncertainty}` : ""}
            </p>
          ))}
        </section>
      ))}
    </div>
  );
}

function FieldEditor({
  label,
  status,
  corrected,
  detail,
  reasons,
  children,
}: {
  label: string;
  status: FieldStatus;
  corrected: boolean;
  detail?: string | null;
  reasons: string[];
  children: ReactNode;
}) {
  return (
    <div className={`field-row ${status === "NEEDS_REVIEW" ? "field-review" : ""}`}>
      <div className="field-heading">
        <div>
          <label>{label}</label>
          {detail ? <p>{detail}</p> : null}
        </div>
        <StatusBadge status={status} corrected={corrected} />
      </div>
      {children}
      {reasons.length ? <p className="field-reason">{reasons.join(" ")}</p> : null}
    </div>
  );
}

function NotApplicableDimension({ label }: { label: string }) {
  return (
    <div className="field-row field-not-applicable">
      <div className="field-heading">
        <label>{label}</label>
        <span className="status status-not_applicable">Not applicable</span>
      </div>
      <div className="dimension-input">
        <input disabled value="" aria-label={`${label}: not applicable`} />
        <span>—</span>
      </div>
    </div>
  );
}

function RecommendationPanel({
  recommendation,
  recalculated,
}: {
  recommendation: StockRecommendation;
  recalculated: boolean;
}) {
  const dimensions = recommendation.stock_diameter
    ? `Dia ${recommendation.stock_diameter}`
    : [
        recommendation.stock_thickness ? `Thk ${recommendation.stock_thickness}` : null,
        recommendation.stock_width ? `W ${recommendation.stock_width}` : null,
      ]
        .filter(Boolean)
        .join(" × ");
  return (
    <section
      className={`recommendation ${recalculated ? "recommendation-unverified" : ""}`}
      aria-labelledby="recommendation-title"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">Order recommendation</p>
          <h2 id="recommendation-title">
            Buy {recommendation.material_name} {recommendation.stock_form}
          </h2>
          <p className="recommendation-order">
            {dimensions || "Custom size"} · Cut to {recommendation.cut_length}
          </p>
        </div>
        <span
          className={`recommendation-state ${recalculated ? "recommendation-state-unverified" : ""}`}
        >
          {recalculated ? "Unverified estimate" : "Ready for review"}
        </span>
      </div>
      <dl className="recommendation-grid">
        <div>
          <dt>Stock size</dt>
          <dd>{dimensions || "—"}</dd>
        </div>
        <div>
          <dt>Cut length</dt>
          <dd>{recommendation.cut_length}</dd>
        </div>
        <div>
          <dt>Closest drop</dt>
          <dd>{recommendation.closest_drop_length}</dd>
        </div>
        <div>
          <dt>12-foot bar yield</dt>
          <dd>{recommendation.bar_yield}</dd>
        </div>
      </dl>
    </section>
  );
}

export default function HomePage() {
  const fileInput = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [recalculation, setRecalculation] = useState<RecalculationResponse | null>(null);
  const [facts, setFacts] = useState<EditableFacts>(EMPTY_FACTS);
  const [correctedFields, setCorrectedFields] = useState<CorrectionField[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isRecalculating, setIsRecalculating] = useState(false);
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
    setRecalculation(null);
    setCorrectedFields([]);
    setFacts(EMPTY_FACTS);
    setError(null);
    setIsAnalyzing(true);
    try {
      const result = await analyzeDrawing(selected);
      setAnalysis(result);
      setFacts(factsFromAnalysis(result));
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

  function markCorrected(field: CorrectionField) {
    setCorrectedFields((current) => (current.includes(field) ? current : [...current, field]));
    setRecalculation(null);
  }

  function updateFact<K extends Exclude<keyof EditableFacts, "dimensions">>(
    key: K,
    value: EditableFacts[K],
    correction: CorrectionField,
  ) {
    setFacts((current) => ({ ...current, [key]: value }));
    markCorrected(correction);
  }

  function updateDimension(name: DimensionName, value: string) {
    setFacts((current) => ({
      ...current,
      dimensions: { ...current.dimensions, [name]: value },
    }));
    markCorrected(name);
  }

  const hasRequiredDimensions =
    facts.shape === "ROUND"
      ? Boolean(
          (parseDimension(facts.dimensions.diameter) ||
            (parseDimension(facts.dimensions.thickness) &&
              parseDimension(facts.dimensions.width))) &&
            parseDimension(facts.dimensions.length),
        )
      : facts.shape === "FLAT"
        ? Boolean(
            parseDimension(facts.dimensions.thickness) &&
              parseDimension(facts.dimensions.width) &&
              parseDimension(facts.dimensions.length),
          )
        : false;
  const canRecalculate = Boolean(
    analysis &&
      correctedFields.length &&
      facts.units !== "UNKNOWN" &&
      facts.shape !== "UNKNOWN" &&
      facts.material.trim() &&
      facts.allowance_class !== "NOT_FOUND" &&
      hasRequiredDimensions,
  );

  const requiredDimensionNames: DimensionName[] =
    facts.shape === "ROUND"
      ? parseDimension(facts.dimensions.diameter)
        ? ["diameter", "length"]
        : ["thickness", "width", "length"]
      : facts.shape === "FLAT"
        ? ["thickness", "width", "length"]
        : [];
  const confirmableFields: CorrectionField[] = analysis
    ? [
        ...(analysis.units.status === "RESOLVED" ? [] : (["units"] as CorrectionField[])),
        ...(analysis.material.status === "RESOLVED" ? [] : (["material"] as CorrectionField[])),
        ...(analysis.shape.status === "RESOLVED" ? [] : (["shape"] as CorrectionField[])),
        ...requiredDimensionNames.filter(
          (name) => analysis.dimensions[name].status !== "RESOLVED",
        ),
      ]
    : [];
  const canConfirmShownValues = Boolean(
    analysis &&
      facts.units !== "UNKNOWN" &&
      facts.shape !== "UNKNOWN" &&
      facts.material.trim() &&
      facts.allowance_class !== "NOT_FOUND" &&
      hasRequiredDimensions,
  );
  const stockBlockers = analysis
    ? [
        ...(analysis.units.status === "RESOLVED" ? [] : analysis.units.reasons),
        ...(analysis.material.status === "RESOLVED" ? [] : analysis.material.ambiguities),
        ...(analysis.shape.status === "RESOLVED" ? [] : analysis.shape.reasons),
        ...requiredDimensionNames.flatMap((name) =>
          analysis.dimensions[name].status === "RESOLVED"
            ? []
            : analysis.dimensions[name].reasons,
        ),
      ]
    : [];

  async function runRecalculation(fields: CorrectionField[]) {
    if (!analysis) return;
    setIsRecalculating(true);
    setError(null);
    try {
      const result = await recalculateStock({
        analysis_id: analysis.analysis_id,
        part_number: facts.part_number.trim() || null,
        part_name: facts.part_name.trim() || null,
        units: facts.units,
        material_callout_raw: facts.material.trim(),
        allowance_class: facts.allowance_class,
        shape: facts.shape,
        dimensions: {
          diameter: parseDimension(facts.dimensions.diameter),
          thickness: parseDimension(facts.dimensions.thickness),
          width: parseDimension(facts.dimensions.width),
          length: parseDimension(facts.dimensions.length),
        },
        corrected_fields: fields,
      });
      setRecalculation(result);
    } catch (requestError: unknown) {
      setError(requestError instanceof Error ? requestError.message : String(requestError));
    } finally {
      setIsRecalculating(false);
    }
  }

  async function handleRecalculate() {
    if (!canRecalculate) return;
    await runRecalculation(correctedFields);
  }

  async function handleConfirmShownValues() {
    if (!canConfirmShownValues) return;
    const fields = Array.from(new Set(confirmableFields));
    setCorrectedFields((current) => Array.from(new Set([...current, ...fields])));
    await runRecalculation(fields);
  }

  function reset() {
    setFile(null);
    setPreviewUrl(null);
    setAnalysis(null);
    setRecalculation(null);
    setFacts(EMPTY_FACTS);
    setCorrectedFields([]);
    setError(null);
    if (fileInput.current) fileInput.current.value = "";
  }

  const recommendation = recalculation?.recommendation ?? analysis?.recommendation ?? null;
  const dimensionEntries: Array<[DimensionName, string]> = [
    ["diameter", "Diameter"],
    ["thickness", "Thickness"],
    ["width", "Width"],
    ["length", "Overall length"],
  ];

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
        <div className="header-actions">
          <span className="scope-note">Digital PDF pilot</span>
          {file ? (
            <button className="button button-secondary" onClick={reset} type="button">
              New drawing
            </button>
          ) : null}
        </div>
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
            <p className="eyebrow">From print to purchasing intent</p>
            <h1>Know what stock to order before the first cut.</h1>
            <p>
              Upload one digitally generated engineering drawing. Machinable compares two
              independent reads, shows what is known, and keeps uncertainty visible.
            </p>
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
          <section className="progress-strip" aria-live="polite">
            <div>
              <strong>{file.name}</strong>
              <span>{isAnalyzing ? "Analysis in progress" : "Analysis received"}</span>
            </div>
            <ol>
              {[
                { label: "Read PDF evidence", complete: Boolean(analysis) },
                { label: "Compare Sol and Terra", complete: Boolean(analysis) },
                { label: "Resolve stock recommendation", complete: Boolean(recommendation) },
              ].map(({ label, complete }) => (
                <li className={complete ? "stage-complete" : "stage-active"} key={label}>
                  <span>{complete ? "✓" : "•"}</span>
                  {label}
                </li>
              ))}
            </ol>
          </section>

          {error ? <div className="error-banner workspace-error">{error}</div> : null}

          <div className="workspace">
            <section className="drawing-pane" aria-label="Original drawing">
              <div className="pane-heading">
                <div>
                  <p className="eyebrow">Original drawing</p>
                  <h2>{file.name}</h2>
                </div>
                <button className="text-button" onClick={() => fileInput.current?.click()}>
                  Replace
                </button>
              </div>
              {previewUrl ? (
                <iframe className="pdf-frame" src={previewUrl} title={`Drawing: ${file.name}`} />
              ) : null}
            </section>

            <section className="review-pane" aria-label="Analysis review">
              {isAnalyzing ? (
                <div className="analysis-loading">
                  <span className="spinner" />
                  <h2>Reading the drawing</h2>
                  <p>Sol and Terra are independently reviewing the same PDF.</p>
                </div>
              ) : analysis ? (
                <>
                  <div className="review-header">
                    <div>
                      <p className="eyebrow">Analysis review</p>
                      <h1>
                        {analysis.presentation_status === "COMPLETE"
                          ? "Recommendation ready"
                          : analysis.presentation_status === "PARTIAL_SUCCESS"
                            ? "Review required"
                            : "Unsupported drawing"}
                      </h1>
                    </div>
                    <span className={`summary-status summary-${analysis.presentation_status.toLowerCase()}`}>
                      {analysis.presentation_status.replace("_", " ").toLowerCase()}
                    </span>
                  </div>

                  {recommendation ? (
                    <RecommendationPanel
                      recommendation={recommendation}
                      recalculated={Boolean(recalculation)}
                    />
                  ) : (
                    <section className="blocked-panel">
                      <div>
                        <p className="eyebrow">Stock recommendation</p>
                        <h2>Waiting for usable inputs</h2>
                        <p>
                          Review the highlighted candidates before calculating an estimate.
                        </p>
                      </div>
                      {analysis.blocked_outputs.length ? (
                        <p className="blocked-list">Blocked: {analysis.blocked_outputs.join(", ")}</p>
                      ) : null}
                      {stockBlockers.length ? (
                        <ul className="blocked-reasons">
                          {stockBlockers.map((reason) => (
                            <li key={reason}>{reason}</li>
                          ))}
                        </ul>
                      ) : null}
                      {canConfirmShownValues ? (
                        <button
                          className="button button-primary confirm-stock-button"
                          disabled={isRecalculating}
                          onClick={() => void handleConfirmShownValues()}
                          type="button"
                        >
                          {isRecalculating
                            ? "Calculating stock…"
                            : "Calculate estimate from shown values"}
                        </button>
                      ) : null}
                    </section>
                  )}

                  <div className="field-section">
                    <div className="section-title">
                      <h2>Part</h2>
                      <span>Identity</span>
                    </div>
                    <FieldEditor
                      label="Part number"
                      status={analysis.part_number.status}
                      corrected={correctedFields.includes("part_number")}
                      reasons={analysis.part_number.reasons}
                    >
                      <input
                        value={facts.part_number}
                        onChange={(event) => updateFact("part_number", event.target.value, "part_number")}
                      />
                    </FieldEditor>
                    <FieldEditor
                      label="Part name"
                      status={analysis.part_name.status}
                      corrected={correctedFields.includes("part_name")}
                      reasons={analysis.part_name.reasons}
                    >
                      <input
                        value={facts.part_name}
                        onChange={(event) => updateFact("part_name", event.target.value, "part_name")}
                      />
                    </FieldEditor>
                  </div>

                  <div className="field-section">
                    <div className="section-title">
                      <h2>Material and form</h2>
                      <span>Purchasing intent</span>
                    </div>
                    <FieldEditor
                      label="Material"
                      status={analysis.material.status}
                      corrected={correctedFields.includes("material")}
                      detail={
                        analysis.material.raw_callout &&
                        analysis.material.raw_callout !== analysis.material.resolved_identity
                          ? `Drawing callout: ${analysis.material.raw_callout}`
                          : null
                      }
                      reasons={analysis.material.ambiguities}
                    >
                      <input
                        value={facts.material}
                        onChange={(event) => updateFact("material", event.target.value, "material")}
                      />
                    </FieldEditor>
                    <FieldEditor
                      label="Stock shape"
                      status={analysis.shape.status}
                      corrected={correctedFields.includes("shape")}
                      reasons={analysis.shape.reasons}
                    >
                      <select
                        value={facts.shape}
                        onChange={(event) => updateFact("shape", event.target.value as Shape, "shape")}
                      >
                        <option value="UNKNOWN">Select shape</option>
                        <option value="ROUND">Round bar</option>
                        <option value="FLAT">Flat bar or plate</option>
                      </select>
                    </FieldEditor>
                  </div>

                  <div className="field-section">
                    <div className="section-title">
                      <h2>Finished dimensions</h2>
                      <select
                        className="unit-select"
                        aria-label="Primary units"
                        value={facts.units}
                        onChange={(event) => updateFact("units", event.target.value as Units, "units")}
                      >
                        <option value="UNKNOWN">Units</option>
                        <option value="IN">Inches</option>
                        <option value="MM">Millimeters</option>
                      </select>
                    </div>
                    <div className="dimension-grid">
                      {dimensionEntries.map(([name, label]) => {
                        const result = analysis.dimensions[name];
                        const roundUsesCrossSection =
                          facts.shape === "ROUND" &&
                          !parseDimension(facts.dimensions.diameter) &&
                          Boolean(
                            parseDimension(facts.dimensions.thickness) &&
                              parseDimension(facts.dimensions.width),
                          );
                        const applicable =
                          facts.shape === "FLAT"
                            ? name !== "diameter"
                            : facts.shape === "ROUND"
                              ? name !== "thickness" && name !== "width"
                                ? true
                                : roundUsesCrossSection
                              : true;
                        if (!applicable) {
                          return <NotApplicableDimension key={name} label={label} />;
                        }
                        return (
                          <FieldEditor
                            key={name}
                            label={label}
                            status={result.status}
                            corrected={correctedFields.includes(name)}
                            detail={result.dimension_path}
                            reasons={result.reasons}
                          >
                            <div className="dimension-input">
                              <input
                                inputMode="decimal"
                                value={facts.dimensions[name]}
                                onChange={(event) => updateDimension(name, event.target.value)}
                              />
                              <span>{facts.units === "UNKNOWN" ? "—" : facts.units}</span>
                            </div>
                          </FieldEditor>
                        );
                      })}
                    </div>
                  </div>

                  {analysis.drawing_stock_callout.value ? (
                    <section className="drawing-stock">
                      <div>
                        <p className="eyebrow">Drawing-specified stock</p>
                        <strong>{analysis.drawing_stock_callout.value.raw_callout}</strong>
                        <p>{analysis.drawing_stock_callout.value.evidence}</p>
                      </div>
                      <StatusBadge status={analysis.drawing_stock_callout.status} />
                    </section>
                  ) : null}

                  {correctedFields.length ? (
                    <div className="recalculate-bar">
                      <div>
                        <strong>{correctedFields.length} field{correctedFields.length === 1 ? "" : "s"} changed</strong>
                        <span>Uses deterministic shop math only</span>
                      </div>
                      <button
                        className="button button-primary"
                        disabled={!canRecalculate || isRecalculating}
                        onClick={() => void handleRecalculate()}
                      >
                        {isRecalculating ? "Recalculating…" : "Recalculate stock"}
                      </button>
                    </div>
                  ) : null}

                  <details className="evidence-drawer">
                    <summary>Reader evidence and validation</summary>
                    <div className="evidence-content">
                      {analysis.reader_summaries.map((reader) => (
                        <div key={reader.reader_model}>
                          <strong>{reader.reader_model}</strong>
                          <span>{reader.status.toLowerCase()}</span>
                          {[...reader.conflicts, ...reader.warnings].map((item) => (
                            <p key={item}>{item}</p>
                          ))}
                          {reader.error ? <p>{reader.error}</p> : null}
                        </div>
                      ))}
                      <div>
                        <strong>Validation</strong>
                        {analysis.validation_summary.map((item) => (
                          <p key={item}>{item}</p>
                        ))}
                      </div>
                    </div>
                    <CandidateEvidence analysis={analysis} />
                  </details>

                  <p className="verification-note">{analysis.verification_message}</p>
                </>
              ) : null}
            </section>
          </div>
        </>
      )}
    </main>
  );
}
