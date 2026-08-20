export type FieldStatus =
  | "RESOLVED"
  | "NEEDS_REVIEW"
  | "MISSING"
  | "UNSUPPORTED";

export type PresentationStatus = "COMPLETE" | "PARTIAL_SUCCESS" | "UNSUPPORTED";
export type Units = "IN" | "MM" | "UNKNOWN";
export type Shape = "ROUND" | "FLAT" | "UNKNOWN";
export type StockForm = "BAR" | "PLATE" | "DISC" | "UNKNOWN";
export type DimensionSource =
  | "EXPLICIT_OVERALL"
  | "EXPLICIT_OUTERMOST_FEATURE"
  | "RECONCILED_ACROSS_VIEWS"
  | "CHAINED_DIMENSIONS"
  | "INFERRED_OUTLINE"
  | "NOT_FOUND";

export type MaterialClassification =
  | "ALUMINUM"
  | "TITANIUM"
  | "CARBON_STEEL"
  | "ALLOY_STEEL"
  | "STAINLESS_STEEL"
  | "TOOL_STEEL"
  | "BRASS"
  | "COPPER"
  | "POLYMER"
  | "CERAMIC"
  | "COMPOSITE"
  | "CAST_IRON"
  | "CAST_ALUMINUM"
  | "NOT_FOUND";

export type CorrectionField =
  | "part_number"
  | "part_name"
  | "units"
  | "material"
  | "shape"
  | "diameter"
  | "thickness"
  | "width"
  | "length";

export interface FieldCandidate {
  reader_model: string;
  value: string | null;
  evidence: string[];
  uncertainty: string | null;
}

export interface FieldResult {
  status: FieldStatus;
  value: string | null;
  candidates: FieldCandidate[];
  reasons: string[];
  user_corrected: boolean;
}

export interface MaterialCandidate {
  reader_model: string;
  raw_callout: string | null;
  allowance_class: MaterialClassification;
  evidence: string[];
}

export interface MaterialResult {
  status: FieldStatus;
  raw_callout: string | null;
  raw_callout_evidence: string[];
  canonical_grade: string | null;
  standard_system: string | null;
  material_family: string | null;
  temper_or_condition: string | null;
  specification: string | null;
  resolved_identity: string | null;
  supplier_description: string | null;
  supplier_search_terms: Record<string, string>;
  allowance_class: MaterialClassification | null;
  resolution_basis: string | null;
  resolution_confidence: "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN";
  ambiguities: string[];
  temper_source: string | null;
  temper_confirmation_required: boolean;
  sources: string[];
  candidates: MaterialCandidate[];
  user_corrected: boolean;
}

export interface ChainTerm {
  raw_text: string;
  value: number;
  units: Units;
  evidence: string;
}

export interface DimensionCandidate {
  reader_model: string;
  value: number | null;
  units: Units;
  source: DimensionSource;
  dimension_path: string | null;
  evidence: string | null;
  uncertainty: string | null;
  chain_terms: ChainTerm[];
}

export interface DimensionFieldResult {
  status: FieldStatus;
  value: number | null;
  units: Units | null;
  source: DimensionSource | null;
  dimension_path: string | null;
  candidates: DimensionCandidate[];
  reasons: string[];
  user_corrected: boolean;
}

export interface DimensionFieldResults {
  diameter: DimensionFieldResult;
  thickness: DimensionFieldResult;
  width: DimensionFieldResult;
  length: DimensionFieldResult;
}

export interface DrawingStockCallout {
  raw_callout: string;
  shape: Shape;
  stock_form: StockForm;
  units: Units;
  diameter: number | null;
  thickness: number | null;
  width: number | null;
  length: number | null;
  evidence: string;
}

export interface DrawingStockCalloutResult {
  status: FieldStatus;
  value: DrawingStockCallout | null;
  candidates: Array<{ reader_model: string; value: DrawingStockCallout }>;
  reasons: string[];
  user_corrected: boolean;
}

export interface StockRecommendation {
  material_name: string;
  stock_shape: string;
  stock_form: string;
  supplier_description: string;
  stock_thickness: string | null;
  stock_width: string | null;
  stock_length: string | null;
  stock_diameter: string | null;
  cut_length: string | null;
  closest_drop_length: string | null;
  bar_yield: string | null;
  stock_note: string | null;
  dominant_machining_process: string;
  finished_dimensions: Record<string, string | number | null>;
  adjusted_dimensions: Record<string, string | number | null>;
}

export interface ReaderSummary {
  reader_model: string;
  status: "SUCCEEDED" | "FAILED";
  warnings: string[];
  conflicts: string[];
  error: string | null;
}

export interface AnalysisResponse {
  analysis_id: string;
  presentation_status: PresentationStatus;
  part_number: FieldResult;
  part_name: FieldResult;
  units: FieldResult;
  material: MaterialResult;
  shape: FieldResult;
  dimensions: DimensionFieldResults;
  drawing_stock_callout: DrawingStockCalloutResult;
  recommendation: StockRecommendation | null;
  blocked_outputs: string[];
  reader_summaries: ReaderSummary[];
  validation_summary: string[];
  warnings: string[];
  requires_machinist_verification: true;
  verification_message: string;
}

export interface RecalculationRequest {
  analysis_id: string;
  part_number: string | null;
  part_name: string | null;
  units: Units;
  material_callout_raw: string;
  allowance_class: MaterialClassification;
  shape: Shape;
  dimensions: {
    diameter: number | null;
    thickness: number | null;
    width: number | null;
    length: number | null;
  };
  corrected_fields: CorrectionField[];
}

export interface RecalculationResponse {
  analysis_id: string;
  recommendation: StockRecommendation;
  user_corrected_fields: CorrectionField[];
  warnings: string[];
  requires_machinist_verification: true;
  verification_message: string;
}
