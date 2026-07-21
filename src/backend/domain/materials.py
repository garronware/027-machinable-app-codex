"""Conservative deterministic material and purchasing-intent resolution."""

from __future__ import annotations

import re
from dataclasses import dataclass

from backend.domain.models import (
    FieldResult,
    FieldStatus,
    MaterialClassification,
    MaterialResult,
    Shape,
)


@dataclass(frozen=True)
class MaterialFamilyRule:
    pattern: re.Pattern[str]
    classification: MaterialClassification
    family: str
    identity_suffix: str


FAMILY_RULES = (
    MaterialFamilyRule(
        re.compile(r"\b(?:6061|7075|2024|5052|6063|MIC[ -]?6)\b", re.I),
        MaterialClassification.ALUMINUM,
        "Aluminum Alloy",
        "Aluminum Alloy",
    ),
    MaterialFamilyRule(
        re.compile(r"\b(?:303|304|316L?|17[ -]?4)\b|STAINLESS|\bSST\b", re.I),
        MaterialClassification.STAINLESS_STEEL,
        "Stainless Steel",
        "Stainless Steel",
    ),
    MaterialFamilyRule(
        re.compile(
            r"\b(?:4130|4140H?|4145|4150H?|4340H?|8620|52100)\b|ALLOY STEEL",
            re.I,
        ),
        MaterialClassification.ALLOY_STEEL,
        "Alloy Steel",
        "Alloy Steel",
    ),
    MaterialFamilyRule(
        re.compile(r"\b(?:1008|1018|1020|1215|A36)\b|MILD STEEL", re.I),
        MaterialClassification.MILD_STEEL,
        "Carbon Steel",
        "Carbon Steel",
    ),
    MaterialFamilyRule(
        re.compile(r"\b(?:A2|D2|H13|T15|M2)\b|TOOL STEEL|\bHSS\b", re.I),
        MaterialClassification.TOOL_STEEL,
        "Tool Steel",
        "Tool Steel",
    ),
    MaterialFamilyRule(
        re.compile(r"TUNGSTEN CARBIDE|\bCARBIDE\b", re.I),
        MaterialClassification.CERAMIC,
        "Tungsten Carbide",
        "Tungsten Carbide",
    ),
    MaterialFamilyRule(
        re.compile(r"\bTITANIUM\b|\bTI[- ]?6AL[- ]?4V\b", re.I),
        MaterialClassification.TITANIUM,
        "Titanium Alloy",
        "Titanium Alloy",
    ),
    MaterialFamilyRule(
        re.compile(r"\b(?:BRASS|BRONZE)\b", re.I),
        MaterialClassification.BRASS,
        "Copper Alloy",
        "Brass/Bronze",
    ),
    MaterialFamilyRule(
        re.compile(r"\bCOPPER\b", re.I),
        MaterialClassification.COPPER,
        "Copper",
        "Copper",
    ),
    MaterialFamilyRule(
        re.compile(r"\b(?:DELRIN|ACETAL|NYLON|PEEK|UHMW)\b", re.I),
        MaterialClassification.POLYMER,
        "Engineering Polymer",
        "Engineering Polymer",
    ),
)


def _normalized_grade(value: str) -> str:
    return re.sub(r"\s+", "", value.upper())


def _rule_and_grades(raw_callout: str) -> tuple[MaterialFamilyRule | None, list[str]]:
    """Return deterministic material meaning without depending on phrasing."""

    matched_rules = [rule for rule in FAMILY_RULES if rule.pattern.search(raw_callout)]
    classifications = {rule.classification for rule in matched_rules}
    if not matched_rules or len(classifications) != 1:
        return None, []

    rule = matched_rules[0]
    grade_matches: list[str] = []
    for match in rule.pattern.finditer(raw_callout):
        if not re.search(r"\d|^[A-Z]\d+$|MIC|CARBIDE", match.group(0), re.I):
            continue
        window = raw_callout[max(0, match.start() - 12) : match.end() + 12]
        if rule.classification is MaterialClassification.TOOL_STEEL and re.search(
            r"\b[A-Z]\d+\s*(?:TO|THROUGH|-)\s*[A-Z]\d+\b", window, re.I
        ):
            # Range endpoints identify a permitted family, not one selected grade.
            continue
        grade_matches.append(_normalized_grade(match.group(0)))
    return rule, list(dict.fromkeys(grade_matches))


def _condition(raw_callout: str) -> tuple[str | None, str | None]:
    upper = raw_callout.upper()
    temper = re.search(r"(?<![A-Z0-9])T(?:3|4|5|6|51|651|7|73|7351)(?!\d)", upper)
    conditions: list[str] = []
    if "HR" in upper or "HOT ROLLED" in upper:
        conditions.append("Hot Rolled")
    if "Q&T" in upper or "QUENCHED AND TEMPERED" in upper:
        conditions.append("Quenched and Tempered")
    if "NORMALIZED" in upper:
        conditions.append("Normalized")
    if "ANNEALED" in upper:
        conditions.append("Annealed")
    if temper:
        conditions.insert(0, temper.group(0))
    if not conditions:
        return None, None
    return ", ".join(dict.fromkeys(conditions)), "drawing material callout"


def _standard_system(raw_callout: str) -> str | None:
    upper = raw_callout.upper()
    for standard in ("ASTM", "AISI", "SAE", "AMS", "MIL", "ASME"):
        if standard in upper:
            return standard
    return None


def _stock_form(shape: FieldResult) -> str:
    if shape.status is not FieldStatus.RESOLVED:
        return "Stock"
    if shape.value == Shape.ROUND.value:
        return "Round Bar"
    if shape.value == Shape.FLAT.value:
        return "Flat Bar or Plate"
    return "Stock"


def _apply_resolution(
    material: MaterialResult,
    shape: FieldResult,
    *,
    rule: MaterialFamilyRule,
    grades: list[str],
    metadata_raw: str,
    resolution_basis: str,
    condition: str | None = None,
    temper_source: str | None = None,
) -> MaterialResult:
    material.ambiguities = [
        ambiguity
        for ambiguity in material.ambiguities
        if ambiguity
        not in {
            "Readers disagree on the exact material callout.",
            "The machining-allowance material class is unresolved.",
        }
    ]
    if (
        rule.classification is MaterialClassification.TOOL_STEEL
        and "A2" in grades
        and len(grades) > 1
    ):
        # A2 is the discrete common purchasing grade when the drawing also
        # permits a broad high-speed-tool-steel family or range.
        grades = ["A2"]
    canonical_grade = " / ".join(grades) if grades else None
    if rule.classification is MaterialClassification.CERAMIC:
        canonical_grade = "Tungsten Carbide"
        identity = "Tungsten Carbide"
    elif (
        rule.classification is MaterialClassification.ALUMINUM
        and canonical_grade
        and condition
        and condition.startswith("T")
    ):
        identity = f"{canonical_grade}-{condition} {rule.identity_suffix}"
    elif canonical_grade:
        identity = f"{canonical_grade} {rule.identity_suffix}"
    else:
        identity = rule.family
    if condition and not (
        rule.classification is MaterialClassification.ALUMINUM
        and canonical_grade
        and condition.startswith("T")
    ):
        identity = f"{identity}, {condition}"

    supplier_description = f"{identity} {_stock_form(shape)}"
    if material.allowance_class not in (None, rule.classification):
        material.ambiguities.append(
            "Reader material class was replaced by the deterministic grade mapping."
        )
    material.status = FieldStatus.RESOLVED
    material.allowance_class = rule.classification
    material.canonical_grade = canonical_grade
    material.standard_system = _standard_system(metadata_raw)
    material.material_family = rule.family
    material.temper_or_condition = condition
    material.resolved_identity = identity
    material.supplier_description = supplier_description
    material.supplier_search_terms = {
        "mcmaster_carr": supplier_description,
        "alro": supplier_description,
    }
    material.resolution_basis = resolution_basis
    material.resolution_confidence = "HIGH" if canonical_grade else "MEDIUM"
    material.temper_source = temper_source
    material.temper_confirmation_required = condition is None
    if condition is None:
        material.ambiguities.append(
            "Temper or purchasing condition was not explicit; confirm before ordering."
        )
    return material


def resolve_material(material: MaterialResult, shape: FieldResult) -> MaterialResult:
    """Resolve only explicit known families; preserve obscure codes as unresolved."""

    candidate_raws = [
        candidate.raw_callout.strip()
        for candidate in material.candidates
        if candidate.raw_callout and candidate.raw_callout.strip()
    ]
    if len(candidate_raws) >= 2:
        candidate_facts = [_rule_and_grades(raw) for raw in candidate_raws]
        candidate_rules = [rule for rule, _ in candidate_facts if rule is not None]
        if len(candidate_rules) == len(candidate_raws) and len(
            {rule.classification for rule in candidate_rules}
        ) == 1:
            grade_sets = [set(grades) for _, grades in candidate_facts]
            shared_grades = set.intersection(*grade_sets) if grade_sets else set()
            ordered_shared_grades = [
                grade
                for grade in candidate_facts[0][1]
                if grade in shared_grades
            ]
            if ordered_shared_grades:
                conditions = [_condition(raw)[0] for raw in candidate_raws]
                shared_condition = (
                    conditions[0]
                    if conditions[0] is not None and len(set(conditions)) == 1
                    else None
                )
                material.ambiguities = [
                    ambiguity
                    for ambiguity in material.ambiguities
                    if ambiguity != "Readers disagree on the exact material callout."
                ]
                return _apply_resolution(
                    material,
                    shape,
                    rule=candidate_rules[0],
                    grades=ordered_shared_grades,
                    metadata_raw=candidate_raws[0],
                    resolution_basis=(
                        "Independent reader wording normalized to the same material grade."
                    ),
                    condition=shared_condition,
                    temper_source=(
                        "agreed drawing material callout" if shared_condition else None
                    ),
                )

    if material.status is not FieldStatus.RESOLVED or not material.raw_callout:
        return material
    raw = material.raw_callout.strip()
    if re.fullmatch(r"\d{4,8}", raw):
        material.allowance_class = None
        material.canonical_grade = None
        material.material_family = None
        material.resolved_identity = raw
        material.supplier_description = None
        material.supplier_search_terms = {}
        material.resolution_basis = "Exact drawing code preserved; no authoritative mapping."
        material.resolution_confidence = "UNKNOWN"
        material.ambiguities.append(
            "Manufacturer material code requires an authoritative cross-reference."
        )
        material.temper_confirmation_required = True
        return material

    rule, grades = _rule_and_grades(raw)
    matched_rules = [item for item in FAMILY_RULES if item.pattern.search(raw)]
    if not matched_rules:
        material.allowance_class = None
        material.resolved_identity = raw
        material.supplier_description = None
        material.supplier_search_terms = {}
        material.resolution_basis = "Exact callout preserved; no deterministic mapping."
        material.resolution_confidence = "UNKNOWN"
        material.ambiguities.append(
            "Material identity needs an authoritative mapping or manual confirmation."
        )
        return material
    if rule is None:
        material.status = FieldStatus.NEEDS_REVIEW
        material.allowance_class = None
        material.resolved_identity = raw
        material.supplier_description = None
        material.supplier_search_terms = {}
        material.resolution_basis = "Callout matches more than one material family."
        material.resolution_confidence = "LOW"
        material.ambiguities.append("Material callout spans different material families.")
        return material

    condition, temper_source = _condition(raw)
    return _apply_resolution(
        material,
        shape,
        rule=rule,
        grades=grades,
        metadata_raw=raw,
        resolution_basis="Deterministic mapping from the agreed drawing callout.",
        condition=condition,
        temper_source=temper_source,
    )
