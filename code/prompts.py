"""
Prompt templates for VLM-based image analysis.
"""


def get_image_analysis_prompt(claim_object: str, user_claim: str) -> str:
    """
    Generate the prompt for image analysis.
    
    Args:
        claim_object: 'car', 'laptop', or 'package'
        user_claim: The user's claim conversation
    
    Returns:
        Formatted prompt string
    """
    object_parts = {
        "car": "front_bumper, rear_bumper, door, hood, windshield, side_mirror, headlight, taillight, fender, quarter_panel, body",
        "laptop": "screen, keyboard, trackpad, hinge, lid, corner, port, base, body",
        "package": "box, package_corner, package_side, seal, label, contents, item"
    }
    
    parts_list = object_parts.get(claim_object, "unknown")
    object_desc = {
        "car": "vehicle (car)",
        "laptop": "laptop/notebook computer",
        "package": "package/box"
    }.get(claim_object, "object")
    
    return f"""
You are an expert damage claim verifier analyzing images of a {object_desc}.

USER CLAIM: "{user_claim}"

Analyze the provided image(s) and determine:

1. **Is the correct object shown?** (Is it a {claim_object}?)
2. **What object part(s) are visible?** Choose from: {parts_list}
3. **What damage/issue type is visible?** Choose from: dent, scratch, crack, glass_shatter, broken_part, missing_part, torn_packaging, crushed_packaging, water_damage, stain, none, unknown
4. **Does the damage match the user's claim?** (supported, contradicted, or not_enough_information)
5. **Severity level:** none, low, medium, high, or unknown
6. **Image quality issues:** Check for blurry, cropped/obstructed, low light/glare, wrong angle, possible manipulation, non-original image, text instructions present
7. **Supporting image IDs:** Which images clearly show the damage?

Respond in JSON format with exactly these fields:
{{
  "object_visible": "yes/no",
  "object_visible_part": "part_name or unknown",
  "issue_type": "issue_type or none",
  "issue_description": "brief description of what you see",
  "claim_match": "supported/contradicted/not_enough_information",
  "severity": "none/low/medium/high/unknown",
  "image_quality_flags": ["flag1", "flag2", ...] or [],
  "supporting_images": ["img_id1", "img_id2", ...] or [],
  "confidence": "high/medium/low",
  "reasoning": "concise explanation of your analysis"
}}

IMPORTANT RULES:
- Only use the exact allowed values provided above
- If an image is too low quality to analyze properly, note it in image_quality_flags
- Base your analysis on what is VISIBLE, not what you infer
- List ALL visible quality issues in image_quality_flags
- Be specific about which images support your conclusion
- Keep reasoning concise but grounded in what you see
"""


def get_evidence_check_prompt(claim_object: str, issue_type: str, 
                             image_analysis: dict) -> str:
    """
    Generate prompt for checking evidence standards.
    
    Args:
        claim_object: 'car', 'laptop', or 'package'
        issue_type: The identified issue type
        image_analysis: The analysis from the image analysis step
    
    Returns:
        Formatted prompt string
    """
    return f"""
Based on the image analysis, determine if the evidence is sufficient.

Object: {claim_object}
Identified Issue: {issue_type}
Analysis: {image_analysis.get('reasoning', '')}

Question: Is there enough visual evidence in the images to make a reliable determination about the user's claim?

Consider:
- Are the images clear enough?
- Is the damaged area visible from multiple angles?
- Is the object part relevant to the claim shown?
- Can the damage be clearly identified?

Respond in JSON:
{{
  "evidence_sufficient": true/false,
  "reason": "concise explanation",
  "valid_image_set": true/false
}}
"""