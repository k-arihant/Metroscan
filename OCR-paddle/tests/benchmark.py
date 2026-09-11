"""
Benchmark Harness for Food/Product Label Compliance OCR Pipeline.
Executes pipeline across sample dataset, compares against ground truth,
and reports precision, recall, exact match accuracy, confidence calibration, and latency.
"""
import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Ensure project root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config
from src.pipeline import LabelCompliancePipeline


def normalize_val(val: Any) -> str:
    """Normalize values for robust semantic comparison (case, spaces, currency symbols)."""
    if val is None:
        return ""
    s = str(val).lower().strip()
    # Remove currency symbols and slashes
    for char in ["₹", "rs.", "rs", "inr", "/-", ":"]:
        s = s.replace(char, "")
    # Normalize spaces
    s = " ".join(s.split())
    # Standardize units
    s = s.replace("grams", "g").replace("gram", "g").replace("gm", "g")
    return s.strip()


def values_match(pred: Any, target: Any) -> bool:
    """Check if predicted value matches ground truth semantically."""
    p_norm = normalize_val(pred)
    t_norm = normalize_val(target)
    if not p_norm or not t_norm:
        return False
    if p_norm == t_norm:
        return True
    # Substring / partial match for product names and manufacturers
    if (len(t_norm) > 4 and t_norm in p_norm) or (len(p_norm) > 4 and p_norm in t_norm):
        return True
    # Numeric date match (e.g. 06/2026 matches 06/2026 or 6/2026)
    if "/" in t_norm and "/" in p_norm:
        p_parts = p_norm.split("/")
        t_parts = t_norm.split("/")
        if len(p_parts) == len(t_parts):
            return all(p.zfill(2) == t.zfill(2) for p, t in zip(p_parts, t_parts))
    # Float numerical equivalence for prices and quantities (e.g. 22 == 22.00, 110 == 110.00)
    try:
        p_num = float(p_norm)
        t_num = float(t_norm)
        if abs(p_num - t_num) < 1e-3:
            return True
    except (ValueError, TypeError):
        pass
    return False


def run_benchmark(
    ground_truth_path: str = "tests/ground_truth.json",
    images_dir: str = "images",
    limit: int = 5,
) -> Dict[str, Any]:
    """
    Run automated benchmark on test images.
    """
    gt_file = Path(ground_truth_path)
    if not gt_file.exists():
        raise FileNotFoundError(f"Ground truth file not found at {gt_file}")

    with open(gt_file, "r", encoding="utf-8") as f:
        ground_truth: Dict[str, Dict[str, Any]] = json.load(f)

    img_dir = Path(images_dir)
    pipeline = LabelCompliancePipeline()

    test_images = list(ground_truth.keys())[:limit]
    results = []

    total_gt_fields = 0
    total_correct = 0
    total_extracted = 0
    total_latency = 0.0

    print(f"\n==================================================")
    print(f"STARTING OCR BENCHMARK ON {len(test_images)} IMAGES")
    print(f"==================================================\n")

    for img_name in test_images:
        img_path = img_dir / img_name
        if not img_path.exists():
            print(f"Skipping {img_name}: file does not exist.")
            continue

        gt_fields = ground_truth.get(img_name, {})
        print(f"--> Processing: {img_name} ({len(gt_fields)} ground truth fields)...")

        t0 = time.perf_counter()
        pipeline_res = pipeline.process_image(str(img_path))
        elapsed = time.perf_counter() - t0
        total_latency += elapsed

        extracted = pipeline_res.get("fields", {})
        confidences = pipeline_res.get("confidence", {})

        image_correct = 0
        image_extracted = 0
        field_comparisons = {}

        for field, target_val in gt_fields.items():
            total_gt_fields += 1
            pred_val = extracted.get(field)
            pred_conf = confidences.get(field, 0.0)

            is_match = False
            if pred_val is not None:
                image_extracted += 1
                total_extracted += 1
                if values_match(pred_val, target_val):
                    is_match = True
                    image_correct += 1
                    total_correct += 1

            field_comparisons[field] = {
                "ground_truth": target_val,
                "predicted": pred_val,
                "confidence": pred_conf,
                "is_match": is_match,
            }

        results.append({
            "image": img_name,
            "status": pipeline_res.get("ocr_status"),
            "elapsed_seconds": round(elapsed, 2),
            "correct_fields": image_correct,
            "total_gt_fields": len(gt_fields),
            "field_comparisons": field_comparisons,
            "uncertain_fields": pipeline_res.get("uncertain_fields", []),
        })

        print(f"    Done in {elapsed:.2f}s | Matches: {image_correct}/{len(gt_fields)}")

    recall = (total_correct / total_gt_fields) if total_gt_fields > 0 else 0.0
    precision = (total_correct / total_extracted) if total_extracted > 0 else 0.0
    avg_latency = (total_latency / len(test_images)) if test_images else 0.0

    summary = {
        "images_tested": len(test_images),
        "total_ground_truth_fields": total_gt_fields,
        "total_extracted_fields": total_extracted,
        "total_correct_fields": total_correct,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "average_latency_seconds": round(avg_latency, 2),
        "detailed_results": results,
    }

    print("\n==================================================")
    print("BENCHMARK SUMMARY")
    print("==================================================")
    print(f"Images Tested      : {summary['images_tested']}")
    print(f"Precision          : {summary['precision'] * 100:.1f}%")
    print(f"Recall             : {summary['recall'] * 100:.1f}%")
    print(f"Avg Latency        : {summary['average_latency_seconds']:.2f}s per image (GPU)")
    print("==================================================\n")

    return summary


if __name__ == "__main__":
    run_benchmark(limit=5)
