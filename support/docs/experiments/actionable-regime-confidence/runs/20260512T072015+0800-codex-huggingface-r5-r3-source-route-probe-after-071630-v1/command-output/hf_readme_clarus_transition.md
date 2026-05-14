---
language:
  - en
license: mit
pretty_name: Market Regime Transition Breakpoint Mapping v0.1
dataset_name: market-regime-transition-breakpoint-mapping-v0.1
tags:
  - clarusc64
  - markets
  - regime
  - transition
  - macro
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

## What this dataset tests

Whether a system can map regime transitions  
before price confirms them.

Markets move between structural basins.  
This dataset identifies  
- current regime  
- adjacent regimes  
- triggers  
- transition probabilities  

## Required outputs

- current regime basin  
- adjacent regime targets  
- trigger condition set  
- transition probability 24h  
- transition probability 72h  
- projected post-shift structure  

## Why it matters

Most systems detect regimes after they move.  
This dataset evaluates whether a system can detect  
the next regime before the shift.

## Evaluation focus

High scores require  
- explicit regime basin  
- explicit transition targets  
- numeric probabilities  
- clear trigger conditions  
