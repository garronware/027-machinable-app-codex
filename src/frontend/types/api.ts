export type ShapeType = "CUBE" | "CYLINDER";

export interface NakedBoundingDims {
  Thk?: number;
  W?: number;
  Dia?: number;
  L: number;
  Units: string;
  Shape: ShapeType;
}

export interface AdjustedBoundingDims extends NakedBoundingDims {
  Lookup_Tbl: string;
}

export interface PartBasics {
  Part_No: string;
  Part_Name?: string;
  Dominant_Machining_Process: "MILL" | "LATHE";
  Naked_Bounding_Dims: NakedBoundingDims;
  Naked_Dims_Plus_Machining_Alwnc: AdjustedBoundingDims;
}

export interface RawMaterialNeeded {
  Matl_Name: string;
  Stock_Shape: string;
  Stock_Form: string;
  Prod_Descr: string;
  Stock_Thk?: string;
  Stock_W?: string;
  Stock_Dia?: string;
  Cut_L: string;
  Closest_Drop_L: string;
  "12-Ft_Bar_Yields": string;
}

export interface AnalysisMetadata {
  warnings: string[];
  requires_machinist_verification: true;
  verification_message: string;
}

export interface FinalOutput {
  Part_Basics: PartBasics;
  Raw_Matl_Needed: RawMaterialNeeded;
  _analysis?: AnalysisMetadata;
}

