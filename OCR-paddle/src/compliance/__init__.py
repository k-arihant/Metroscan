"""
Compliance verification package for Legal Metrology Packaged Commodity Rules.
"""
from src.compliance.rule_7 import (
    evaluate_rule_7_for_detection,
    summarize_rule_7_compliance,
    get_required_character_height,
    get_rule_7_threshold,
    Rule7Evaluation,
    RULE_7_HEIGHT_TABLE,
    MIN_WIDTH_HEIGHT_RATIO,
    NARROW_CHARACTER_EXCEPTIONS,
)

