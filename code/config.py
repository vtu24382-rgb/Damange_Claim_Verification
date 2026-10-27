"""
Configuration module for the damage claim verification system.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATASET_PATH = PROJECT_ROOT / "dataset"
CODE_PATH = PROJECT_ROOT / "code"
EVALUATION_PATH = CODE_PATH / "evaluation"

# CSV paths
CLAIMS_CSV = DATASET_PATH / "claims.csv"
SAMPLE_CLAIMS_CSV = DATASET_PATH / "sample_claims.csv"
USER_HISTORY_CSV = DATASET_PATH / "user_history.csv"
EVIDENCE_REQUIREMENTS_CSV = DATASET_PATH / "evidence_requirements.csv"
OUTPUT_CSV = PROJECT_ROOT / "output.csv"

# Image paths
IMAGES_SAMPLE = DATASET_PATH / "images" / "sample"
IMAGES_TEST = DATASET_PATH / "images" / "test"

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Choose your model
# Options: "gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet-20241022"
VISION_MODEL = os.getenv("VISION_MODEL", "gpt-4o")
USE_OPENAI = VISION_MODEL.startswith("gpt-")
USE_ANTHROPIC = VISION_MODEL.startswith("claude-")

# Model parameters
TEMPERATURE = 0.1  # Low temperature for consistent results
MAX_TOKENS = 1000

# Rate limiting
REQUESTS_PER_MINUTE = 60  # Adjust based on your API tier
BATCH_SIZE = 10
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2  # seconds

# Cache settings
CACHE_ENABLED = True
CACHE_DIR = CODE_PATH / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

# Allowed values for validation
CLAIM_STATUS_VALUES = ["supported", "contradicted", "not_enough_information"]
ISSUE_TYPES = [
    "dent", "scratch", "crack", "glass_shatter", "broken_part", 
    "missing_part", "torn_packaging", "crushed_packaging", 
    "water_damage", "stain", "none", "unknown"
]
CAR_PARTS = [
    "front_bumper", "rear_bumper", "door", "hood", "windshield",
    "side_mirror", "headlight", "taillight", "fender", 
    "quarter_panel", "body", "unknown"
]
LAPTOP_PARTS = [
    "screen", "keyboard", "trackpad", "hinge", "lid", "corner",
    "port", "base", "body", "unknown"
]
PACKAGE_PARTS = [
    "box", "package_corner", "package_side", "seal", "label",
    "contents", "item", "unknown"
]
RISK_FLAGS = [
    "blurry_image", "cropped_or_obstructed", "low_light_or_glare",
    "wrong_angle", "wrong_object", "wrong_object_part",
    "damage_not_visible", "claim_mismatch", "possible_manipulation",
    "non_original_image", "text_instruction_present",
    "user_history_risk", "manual_review_required"
]

OBJECT_TYPE_PARTS = {
    "car": CAR_PARTS,
    "laptop": LAPTOP_PARTS,
    "package": PACKAGE_PARTS
}