---
language:
  - en
license: mit
pretty_name: Market Regime Coherence Mapping v0.1
dataset_name: market-regime-coherence-mapping-v0.1
tags:
  - clarusc64
  - markets
  - macro
  - regime
  - cross-asset
task_categories:
  - tabular-classification
size_categories:
  - 1K<n<10K
configs:
  - config_name: default
    data_files:
      - split: train
        path: data/train.csv
      - split: test
        path: data/test.csv
---

What this dataset tests

Whether a system can identify the current market regime  
based on relationships between assets.

Not price prediction.  
Structure detection.

Required outputs

- regime coherence score  
- dominant driver label  
- cross-asset alignment index  
- dispersion vs concentration index  
- regime stability band  

Constraints

Use relationships across assets  
not single-asset forecasts.

Evaluation focus

High scores require  
- numeric indices  
- explicit regime driver  
- explicit stability band  
- internal consistency across outputs
