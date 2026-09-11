"""
Strict Schema Definition and Validation for Standardized Compliance OCR Output.

Enforces:
1. All required top-level keys: package_id, processing, images, detections, extracted_fields, compliance_summary.
2. All required image-level metadata: image_id, filename, dimensions, image_quality, calibration, principal_display_panel.
3. All required detection-level keys: detection_id, source_image_id, text, normalized_text, confidence,
   ocr_metadata, detection_type, bounding_box, layout, field, font_metrics, physical_metrics, rule_7.
4. Value enums and constraints (detection_type, rule_7 statuses, bounding_box non-negativity).
5. Raises descriptive ValidationError on any structural violation before file writes.
"""
from typing import Dict, Any, List, Tuple, Set


VALID_DETECTION_TYPES: Set[str] = {
    "text",
    "numeric",
    "date",
    "barcode",
    "qr",
    "mixed",
    "unknown",
}

VALID_RULE_7_STATUSES: Set[str] = {
    "COMPLIANT",
    "NON_COMPLIANT",
    "UNABLE_TO_VERIFY",
}

VALID_VERIFICATION_STATUSES: Set[str] = {
    "VERIFIED",
    "UNABLE_TO_VERIFY",
}

VALID_LAYOUT_ROLES: Set[str] = {
    "label",
    "value",
    "heading",
    "body",
    "unknown",
}

REQUIRED_TOP_LEVEL_KEYS: Set[str] = {
    "package_id",
    "processing",
    "images",
    "detections",
    "extracted_fields",
    "compliance_summary",
}

REQUIRED_PROCESSING_KEYS: Set[str] = {
    "pipeline_version",
    "timestamp",
    "ocr_status",
}

REQUIRED_IMAGE_KEYS: Set[str] = {
    "image_id",
    "filename",
    "label_side",
    "width",
    "height",
    "image_quality",
    "calibration",
    "principal_display_panel",
}

REQUIRED_IMAGE_QUALITY_KEYS: Set[str] = {
    "quality_score",
    "blur_score",
    "resolution_sufficient",
    "orientation_corrected",
    "deskew_applied",
}

REQUIRED_CALIBRATION_KEYS: Set[str] = {
    "available",
    "pixels_per_mm",
    "source",
    "confidence",
}

REQUIRED_PDP_KEYS: Set[str] = {
    "detected",
    "width_px",
    "height_px",
    "width_cm",
    "height_cm",
    "area_cm2",
    "measurement_source",
    "confidence",
}

REQUIRED_DETECTION_KEYS: Set[str] = {
    "detection_id",
    "source_image_id",
    "text",
    "normalized_text",
    "confidence",
    "ocr_metadata",
    "detection_type",
    "bounding_box",
    "layout",
    "field",
    "font_metrics",
    "physical_metrics",
    "rule_7",
}

REQUIRED_OCR_METADATA_KEYS: Set[str] = {
    "engine",
    "pass",
    "preprocessing",
    "source",
}

REQUIRED_BOUNDING_BOX_KEYS: Set[str] = {
    "x",
    "y",
    "width",
    "height",
}

REQUIRED_LAYOUT_KEYS: Set[str] = {
    "column",
    "row",
    "role",
    "layout_confidence",
}

REQUIRED_FIELD_KEYS: Set[str] = {
    "predicted",
    "candidate",
    "field_confidence",
}

REQUIRED_FONT_METRICS_KEYS: Set[str] = {
    "measurement_available",
    "character_height_px",
    "character_widths_px",
    "minimum_character_width_px",
    "width_height_ratio",
    "measurement_confidence",
}

REQUIRED_PHYSICAL_METRICS_KEYS: Set[str] = {
    "measurement_available",
    "character_height_mm",
    "minimum_character_width_mm",
}

REQUIRED_RULE_7_KEYS: Set[str] = {
    "applicable",
    "verification_status",
    "required_character_height_mm",
    "measured_character_height_mm",
    "height_status",
    "minimum_width_height_ratio",
    "measured_width_height_ratio",
    "width_status",
    "overall_status",
    "confidence",
    "reason",
}

REQUIRED_COMPLIANCE_SUMMARY_KEYS: Set[str] = {
    "verified",
    "compliant",
    "non_compliant",
    "unable_to_verify",
    "rule_7",
}

REQUIRED_RULE_7_SUMMARY_KEYS: Set[str] = {
    "status",
    "verified",
    "compliant",
    "non_compliant",
    "unable_to_verify",
    "detections_evaluated",
    "detections_compliant",
    "detections_non_compliant",
    "detections_unable_to_verify",
}



class SchemaValidationError(ValueError):
    """Raised when structured OCR output fails compliance schema validation."""
    def __init__(self, errors: List[str]):
        self.errors = errors
        message = f"Schema validation failed with {len(errors)} error(s):\n" + "\n".join(f" - {e}" for e in errors[:10])
        if len(errors) > 10:
            message += f"\n ... and {len(errors) - 10} more."
        super().__init__(message)


def validate_output_schema(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a dictionary against the standardized compliance OCR schema.
    Returns: (is_valid, list_of_errors)
    """
    errors: List[str] = []

    if not isinstance(data, dict):
        return False, ["Root object must be a dictionary."]

    # 1. Top-Level Keys
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in data:
            errors.append(f"Missing required top-level key: '{key}'")

    if errors:
        return False, errors

    # 2. Processing
    proc = data.get("processing")
    if not isinstance(proc, dict):
        errors.append("'processing' must be a dictionary.")
    else:
        for pk in REQUIRED_PROCESSING_KEYS:
            if pk not in proc:
                errors.append(f"Missing in processing: '{pk}'")

    # 3. Images
    imgs = data.get("images")
    if not isinstance(imgs, list) or len(imgs) == 0:
        errors.append("'images' must be a non-empty list of image objects.")
    else:
        for idx, img in enumerate(imgs):
            if not isinstance(img, dict):
                errors.append(f"images[{idx}] must be a dictionary.")
                continue
            for ik in REQUIRED_IMAGE_KEYS:
                if ik not in img:
                    errors.append(f"Missing in images[{idx}]: '{ik}'")

            # Image Quality
            iq = img.get("image_quality")
            if not isinstance(iq, dict):
                errors.append(f"images[{idx}]['image_quality'] must be a dictionary.")
            else:
                for qk in REQUIRED_IMAGE_QUALITY_KEYS:
                    if qk not in iq:
                        errors.append(f"Missing in images[{idx}]['image_quality']: '{qk}'")

            # Calibration
            cal = img.get("calibration")
            if not isinstance(cal, dict):
                errors.append(f"images[{idx}]['calibration'] must be a dictionary.")
            else:
                for ck in REQUIRED_CALIBRATION_KEYS:
                    if ck not in cal:
                        errors.append(f"Missing in images[{idx}]['calibration']: '{ck}'")

            # PDP
            pdp = img.get("principal_display_panel")
            if not isinstance(pdp, dict):
                errors.append(f"images[{idx}]['principal_display_panel'] must be a dictionary.")
            else:
                for dk in REQUIRED_PDP_KEYS:
                    if dk not in pdp:
                        errors.append(f"Missing in images[{idx}]['principal_display_panel']: '{dk}'")

    # 4. Detections
    dets = data.get("detections")
    if not isinstance(dets, list):
        errors.append("'detections' must be a list.")
    else:
        for idx, det in enumerate(dets):
            if not isinstance(det, dict):
                errors.append(f"detections[{idx}] must be a dictionary.")
                continue

            det_id = det.get("detection_id", f"idx_{idx}")
            for dk in REQUIRED_DETECTION_KEYS:
                if dk not in det:
                    errors.append(f"Missing in detection '{det_id}': '{dk}'")

            # Detection type
            dtype = det.get("detection_type")
            if dtype not in VALID_DETECTION_TYPES:
                errors.append(f"Detection '{det_id}' has invalid detection_type '{dtype}'. Expected one of {sorted(VALID_DETECTION_TYPES)}.")

            # Bounding Box
            bbox = det.get("bounding_box")
            if not isinstance(bbox, dict):
                errors.append(f"Detection '{det_id}' bounding_box must be a dictionary.")
            else:
                for bk in REQUIRED_BOUNDING_BOX_KEYS:
                    if bk not in bbox:
                        errors.append(f"Detection '{det_id}' bounding_box missing '{bk}'")

            # OCR Metadata
            ometa = det.get("ocr_metadata")
            if not isinstance(ometa, dict):
                errors.append(f"Detection '{det_id}' ocr_metadata must be a dictionary.")
            else:
                for ok in REQUIRED_OCR_METADATA_KEYS:
                    if ok not in ometa:
                        errors.append(f"Detection '{det_id}' ocr_metadata missing '{ok}'")

            # Layout
            lay = det.get("layout")
            if not isinstance(lay, dict):
                errors.append(f"Detection '{det_id}' layout must be a dictionary.")
            else:
                for lk in REQUIRED_LAYOUT_KEYS:
                    if lk not in lay:
                        errors.append(f"Detection '{det_id}' layout missing '{lk}'")
                role = lay.get("role")
                if role is not None and role not in VALID_LAYOUT_ROLES:
                    errors.append(f"Detection '{det_id}' has invalid layout role '{role}'. Expected one of {sorted(VALID_LAYOUT_ROLES)} or null.")

            # Field
            fld = det.get("field")
            if not isinstance(fld, dict):
                errors.append(f"Detection '{det_id}' field must be a dictionary.")
            else:
                for fk in REQUIRED_FIELD_KEYS:
                    if fk not in fld:
                        errors.append(f"Detection '{det_id}' field missing '{fk}'")

            # Font Metrics
            fm = det.get("font_metrics")
            if not isinstance(fm, dict):
                errors.append(f"Detection '{det_id}' font_metrics must be a dictionary.")
            else:
                for fmk in REQUIRED_FONT_METRICS_KEYS:
                    if fmk not in fm:
                        errors.append(f"Detection '{det_id}' font_metrics missing '{fmk}'")

            # Physical Metrics
            pm = det.get("physical_metrics")
            if not isinstance(pm, dict):
                errors.append(f"Detection '{det_id}' physical_metrics must be a dictionary.")
            else:
                for pmk in REQUIRED_PHYSICAL_METRICS_KEYS:
                    if pmk not in pm:
                        errors.append(f"Detection '{det_id}' physical_metrics missing '{pmk}'")

            # Rule 7
            r7 = det.get("rule_7")
            if not isinstance(r7, dict):
                errors.append(f"Detection '{det_id}' rule_7 must be a dictionary.")
            else:
                for rk in REQUIRED_RULE_7_KEYS:
                    if rk not in r7:
                        errors.append(f"Detection '{det_id}' rule_7 missing '{rk}'")

                v_status = r7.get("verification_status")
                if v_status not in VALID_VERIFICATION_STATUSES:
                    errors.append(f"Detection '{det_id}' has invalid rule_7.verification_status '{v_status}'.")

                o_status = r7.get("overall_status")
                if o_status not in VALID_RULE_7_STATUSES:
                    errors.append(f"Detection '{det_id}' has invalid rule_7.overall_status '{o_status}'.")

                h_status = r7.get("height_status")
                if h_status not in VALID_RULE_7_STATUSES:
                    errors.append(f"Detection '{det_id}' has invalid rule_7.height_status '{h_status}'.")

                w_status = r7.get("width_status")
                if w_status not in VALID_RULE_7_STATUSES:
                    errors.append(f"Detection '{det_id}' has invalid rule_7.width_status '{w_status}'.")

    # 5. Extracted Fields
    ef = data.get("extracted_fields")
    if not isinstance(ef, dict):
        errors.append("'extracted_fields' must be a dictionary.")

    # 6. Compliance Summary
    cs = data.get("compliance_summary")
    if not isinstance(cs, dict):
        errors.append("'compliance_summary' must be a dictionary.")
    else:
        for csk in REQUIRED_COMPLIANCE_SUMMARY_KEYS:
            if csk not in cs:
                errors.append(f"Missing in compliance_summary: '{csk}'")
        r7_sum = cs.get("rule_7")
        if not isinstance(r7_sum, dict):
            errors.append("compliance_summary['rule_7'] must be a dictionary.")
        else:
            for rsk in REQUIRED_RULE_7_SUMMARY_KEYS:
                if rsk not in r7_sum:
                    errors.append(f"Missing in compliance_summary['rule_7']: '{rsk}'")
            sum_status = r7_sum.get("status")
            if sum_status not in VALID_RULE_7_STATUSES:
                errors.append(f"compliance_summary['rule_7'].status '{sum_status}' is invalid.")

    return len(errors) == 0, errors


def validate_or_raise(data: Dict[str, Any]) -> None:
    """Validate data against schema, raising SchemaValidationError on failure."""
    is_valid, errors = validate_output_schema(data)
    if not is_valid:
        raise SchemaValidationError(errors)
