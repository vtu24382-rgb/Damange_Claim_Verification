"""
Claims parser module for loading and validating CSV data.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import logging
from config import (
    CLAIMS_CSV, SAMPLE_CLAIMS_CSV, USER_HISTORY_CSV, 
    EVIDENCE_REQUIREMENTS_CSV, OBJECT_TYPE_PARTS,
    IMAGES_SAMPLE, IMAGES_TEST, DATASET_PATH
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClaimParser:
    """Parse and validate claim data from CSV files."""
    
    def __init__(self):
        self.claims_df = None
        self.sample_claims_df = None
        self.user_history = None
        self.evidence_requirements = None
        self.user_history_lookup = {}
        self.evidence_lookup = {}
    
    def load_data(self):
        """Load all CSV files."""
        logger.info("Loading dataset files...")
        
        # Load claims
        self.claims_df = pd.read_csv(CLAIMS_CSV)
        logger.info(f"Loaded {len(self.claims_df)} claims from claims.csv")
        
        # Load sample claims
        self.sample_claims_df = pd.read_csv(SAMPLE_CLAIMS_CSV)
        logger.info(f"Loaded {len(self.sample_claims_df)} sample claims")
        
        # Load user history
        self.user_history = pd.read_csv(USER_HISTORY_CSV)
        self._build_user_history_lookup()
        logger.info(f"Loaded {len(self.user_history)} user history records")
        
        # Load evidence requirements
        self.evidence_requirements = pd.read_csv(EVIDENCE_REQUIREMENTS_CSV)
        self._build_evidence_lookup()
        logger.info(f"Loaded {len(self.evidence_requirements)} evidence requirements")
        
        return {
            "claims": self.claims_df,
            "sample": self.sample_claims_df,
            "user_history": self.user_history,
            "evidence": self.evidence_requirements
        }
    
    def _build_user_history_lookup(self):
        """Build a dictionary for quick user history lookup."""
        for _, row in self.user_history.iterrows():
            user_id = row['user_id']
            self.user_history_lookup[user_id] = row.to_dict()
    
    def _build_evidence_lookup(self):
        """Build a dictionary for evidence requirements lookup."""
        for _, row in self.evidence_requirements.iterrows():
            key = (row['claim_object'], row['applies_to'])
            self.evidence_lookup[key] = row['minimum_image_evidence']
    
    def get_user_history(self, user_id: str) -> Dict:
        """Get user history for a given user_id."""
        return self.user_history_lookup.get(user_id, {})
    
    def get_evidence_requirement(self, claim_object: str, issue_type: str) -> int:
        """
        Get minimum evidence requirement for a claim_object and issue_type.
        
        Matches by claim_object and applies_to (issue family).
        """
        # Check for specific match
        for (obj, applies_to), min_evidence in self.evidence_lookup.items():
            if obj == claim_object and issue_type in applies_to:
                return min_evidence
            if obj == "all" and issue_type in applies_to:
                return min_evidence
        # Default minimum
        return 1
    
    def parse_image_paths(self, image_paths_str: str) -> List[str]:
        """Parse semicolon-separated image paths."""
        if pd.isna(image_paths_str) or not image_paths_str:
            return []
        return [p.strip() for p in image_paths_str.split(';') if p.strip()]
    
    def get_image_id(self, image_path: str) -> str:
        """Extract image ID from file path."""
        return Path(image_path).stem
    
    def get_image_paths_for_claim(self, claim_row: pd.Series) -> List[str]:
        """
        Get full image paths for a claim row.
        
        Handles various path formats:
        - "case_001/img_1.jpg"
        - "img_1.jpg" (looks up in case folder based on row index)
        - "sample/case_001/img_1.jpg"
        - "images/sample/case_001/img_1.jpg"
        """
        image_paths_str = claim_row['image_paths']
        if pd.isna(image_paths_str) or not image_paths_str:
            return []
        
        paths = self.parse_image_paths(image_paths_str)
        abs_paths = []
        
        # Determine if this is a sample claim or test claim
        is_sample = False
        if self.sample_claims_df is not None:
            # Check if this claim exists in sample claims
            user_id = claim_row.get('user_id', '')
            if user_id:
                sample_users = set(self.sample_claims_df['user_id'].values)
                if user_id in sample_users:
                    is_sample = True
        
        # If we can't determine from user_id, check the row index
        if not is_sample and self.claims_df is not None:
            # Check if this is from the claims dataframe
            if claim_row.name is not None:
                # If we're processing claims.csv, use test folder
                is_sample = False
        
        base_path = IMAGES_SAMPLE if is_sample else IMAGES_TEST
        
        for p in paths:
            p = p.strip()
            
            # Check if the path already has a folder structure
            if '/' in p or '\\' in p:
                # Clean up the path
                # Remove common prefixes
                if p.startswith('dataset/'):
                    p = p.replace('dataset/', '')
                if p.startswith('images/'):
                    p = p.replace('images/', '')
                if p.startswith('sample/'):
                    p = p.replace('sample/', '')
                if p.startswith('test/'):
                    p = p.replace('test/', '')
                
                # Now p should be like "case_001/img_1.jpg" or just "img_1.jpg"
                if 'case_' in p:
                    # Has case folder - use as-is
                    abs_path = base_path / p
                else:
                    # Just a filename - need to find the case folder
                    # Use the row index to determine case number
                    idx = claim_row.name
                    if idx is not None:
                        case_num = idx + 1
                        abs_path = base_path / f"case_{case_num:03d}" / p
                    else:
                        # Fallback - look in the base path directly
                        abs_path = base_path / p
            else:
                # Just a filename like "img_1.jpg"
                # Use the row index to find the case folder
                idx = claim_row.name
                if idx is not None and idx >= 0:
                    case_num = idx + 1
                    abs_path = base_path / f"case_{case_num:03d}" / p
                else:
                    # Fallback - look in the base path directly
                    abs_path = base_path / p
            
            abs_paths.append(str(abs_path))
        
        # If no paths were resolved, try a different approach
        if not abs_paths:
            # Try to find images in the base path
            for p in paths:
                p = p.strip()
                # Try to find the image in any case folder
                if base_path.exists():
                    for case_folder in base_path.glob("case_*"):
                        img_path = case_folder / Path(p).name
                        if img_path.exists():
                            abs_paths.append(str(img_path))
                            break
                    else:
                        # Not found - just use base path
                        abs_paths.append(str(base_path / Path(p).name))
        
        return abs_paths
    
    def get_issue_family(self, issue_type: str) -> str:
        """Get the issue family for an issue type."""
        family_map = {
            "dent": "dent or scratch",
            "scratch": "dent or scratch",
            "crack": "crack",
            "glass_shatter": "glass_shatter",
            "broken_part": "broken_part",
            "missing_part": "missing_part",
            "torn_packaging": "torn_packaging",
            "crushed_packaging": "crushed_packaging",
            "water_damage": "water_damage",
            "stain": "stain",
            "none": "none",
            "unknown": "unknown"
        }
        return family_map.get(issue_type, issue_type)


# Global parser instance
parser = ClaimParser()