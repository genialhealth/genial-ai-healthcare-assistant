---
license: apache-2.0
tags:
  - medical
  - image-classification
  - clinically visible disease
  - torchscript
pipeline_tag: image-classification
---

# Medsiglip 80-Disease Classifier

A dermatological image classifier that recognizes **80 disease categories** using a MedSiglip-based vision backbone exported as TorchScript.

## Files

| File | Description |
|------|-------------|
| `model.pt` | TorchScript model (CPU/GPU compatible) |
| `disease_names.csv` | 80 class labels |
| `inference.py` | Ready-to-use inference script |
| `requirements.txt` | Python dependencies |

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Clone the repo (or download files manually)

```bash
git lfs install
git clone https://huggingface.co/genial-team/medsiglip-80-diseases-classifier
cd medsiglip-80-diseases-classifier
```

### 3. Run from command line

```bash
python inference.py path/to/lesion_image.jpg
```

Optional flags:

```bash
python inference.py path/to/lesion_image.jpg --threshold 0.3 --top_k 10
```

Example output:

```
Device : cpu
Model  : model.pt
Loading model... done.
Image  : lesion_image.jpg

Top predictions (score >= 0.3):
  0.812  Melanocytic Nevus
  0.431  Melanoma
  0.378  Benign Keratinocytic Lesions and Lentigines
```

### 4. Python API

```python
from inference import DiseaseClassifier

classifier = DiseaseClassifier("model.pt", "disease_names.csv")

# accepts a file path, PIL Image, or numpy RGB array
results = classifier.classify("photo_lesion.jpg", score_threshold=0.3, top_k=5)

for r in results:
    print(f"{r['name']}: {r['score']:.3f}")
```

## Supported Disease Classes

The model outputs a probability score (sigmoid) for each of the 80 classes listed in `disease_names.csv`. A non-exhaustive sample:

- Infestation
- Diabetes
- Bowen Disease - Squamous Cell Carcinoma in Situ 
- Hyperpigmentation 
- Lichen Planus
- Hypopigmentation
- Melanoma
- Actinic Keratosis
- Dermatomyositis
- Hair Diseases
- Leprosy
- … and 69 more (see `disease_names.csv`)

## Input Requirements

| Property | Value |
|----------|-------|
| Input type | RGB image (any size) |
| Internal resolution | 448 × 448 (auto-padded) |
| Normalization | ImageNet mean/std |
| Output | 80-dim logit vector → sigmoid scores |

## Inference Notes

- The model is exported with **TorchScript** (`torch.jit.load`) — no model source code required.
- Runs on **CPU or GPU** automatically.
- `score_threshold=0.3` is a reasonable default; lower it to see more candidates.
- Scores are **independent sigmoid probabilities**, not a softmax — multiple classes can score high simultaneously (multi-label setting).

## Citation

If you use this model in your work, please cite the original Medgemma paper and this repository.

## License

Apache 2.0
