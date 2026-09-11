"""
OCR Result Aggregator: Multi-pass merging, consensus scoring, confidence calibration, and spatial line clustering.
"""
from typing import List, Dict, Tuple, Optional
import numpy as np
from src.ocr.engine_manager import OCRBox
from src.utils.geometry import BoundingBox, calculate_iou, distance_between, is_horizontally_aligned


def cluster_into_lines(boxes: List[OCRBox], max_v_diff_ratio: float = 0.5) -> List[OCRBox]:
    """
    Cluster word-level OCR boxes that reside on the same horizontal line into line-level phrases.
    Preserves precise bounding box spanning all words in the line.
    """
    if not boxes:
        return []

    # Sort boxes primarily by y_min, secondarily by x_min
    sorted_boxes = sorted(boxes, key=lambda b: (b.bbox.y_min, b.bbox.x_min))

    lines: List[List[OCRBox]] = []
    for box in sorted_boxes:
        placed = False
        for line in lines:
            # Check against reference box in current line
            ref_box = line[0]
            avg_height = (ref_box.bbox.height + box.bbox.height) / 2.0
            if avg_height == 0:
                continue

            v_diff = abs(ref_box.bbox.center_y - box.bbox.center_y)
            if v_diff <= avg_height * max_v_diff_ratio:
                line.append(box)
                placed = True
                break

        if not placed:
            lines.append([box])

    # For each line, sort words left-to-right and construct merged OCRBox
    merged_lines: List[OCRBox] = []
    for line in lines:
        line_sorted = sorted(line, key=lambda b: b.bbox.x_min)
        full_text = " ".join(b.text for b in line_sorted)

        x_min = min(b.bbox.x_min for b in line_sorted)
        y_min = min(b.bbox.y_min for b in line_sorted)
        x_max = max(b.bbox.x_max for b in line_sorted)
        y_max = max(b.bbox.y_max for b in line_sorted)

        # Confidence is mean of individual word confidences
        mean_conf = float(np.mean([b.confidence for b in line_sorted]))
        engines = ",".join(sorted(set(b.engine for b in line_sorted)))
        variants = ",".join(sorted(set(b.variant for b in line_sorted)))

        merged_box = OCRBox(
            text=full_text,
            bbox=BoundingBox(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max),
            confidence=mean_conf,
            engine=engines,
            variant=variants,
            raw_detection=line_sorted,
        )
        merged_lines.append(merged_box)

    return merged_lines


def aggregate_ocr_results(pass_results: List[List[OCRBox]]) -> Tuple[List[OCRBox], List[OCRBox]]:
    """
    Aggregate results from multiple OCR passes.
    Returns:
        (aggregated_words, aggregated_lines)
    """
    all_boxes: List[OCRBox] = []
    for pass_boxes in pass_results:
        all_boxes.extend(pass_boxes)

    if not all_boxes:
        return [], []

    # Consensus matching across passes
    # Find matching/overlapping boxes from different passes and evaluate agreement
    merged_words: List[OCRBox] = []
    used_indices = set()

    for i, box_i in enumerate(all_boxes):
        if i in used_indices:
            continue

        cluster = [box_i]
        used_indices.add(i)

        for j, box_j in enumerate(all_boxes):
            if j in used_indices:
                continue

            iou = calculate_iou(box_i.bbox, box_j.bbox)
            dist = distance_between(box_i.bbox, box_j.bbox)
            avg_h = (box_i.bbox.height + box_j.bbox.height) / 2.0

            # Overlap criteria: either high IoU or very close center distance within line height
            if iou > 0.30 or (dist < max(15.0, avg_h * 0.7)):
                cluster.append(box_j)
                used_indices.add(j)

        if len(cluster) == 1:
            merged_words.append(box_i)
        else:
            # Multiple passes detected this region
            # Check for textual agreement
            texts = [b.text.strip().lower() for b in cluster]
            from collections import Counter
            counts = Counter(texts)
            most_common_text, match_count = counts.most_common(1)[0]

            # Select the original case-preserved box matching most_common_text
            matching_boxes = [b for b in cluster if b.text.strip().lower() == most_common_text]
            best_box = max(matching_boxes, key=lambda b: b.confidence)

            # Consensus boost: if multiple passes agree, boost confidence
            agreement_ratio = match_count / len(cluster)
            if match_count >= 2:
                boosted_conf = min(0.99, best_box.confidence + (0.12 * agreement_ratio))
            else:
                # Disagreement across passes slightly penalizes raw confidence
                boosted_conf = max(0.20, best_box.confidence * 0.90)

            merged_word = OCRBox(
                text=best_box.text,
                bbox=best_box.bbox,
                confidence=boosted_conf,
                engine=",".join(sorted(set(b.engine for b in cluster))),
                variant=",".join(sorted(set(b.variant for b in cluster))),
                raw_detection=cluster,
            )
            merged_words.append(merged_word)

    # Sort merged words in reading order
    sorted_words = sorted(merged_words, key=lambda b: (b.bbox.y_min, b.bbox.x_min))
    # Cluster into coherent line phrases
    merged_lines = cluster_into_lines(sorted_words)

    return sorted_words, merged_lines
