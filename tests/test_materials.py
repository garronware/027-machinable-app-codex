"""Offline tests for conservative material and supplier-intent resolution."""

from backend.domain.materials import resolve_material
from backend.domain.models import (
    FieldCandidate,
    FieldResult,
    FieldStatus,
    MaterialCandidate,
    MaterialClassification,
    MaterialResult,
)


def _shape(value: str = "ROUND") -> FieldResult:
    return FieldResult(
        status=FieldStatus.RESOLVED,
        value=value,
        candidates=[
            FieldCandidate(
                reader_model="test",
                value=value,
                evidence=[],
                uncertainty=None,
            )
        ],
        reasons=[],
    )


def _material(
    raw_callout: str,
    classification: MaterialClassification = MaterialClassification.NOT_FOUND,
) -> MaterialResult:
    return MaterialResult(
        status=FieldStatus.RESOLVED,
        raw_callout=raw_callout,
        raw_callout_evidence=["Drawing material note"],
        canonical_grade=None,
        standard_system=None,
        material_family=None,
        temper_or_condition=None,
        specification=None,
        resolved_identity=raw_callout,
        supplier_description=None,
        supplier_search_terms={},
        allowance_class=(
            classification
            if classification is not MaterialClassification.NOT_FOUND
            else None
        ),
        resolution_basis=None,
        resolution_confidence="UNKNOWN",
        ambiguities=[],
        temper_source=None,
        temper_confirmation_required=False,
        sources=[],
        candidates=[
            MaterialCandidate(
                reader_model="test",
                raw_callout=raw_callout,
                allowance_class=classification,
                evidence=["Drawing material note"],
            )
        ],
    )


def test_explicit_aluminum_grade_and_temper_become_supplier_language():
    result = resolve_material(_material("6061-T6 ALUM"), _shape())

    assert result.allowance_class is MaterialClassification.ALUMINUM
    assert result.canonical_grade == "6061"
    assert result.temper_or_condition == "T6"
    assert result.resolved_identity == "6061-T6 Aluminum Alloy"
    assert result.supplier_description == "6061-T6 Aluminum Alloy Round Bar"
    assert result.temper_confirmation_required is False


def test_missing_temper_is_not_silently_invented():
    result = resolve_material(_material("6061 Aluminum"), _shape("FLAT"))

    assert result.resolved_identity == "6061 Aluminum Alloy"
    assert "T6" not in (result.supplier_description or "")
    assert result.temper_confirmation_required is True


def test_multiple_accepted_grades_are_preserved_as_a_menu():
    result = resolve_material(_material("4130/4140 Steel, Normalized"), _shape())

    assert result.allowance_class is MaterialClassification.ALLOY_STEEL
    assert result.canonical_grade == "4130 / 4140"
    assert "4130 / 4140" in (result.supplier_description or "")


def test_1018_is_classified_as_carbon_steel():
    result = resolve_material(_material("1018 Mild Steel"), _shape("FLAT"))

    assert result.allowance_class is MaterialClassification.CARBON_STEEL
    assert result.resolved_identity == "1018 Carbon Steel"


def test_a2_tool_steel_is_customer_identity_not_internal_class_name():
    result = resolve_material(
        _material("ALLOY TOOL STEEL, A2 PER ASTM-A-681"), _shape()
    )

    assert result.resolved_identity == "A2 Tool Steel"
    assert result.supplier_description == "A2 Tool Steel Round Bar"
    assert result.allowance_class is MaterialClassification.TOOL_STEEL


def test_a2_is_selected_from_allowed_high_speed_or_a2_tool_steel_clause():
    result = resolve_material(
        _material(
            "HIGH SPEED TOOL STEEL, M1 OR M2 PER ASTM A600 OR "
            "ALLOY TOOL STEEL, A2 PER ASTM A681"
        ),
        _shape(),
    )

    assert result.canonical_grade == "A2"
    assert result.resolved_identity == "A2 Tool Steel"


def test_proprietary_numeric_code_remains_useful_but_unresolved():
    result = resolve_material(
        _material("31011", MaterialClassification.ALUMINUM), _shape()
    )

    assert result.status is FieldStatus.RESOLVED
    assert result.raw_callout == "31011"
    assert result.resolved_identity == "31011"
    assert result.allowance_class is None
    assert result.supplier_description is None
    assert result.ambiguities
