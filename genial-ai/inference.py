"""
Inference module for the Genial Team AI MedLIP 80-Diseases Classifier.

This module provides the core logic for loading a TorchScript model and performing
multi-class classification on medical images.
"""

import os
import cv2
import numpy as np
import pandas as pd
import torch
from PIL import Image
from typing import List, Dict, Union, Any

# Determine the best available device for computation
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# ============== Image preprocessing constants ==============

_IMAGENET_MEAN = np.array([0.485, 0.456, 0.406])
_IMAGENET_STD = np.array([0.229, 0.224, 0.225])


def _resize_and_pad(img: np.ndarray, max_size: int = 480) -> np.ndarray:
    """Resizes an image maintaining aspect ratio and pads it to a square.

    Args:
        img: The input image as a numpy array (H, W, C).
        max_size: The target size for the longest side of the image.

    Returns:
        A square numpy array padded with black borders.
    """
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


def _prepare_input(img: np.ndarray, model_size: int = 448) -> torch.Tensor:
    """Preprocesses a raw image for model inference.

    Includes resizing, padding, normalization, and tensor conversion.

    Args:
        img: The input RGB image as a numpy array.
        model_size: The expected input size for the model.

    Returns:
        A 4D torch tensor (1, C, H, W) ready for inference on the selected device.
    """
    img = _resize_and_pad(img, model_size)
    img = img / 255.0
    img = (img - _IMAGENET_MEAN) / _IMAGENET_STD
    return torch.tensor(img.transpose(2, 0, 1)).float().unsqueeze(0).to(device)


# ============== Classifier ==============

class DiseaseClassifier:
    """80-classes diseases classifier powered by MedLIP.

    This class handles the loading of the TorchScript model and provides an
    interface for classifying images against 80 disease classes.

    Attributes:
        model: The loaded TorchScript model.
        disease_names: A list of disease names corresponding to the model output.
    """

    def __init__(self, model_path: str, disease_names_path: str):
        """Initializes the classifier by loading the model and labels.

        Args:
            model_path: Path to the TorchScript model file (model.pt).
            disease_names_path: Path to the CSV file containing labels.
        """
        self.model = torch.jit.load(model_path, map_location=device)
        self.model.to(device)
        self.model.eval()

        df = pd.read_csv(disease_names_path)
        self.disease_names = df["Class"].values.tolist()

    def classify(
        self,
        image: Union[str, Image.Image, np.ndarray],
        score_threshold: float = 0.2,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Classifies a dermatological image.

        Args:
            image: Can be a file path (str), a PIL Image, or a numpy array (RGB).
            score_threshold: Minimum sigmoid score to include in results.
            top_k: Maximum number of results to return.

        Returns:
            A list of dicts [{"name": str, "score": float}] sorted by score descending.
        """
        if isinstance(image, str):
            image = np.array(Image.open(image).convert("RGB"))
        elif isinstance(image, Image.Image):
            image = np.array(image.convert("RGB"))

        image_input = _prepare_input(image, model_size=448)

        with torch.no_grad():
            pred = self.model(image_input)
            # Apply sigmoid to get probabilities and handle ensemble mean if applicable
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
        "--threshold", type=float, default=0.2,
        help="Minimum score threshold (default: 0.2)",
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
