"""
Decision engine for making final claim decisions.
"""

from typing import Dict, Any, List
import logging
from config import CLAIM_STATUS_VALUES, OBJECT_TYPE_PARTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DecisionEngine:
    """Make final decisions on claims."""
    
    def __init__(self, parser):
        self.parser = parser
    
    def determine_evidence_standard(self, analysis_result: Dict[str, Any]) -> tuple:
        """
        Determine if evidence standard is met.
        
        Returns:
            (evidence_standard_met, evidence_standard_met_reason)
        """
        issue_type = analysis_result.get('issue_type', 'unknown')
        claim_object = analysis_result.get('claim_object', 'unknown')
        
        # Get minimum evidence requirement
        min_evidence = self.parser.get_evidence_requirement(claim_object, issue_type)
        
        # Get actual image count
        image_count = analysis_result.get('image_count', 0)
        supporting_images = analysis_result.get('supporting_images', [])
        
        # Ensure min_evidence is an integer
        try:
            min_evidence = int(min_evidence)
        except (ValueError, TypeError):
            min_evidence = 1
        
        # Check if we have enough images
        if image_count < min_evidence:
            return False, f"Need at least {min_evidence} image(s), got {image_count}"
        
        # Check if supporting images exist
        if not supporting_images:
            return False, "No supporting images identified"
        
        # Check image quality
        quality_flags = analysis_result.get('image_quality_flags', [])
        if 'blurry_image' in quality_flags or 'low_light_or_glare' in quality_flags:
            return False, "Image quality insufficient for reliable analysis"
        
        # Check if object is visible
        if analysis_result.get('object_visible') == 'no':
            return False, "Required object not clearly visible in images"
        
        return True, f"Evidence standard met with {len(supporting_images)} supporting image(s)"
    
    def determine_claim_status(self, analysis_result: Dict[str, Any]) -> tuple:
        """
        Determine claim status.
        
        Returns:
            (claim_status, claim_status_justification)
        """
        claim_match = analysis_result.get('claim_match', 'not_enough_information')
        issue_type = analysis_result.get('issue_type', 'unknown')
        reasoning = analysis_result.get('reasoning', '')
        supporting_images = analysis_result.get('supporting_images', [])
        
        # If no supporting images, status can't be supported
        if not supporting_images and claim_match == 'supported':
            claim_match = 'not_enough_information'
        
        # Validate status
        if claim_match not in CLAIM_STATUS_VALUES:
            claim_match = 'not_enough_information'
        
        # Build justification
        if claim_match == 'supported':
            justification = f"Image evidence supports the claim of {issue_type}. {reasoning}"
            if supporting_images:
                img_ids = ';'.join(supporting_images[:3])
                justification += f" Supporting images: {img_ids}"
        elif claim_match == 'contradicted':
            justification = f"Image evidence contradicts the claim. {reasoning}"
        else:
            justification = f"Insufficient evidence to determine claim. {reasoning}"
        
        return claim_match, justification
    
    def validate_values(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean all output values."""
        
        # Validate issue_type
        valid_issue_types = ['dent', 'scratch', 'crack', 'glass_shatter', 
                            'broken_part', 'missing_part', 'torn_packaging', 
                            'crushed_packaging', 'water_damage', 'stain', 
                            'none', 'unknown']
        if output.get('issue_type') not in valid_issue_types:
            output['issue_type'] = 'unknown'
        
        # Validate claim_status
        if output.get('claim_status') not in CLAIM_STATUS_VALUES:
            output['claim_status'] = 'not_enough_information'
        
        # Validate severity
        valid_severity = ['none', 'low', 'medium', 'high', 'unknown']
        if output.get('severity') not in valid_severity:
            output['severity'] = 'unknown'
        
        # Validate object_part based on claim_object
        claim_object = output.get('claim_object', 'unknown')
        object_parts = OBJECT_TYPE_PARTS.get(claim_object, ['unknown'])
        if output.get('object_part') not in object_parts:
            output['object_part'] = 'unknown'
        
        # Ensure supporting_image_ids is properly formatted
        supporting = output.get('supporting_image_ids', 'none')
        if isinstance(supporting, list):
            supporting = ';'.join(supporting) if supporting else 'none'
        if not supporting or supporting == []:
            supporting = 'none'
        output['supporting_image_ids'] = supporting
        
        # Ensure risk_flags
        risk_flags = output.get('risk_flags', 'none')
        if not risk_flags or risk_flags == '' or risk_flags == []:
            output['risk_flags'] = 'none'
        
        # Ensure valid_image
        valid_image = output.get('valid_image')
        if valid_image is None:
            output['valid_image'] = True
        
        return output
    
    def process_claim(self, claim_row: Dict[str, Any], 
                     analysis_result: Dict[str, Any],
                     user_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single claim and produce output.
        
        Args:
            claim_row: Original claim data
            analysis_result: Result from image analysis
            user_history: User history data
        
        Returns:
            Output dictionary with all required fields
        """
        # Determine evidence standard
        evidence_met, evidence_reason = self.determine_evidence_standard(analysis_result)
        
        # Determine claim status
        claim_status, justification = self.determine_claim_status(analysis_result)
        
        # Get supporting images
        supporting_images = analysis_result.get('supporting_images', [])
        if isinstance(supporting_images, list):
            supporting_images_str = ';'.join(supporting_images) if supporting_images else 'none'
        else:
            supporting_images_str = str(supporting_images) if supporting_images else 'none'
        
        # Build output
        output = {
            'user_id': str(claim_row.get('user_id', '')),
            'image_paths': str(claim_row.get('image_paths', '')),
            'user_claim': str(claim_row.get('user_claim', '')),
            'claim_object': str(claim_row.get('claim_object', 'unknown')),
            'evidence_standard_met': bool(evidence_met),
            'evidence_standard_met_reason': str(evidence_reason),
            'risk_flags': str(analysis_result.get('risk_flags', 'none')),
            'issue_type': str(analysis_result.get('issue_type', 'unknown')),
            'object_part': str(analysis_result.get('object_part', 'unknown')),
            'claim_status': str(claim_status),
            'claim_status_justification': str(justification),
            'supporting_image_ids': supporting_images_str,
            'valid_image': self._determine_valid_image(analysis_result),
            'severity': str(analysis_result.get('severity', 'unknown'))
        }
        
        # Validate and clean
        return self.validate_values(output)
    
    def _determine_valid_image(self, analysis_result: Dict[str, Any]) -> bool:
        """Determine if image set is valid for automated review."""
        quality_flags = analysis_result.get('image_quality_flags', [])
        
        # Image is invalid if:
        # 1. Object not visible
        if analysis_result.get('object_visible') == 'no':
            return False
        
        # 2. Major quality issues
        invalid_flags = ['blurry_image', 'low_light_or_glare', 'possible_manipulation',
                        'non_original_image', 'cropped_or_obstructed']
        
        for flag in quality_flags:
            if flag in invalid_flags and flag != 'manual_review_required':
                return False
        
        # 3. No images
        if analysis_result.get('image_count', 0) == 0:
            return False
        
        return True