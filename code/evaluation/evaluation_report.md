# Evaluation Report

## System Overview
- **Evaluation Date**: 2026-06-19 23:33:55
- **Sample Claims Evaluated**: 20
- **Model Used**: gpt-4o

## Performance Metrics

### Classification Accuracy
| Metric | Score |
|--------|-------|
| Claim Status Accuracy | 0.7 |
| Issue Type Accuracy | 0.45 |
| Object Part Accuracy | 0.0 |
| Severity Accuracy | 0.2 |
| Evidence Standard Accuracy | 0.8 |
| **Overall Score** | **0.43** |

### Detailed Classification Reports

#### Claim Status
```
                        precision    recall  f1-score   support

          contradicted       0.33      0.20      0.25         5
not_enough_information       0.00      0.00      0.00         2
             supported       0.76      1.00      0.87        13

              accuracy                           0.70        20
             macro avg       0.37      0.40      0.37        20
          weighted avg       0.58      0.70      0.63        20

```

#### Issue Type
```
                   precision    recall  f1-score   support

      broken_part       0.00      0.00      0.00         3
            crack       0.67      0.67      0.67         3
crushed_packaging       0.00      0.00      0.00         1
             dent       0.75      1.00      0.86         3
             none       0.00      0.00      0.00         2
          scratch       0.50      1.00      0.67         2
            stain       0.50      1.00      0.67         1
   torn_packaging       0.50      1.00      0.67         1
          unknown       0.00      0.00      0.00         3
     water_damage       0.00      0.00      0.00         1

         accuracy                           0.45        20
        macro avg       0.29      0.47      0.35        20
     weighted avg       0.31      0.45      0.36        20

```

#### Object Part
```
                precision    recall  f1-score   support

           box       0.00      0.00      0.00       0.0
      contents       0.00      0.00      0.00       1.0
        corner       0.00      0.00      0.00       1.0
          door       0.00      0.00      0.00       1.0
  front_bumper       0.00      0.00      0.00       2.0
     headlight       0.00      0.00      0.00       1.0
         hinge       0.00      0.00      0.00       1.0
          hood       0.00      0.00      0.00       0.0
      keyboard       0.00      0.00      0.00       1.0
         label       0.00      0.00      0.00       0.0
           lid       0.00      0.00      0.00       0.0
package_corner       0.00      0.00      0.00       1.0
  package_side       0.00      0.00      0.00       1.0
   rear_bumper       0.00      0.00      0.00       2.0
        screen       0.00      0.00      0.00       2.0
          seal       0.00      0.00      0.00       2.0
   side_mirror       0.00      0.00      0.00       1.0
      trackpad       0.00      0.00      0.00       1.0
       unknown       0.00      0.00      0.00       1.0
    windshield       0.00      0.00      0.00       1.0

      accuracy                           0.00      20.0
     macro avg       0.00      0.00      0.00      20.0
  weighted avg       0.00      0.00      0.00      20.0

```

## Operational Analysis

### API Usage
- **Sample Processing API Calls**: 20
- **Test Processing API Calls**: 44
- **Total Images Processed**: 82

### Performance
- **Processing Time**: 7.00 seconds
- **Images per Second**: 11.70
- **Claims per Minute**: 548.00

### Rate Limiting Strategy
- **Requests per Minute**: 60 (configurable)
- **Batch Size**: 10
- **Retry Attempts**: 3
- **Cache Enabled**: True

## Recommendations
- Consider using more diverse prompts for claim status classification
- Improve image quality assessment or use multiple angles
- Add more specific object detection or part segmentation

## Conclusion
The system demonstrates 43.0% overall accuracy on sample claims.
The system needs further refinement to meet production standards.

---
*Report generated automatically by the evaluation system.*