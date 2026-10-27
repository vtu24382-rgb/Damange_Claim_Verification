"""
Risk engine for evaluating risk flags from user history and image quality.
"""

from typing import Dict, List, Any
from config import RISK_FLAGS


class RiskEngine:
    """Evaluate risk flags for claims."""
    
    def __init__(self):
        self.risk_flags = set()
    
    def evaluate_user_history_risk(self, user_history: Dict[str, Any]) -> List[str]:
        """Evaluate risk from user history."""
        flags = []
        
        if not user_history:
            return flags
        
        # Check claim counts - ensure we convert to int
        try:
            past_count = int(user_history.get('past_claim_count', 0))
            if past_count > 5:
                flags.append('user_history_risk')
        except (ValueError, TypeError):
            pass
        
        # Check recent claims
        try:
            recent_count = int(user_history.get('last_90_days_claim_count', 0))
            if recent_count > 3:
                flags.append('user_history_risk')
        except (ValueError, TypeError):
            pass
        
        # Check for manual review flag
        try:
            manual_review = int(user_history.get('manual_review_claim', 0))
            if manual_review > 0:
                flags.append('manual_review_required')
        except (ValueError, TypeError):
            pass
        
        # Check rejections
        try:
            rejected = int(user_history.get('rejected_claim', 0))
            if rejected > 2:
                flags.append('user_history_risk')
        except (ValueError, TypeError):
            pass
        
        # Check history flags
        history_flags = user_history.get('history_flags', '')
        if history_flags and isinstance(history_flags, str):
            for flag in history_flags.split(';'):
                if flag.strip() in RISK_FLAGS:
                    flags.append(flag.strip())
        
        return flags
    
    def evaluate_image_quality_flags(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Extract image quality flags from analysis."""
        flags = []
        
        quality_flags = analysis_result.get('image_quality_flags', [])
        if quality_flags:
            for flag in quality_flags:
                if flag in RISK_FLAGS:
                    flags.append(flag)
        
        # Additional checks
        if analysis_result.get('object_visible') == 'no':
            flags.append('damage_not_visible')
        
        if analysis_result.get('confidence') == 'low':
            flags.append('manual_review_required')
        
        # Check for claim mismatch
        if analysis_result.get('claim_match') == 'contradicted':
            flags.append('claim_mismatch')
        
        return list(set(flags))  # Remove duplicates
    
    def combine_risk_flags(self, user_flags: List[str], 
                          image_flags: List[str]) -> str:
        """Combine user and image risk flags."""
        all_flags = set(user_flags + image_flags)
        
        # Filter out duplicates and sort
        sorted_flags = sorted(all_flags)
        
        if not sorted_flags:
            return "none"
        
        # Ensure 'none' is not mixed with other flags
        if "none" in sorted_flags and len(sorted_flags) > 1:
            sorted_flags.remove("none")
        
        return ";".join(sorted_flags)
    
    def evaluate(self, analysis_result: Dict[str, Any], 
                user_history: Dict[str, Any]) -> str:
        """
        Evaluate all risk factors for a claim.
        
        Returns:
            Semicolon-separated risk flags or "none"
        """
        user_flags = self.evaluate_user_history_risk(user_history)
        image_flags = self.evaluate_image_quality_flags(analysis_result)
        
        return self.combine_risk_flags(user_flags, image_flags)