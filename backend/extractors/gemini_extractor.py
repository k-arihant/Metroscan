"""
Gemini Semantic Extractor.
Uses gemini-2.0-flash (with gemini-1.5-flash as fallback) via the official google-genai SDK
for structured semantic extraction of packaged commodity label fields.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Union
from google import genai
from google.genai import types

from backend.extractors.prompt import EXTRACTION_SYSTEM_INSTRUCTION, build_user_prompt

logger = logging.getLogger(__name__)

_MODEL_FALLBACK_CHAIN = [
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-flash-latest",
    "gemini-3.5-flash",
]


def _build_fallback_result(ocr_dict: dict) -> Dict[str, Any]:
    raw_texts = []
    detections = ocr_dict.get("detections", [])
    for d in detections:
        t = d.get("text", "")
        if t:
            raw_texts.append(t)

    return {
        "package_id": ocr_dict.get("package_id", "unknown"),
        "fields": {
            "manufacturer_packer_importer": None,
            "generic_common_name": None,
            "net_quantity": None,
            "manufacturing_packing_import_date": None,
            "mrp": None,
            "best_before_expiry": None,
            "consumer_care": None,
            "country_of_origin": None,
            "unit_sale_price": None,
        },
        "field_details": {
            "mrp": {"numeric_value": None, "currency": "INR", "tax_inclusive_mentioned": False},
            "net_quantity": {"numeric_value": None, "unit": None},
        },
        "evidence": {
            k: {"raw_source_text": None, "detection_id": None}
            for k in [
                "manufacturer_packer_importer", "generic_common_name", "net_quantity",
                "manufacturing_packing_import_date", "mrp", "best_before_expiry",
                "consumer_care", "country_of_origin", "unit_sale_price",
            ]
        },
        "unclassified_text": raw_texts,
        "_gemini_unavailable": True,
    }


class GeminiSemanticExtractor:
    def __init__(self, api_key: str = None):
        raw_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.api_key = raw_key.strip().strip('"').strip("'") if raw_key else ""
        self._client = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY is not set. Please provide a valid Gemini API key.")
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _call_model(self, model_name: str, user_content: str) -> Dict[str, Any]:
        response = self.client.models.generate_content(
            model=model_name,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=EXTRACTION_SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()
        return json.loads(raw_text)

    def _enrich_evidence(self, result: Dict[str, Any], ocr_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich semantic evidence items with the spatial bounding box, source image ID,
        and OCR confidence from matching raw OCR detections.
        """
        if not isinstance(result, dict) or "evidence" not in result:
            return result

        detections = ocr_dict.get("detections", [])
        det_map = {}
        for d in detections:
            if isinstance(d, dict) and d.get("detection_id"):
                det_map[d["detection_id"]] = d

        evidence = result.get("evidence", {})
        if isinstance(evidence, dict):
            for field_key, ev in evidence.items():
                if isinstance(ev, dict) and ev.get("detection_id"):
                    det_id = ev["detection_id"]
                    if det_id in det_map:
                        matched = det_map[det_id]
                        if not ev.get("bounding_box"):
                            ev["bounding_box"] = matched.get("bounding_box")
                        if not ev.get("source_image_id"):
                            ev["source_image_id"] = matched.get("source_image_id")
                        if not ev.get("ocr_confidence"):
                            ev["ocr_confidence"] = matched.get("confidence")

        return result

    def extract(self, ocr_data: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
        if hasattr(ocr_data, "model_dump"):
            ocr_dict = ocr_data.model_dump()
        else:
            ocr_dict = ocr_data

        user_content = build_user_prompt(ocr_dict)

        last_error = None
        for model_name in _MODEL_FALLBACK_CHAIN:
            for attempt in range(2):
                try:
                    logger.info("Gemini extraction trying %s (attempt %d)...", model_name, attempt + 1)
                    result = self._call_model(model_name, user_content)
                    result = self._enrich_evidence(result, ocr_dict)
                    logger.info("Gemini extraction succeeded with %s", model_name)
                    return result
                except Exception as e:
                    err_msg = str(e)
                    last_error = e
                    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                        logger.warning("Model %s hit quota (429), trying next model in chain...", model_name)
                        break  # try next model in chain
                    if "503" in err_msg or "UNAVAILABLE" in err_msg or "high demand" in err_msg:
                        logger.warning("Model %s returned 503, retrying...", model_name)
                        time.sleep(2)
                        continue
                    logger.warning("Model %s failed (%s), trying next...", model_name, e)
                    break

        logger.error("All Gemini models failed (%s). Using fallback result.", last_error)
        fallback = _build_fallback_result(ocr_dict)
        return self._enrich_evidence(fallback, ocr_dict)

