"""
Inference script for the MedLIP 80-Diseases Classifier.
Usage (CLI):
    python inference.py path/to/image.jpg
    python inference.py path/to/image.jpg --threshold 0.15 --top_k 10
Usage (Python API):
    from inference import DiseaseClassifier
    classifier = DiseaseClassifier("model.pt", "disease_names.csv")
    results = classifier.classify("path/to/image.jpg")
    # [{"name": "Melanoma or Melanoma Mimickers", "score": 0.85}, ...]
"""

import os
import cv2
import numpy as np
import pandas as pd
import torch
from PIL import Image

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# ============== Image preprocessing ==============

_IMAGENET_MEAN = np.array([0.485, 0.456, 0.406])
_IMAGENET_STD = np.array([0.229, 0.224, 0.225])


def _resize_and_pad(img, max_size=480):
    """Resize image so longest side = max_size, then pad to square."""
    if img.shape[0] > max_size or img.shape[1] > max_size:
        scale = max_size / max(img.shape[0], img.shape[1])
        h = int(img.shape[0] * scale)
        w = int(img.shape[1] * scale)
        img = cv2.resize(img, (w, h))
    h, w, _ = img.shape
    top = (max_size - h) // 2
    bottom = max_size - (h + top)
    left = (max_size - w) // 2
    right = max_size - (w + left)
    img = cv2.copyMakeBorder(
        img, top, bottom, left, right, borderType=cv2.BORDER_CONSTANT
    )
    return img


def _prepare_input(img, model_size=448):
    """Preprocess image: resize, pad, normalize, return single-image batch tensor."""
    img = _resize_and_pad(img, model_size)
    img = img / 255.0
    img = (img - _IMAGENET_MEAN) / _IMAGENET_STD
    return torch.tensor(img.transpose(2, 0, 1)).float().unsqueeze(0).to(device)


# ============== Classifier ==============

class DiseaseClassifier:
    """80-classes diseases classifier powered by MedLIP.
    Args:
        model_path: Path to the TorchScript model file (model.pt).
        disease_names_path: Path to the CSV file with a 'Class' column
                            listing disease names (disease_names.csv).
    Example:
        classifier = DiseaseClassifier("model.pt", "disease_names.csv")
        results = classifier.classify("lesion_photo.jpg")
        for r in results:
            print(f"{r['name']}: {r['score']:.3f}")
    """

    def __init__(self, model_path: str, disease_names_path: str):
        self.model = torch.jit.load(model_path, map_location=device)
        self.model.to(device)
        self.model.eval()

        df = pd.read_csv(disease_names_path)
        self.disease_names = df["Class"].values.tolist()

    def classify(
        self,
        image,
        score_threshold: float = 0.3,
        top_k: int = 5,
    ) -> list:
        """Classify a dermatological image.
        Args:
            image: File path (str), PIL Image, or numpy array (H x W x 3, RGB).
            score_threshold: Minimum sigmoid score to include in results.
            top_k: Maximum number of results to return.
        Returns:
            List of dicts [{"name": str, "score": float}] sorted by score descending.
        """
        if isinstance(image, str):
            image = np.array(Image.open(image).convert("RGB"))
        elif isinstance(image, Image.Image):
            image = np.array(image.convert("RGB"))

        image_input = _prepare_input(image, model_size=448)

        with torch.no_grad():
            pred = self.model(image_input)
            scores = torch.sigmoid(pred).mean(dim=0).cpu().numpy()

        predictions = [
            {"name": name, "score": float(round(float(score), 3))}
            for name, score in zip(self.disease_names, scores)
            if score >= score_threshold
        ]
        predictions.sort(key=lambda x: x["score"], reverse=True)
        return predictions[:top_k]


# ============== CLI ==============

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MedLIP 80-Diseases Classifier")
    parser.add_argument("image", help="Path to the input image")
    parser.add_argument(
        "--model", default=None,
        help="Path to model.pt (default: model.pt in the same directory as this script)",
    )
    parser.add_argument(
        "--diseases", default=None,
        help="Path to disease_names.csv (default: disease_names.csv in the same directory)",
    )
    parser.add_argument(
        "--threshold", type=float, default=0.3,
        help="Minimum score threshold (default: 0.3)",
    )
    parser.add_argument(
        "--top_k", type=int, default=5,
        help="Maximum number of results to display (default: 5)",
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = args.model or os.path.join(script_dir, "model.pt")
    diseases_path = args.diseases or os.path.join(script_dir, "disease_names.csv")

    print(f"Device : {device}")
    print(f"Model  : {model_path}")
    print(f"Loading model...", end=" ", flush=True)
    classifier = DiseaseClassifier(model_path, diseases_path)
    print("done.")

    print(f"Image  : {args.image}")
    results = classifier.classify(args.image, score_threshold=args.threshold, top_k=args.top_k)

    if results:
        print(f"\nTop predictions (score >= {args.threshold}):")
        for r in results:
            print(f"  {r['score']:.3f}  {r['name']}")
    else:
        print("\nNo predictions above threshold.")