"""
Main orchestrator for the damage claim verification system.
"""

import pandas as pd
import logging
import time
from pathlib import Path
from tqdm import tqdm
from typing import Dict, Any, List
import json

from claim_parser import ClaimParser
from image_analyzer import ImageAnalyzer
from risk_engine import RiskEngine
from decision_engine import DecisionEngine
from config import OUTPUT_CSV, BATCH_SIZE, REQUESTS_PER_MINUTE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClaimVerificationSystem:
    """Main system orchestrator."""
    
    def __init__(self):
        self.parser = ClaimParser()
        self.image_analyzer = ImageAnalyzer(use_cache=True)
        self.risk_engine = RiskEngine()
        self.decision_engine = DecisionEngine(self.parser)
        
        # Statistics
        self.stats = {
            'total_claims': 0,
            'processed_claims': 0,
            'api_calls': 0,
            'total_images': 0,
            'start_time': None,
            'end_time': None
        }
    
    def load_data(self):
        """Load all required data."""
        logger.info("Loading data...")
        self.parser.load_data()
        return self.parser
    
    def process_claim(self, row: pd.Series) -> Dict[str, Any]:
        """
        Process a single claim.
        
        Args:
            row: Pandas row from claims.csv
        
        Returns:
            Output dictionary
        """
        claim_object = row['claim_object']
        user_id = row['user_id']
        user_claim = row['user_claim']
        image_paths_str = row['image_paths']
        
        # Parse image paths
        image_paths = self.parser.get_image_paths_for_claim(row)
        self.stats['total_images'] += len(image_paths)
        
        # Get user history
        user_history = self.parser.get_user_history(user_id)
        
        # Analyze images
        if image_paths:
            analysis = self.image_analyzer.analyze_images(
                image_paths, claim_object, user_claim
            )
            self.stats['api_calls'] += 1
        else:
            analysis = {
                'object_visible': 'no',
                'issue_type': 'unknown',
                'claim_match': 'not_enough_information',
                'severity': 'unknown',
                'supporting_images': [],
                'reasoning': 'No images provided',
                'image_count': 0,
                'image_quality_flags': ['manual_review_required']
            }
        
        # Add claim_object to analysis for evidence check
        analysis['claim_object'] = claim_object
        
        # Evaluate risk
        risk_flags = self.risk_engine.evaluate(analysis, user_history)
        analysis['risk_flags'] = risk_flags
        
        # Make decision
        claim_dict = row.to_dict()
        output = self.decision_engine.process_claim(
            claim_dict, analysis, user_history
        )
        
        self.stats['processed_claims'] += 1
        
        return output
    
    def process_claims(self, claims_df: pd.DataFrame, 
                      use_tqdm: bool = True) -> List[Dict[str, Any]]:
        """
        Process all claims in the dataframe.
        
        Args:
            claims_df: Dataframe with claims
            use_tqdm: Show progress bar
        
        Returns:
            List of output dictionaries
        """
        self.stats['start_time'] = time.time()
        self.stats['total_claims'] = len(claims_df)
        
        results = []
        iterator = tqdm(claims_df.iterrows(), total=len(claims_df)) if use_tqdm else claims_df.iterrows()
        
        for idx, row in iterator:
            try:
                output = self.process_claim(row)
                results.append(output)
                
                # Rate limiting
                if self.stats['api_calls'] % BATCH_SIZE == 0:
                    time.sleep(60 / REQUESTS_PER_MINUTE)
                    
            except Exception as e:
                logger.error(f"Error processing claim {idx}: {e}")
                # Create fallback output
                fallback = {
                    'user_id': row.get('user_id', ''),
                    'image_paths': row.get('image_paths', ''),
                    'user_claim': row.get('user_claim', ''),
                    'claim_object': row.get('claim_object', 'unknown'),
                    'evidence_standard_met': False,
                    'evidence_standard_met_reason': f"Processing error: {str(e)[:100]}",
                    'risk_flags': 'manual_review_required',
                    'issue_type': 'unknown',
                    'object_part': 'unknown',
                    'claim_status': 'not_enough_information',
                    'claim_status_justification': f"Error processing claim: {str(e)[:100]}",
                    'supporting_image_ids': 'none',
                    'valid_image': False,
                    'severity': 'unknown'
                }
                results.append(fallback)
        
        self.stats['end_time'] = time.time()
        return results
    
    def generate_output(self, results: List[Dict[str, Any]], output_path: Path = OUTPUT_CSV):
        """Generate output CSV from results."""
        df = pd.DataFrame(results)
        
        # Ensure correct column order
        columns = [
            'user_id', 'image_paths', 'user_claim', 'claim_object',
            'evidence_standard_met', 'evidence_standard_met_reason',
            'risk_flags', 'issue_type', 'object_part',
            'claim_status', 'claim_status_justification',
            'supporting_image_ids', 'valid_image', 'severity'
        ]
        
        # Add missing columns
        for col in columns:
            if col not in df.columns:
                df[col] = None
        
        df = df[columns]
        df.to_csv(output_path, index=False)
        logger.info(f"Output saved to {output_path}")
        
        return df
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        elapsed = self.stats['end_time'] - self.stats['start_time'] if self.stats['end_time'] else 0
        
        return {
            'total_claims': self.stats['total_claims'],
            'processed_claims': self.stats['processed_claims'],
            'api_calls': self.stats['api_calls'],
            'total_images': self.stats['total_images'],
            'elapsed_seconds': round(elapsed, 2),
            'claims_per_second': round(self.stats['processed_claims'] / elapsed if elapsed > 0 else 0, 2)
        }


def main():
    """Main entry point."""
    logger.info("=" * 80)
    logger.info("Damage Claim Verification System")
    logger.info("=" * 80)
    
    # Check API key
    from config import OPENAI_API_KEY, ANTHROPIC_API_KEY, USE_OPENAI
    
    if USE_OPENAI and not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set. Please set it in .env file.")
        return
    elif not USE_OPENAI and not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set. Please set it in .env file.")
        return
    
    # Initialize system
    system = ClaimVerificationSystem()
    
    # Load data
    parser = system.load_data()
    
    # Get dataframes
    sample_claims_df = parser.sample_claims_df
    test_claims_df = parser.claims_df
    
    # Process sample claims (for evaluation)
    logger.info("\n" + "-" * 40)
    logger.info("Processing sample claims for evaluation...")
    sample_results = system.process_claims(sample_claims_df)
    sample_df = system.generate_output(sample_results, Path("output_sample.csv"))
    
    # Log sample stats
    sample_stats = system.get_stats()
    logger.info(f"Sample processing complete: {sample_stats}")
    
    # Reset stats for test claims
    system.stats = {'total_claims': 0, 'processed_claims': 0, 'api_calls': 0, 
                   'total_images': 0, 'start_time': None, 'end_time': None}
    
    # Process test claims
    logger.info("\n" + "-" * 40)
    logger.info("Processing test claims...")
    test_results = system.process_claims(test_claims_df)
    test_df = system.generate_output(test_results, OUTPUT_CSV)
    
    # Log test stats
    test_stats = system.get_stats()
    logger.info(f"Test processing complete: {test_stats}")
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("Processing Summary")
    logger.info("=" * 80)
    logger.info(f"Total claims processed: {test_stats['total_claims']}")
    logger.info(f"Total API calls: {test_stats['api_calls']}")
    logger.info(f"Total images analyzed: {test_stats['total_images']}")
    logger.info(f"Processing time: {test_stats['elapsed_seconds']} seconds")
    logger.info(f"Output saved to: {OUTPUT_CSV}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()