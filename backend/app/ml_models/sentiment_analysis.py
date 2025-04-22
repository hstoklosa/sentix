import os
import logging
from pathlib import Path

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent / "finetuned_cryptobert"
model, tokenizer, device = None, None, None


def load_model():
    """
    Load model and tokenizer once on startup.
    The model will be loaded into memory only the first time this is called.
    """
    global model, tokenizer, device

    # Check if model is already loaded
    if model is not None and tokenizer is not None:
        logger.info("Model already loaded")
        return
        
    logger.info("Loading model and tokenizer...")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, use_fast=True)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR, num_labels=3)
        model.to(torch.device("cpu"))
        model.eval()
        logger.info(f"Loaded model and tokenizer from {MODEL_DIR}")
        logger.info(f"Model label mapping: {model.config.id2label}")
    except Exception as e:
        logger.error(f"Error loading model and tokenizer: {e}")
        raise RuntimeError(f"Error loading model and tokenizer: {e}")


def predict_sentiment(text: str) -> dict:
    """
    Predict crypto sentiment for a given text.
    
    Args:
        text: The crypto-related text to analyze
        
    Returns:
        dict: Dictionary with label, score, and polarity
              where polarity is a value between -1 (bearish) and 1 (bullish)
    """
    global model, tokenizer, device
    
    if model is None or tokenizer is None:
        logger.error("Failed to load model or tokenizer. Cannot predict.")
        return {"label": "Unknown", "score": 0.0, "polarity": 0.0}
    
    try:
        inputs = tokenizer(
            text, 
            return_tensors="pt", 
            padding='max_length',
            truncation=True, 
            max_length=64
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            
            probs = F.softmax(logits, dim=1)
            
            probabilities = probs[0].tolist()
            predicted_class = torch.argmax(probs, dim=1).item()
            confidence = probs[0][predicted_class].item()
            label = model.config.id2label[predicted_class]
            
            # Calculate polarity for 3-class sentiment (bearish/neutral/bullish):
            # -1.0 for fully bearish, 0.0 for neutral, 1.0 for fully bullish
            bearish_prob = probs[0][0].item() if 0 in model.config.id2label else 0
            neutral_prob = probs[0][1].item() if 1 in model.config.id2label else 0
            bullish_prob = probs[0][2].item() if 2 in model.config.id2label else 0
            
            polarity = bullish_prob - bearish_prob

        return {
            "label": label,
            "score": confidence,
            "polarity": polarity
        }
    except Exception as e:
        logger.error(f"Error during prediction for text '{text[:50]}...': {e}", exc_info=True)
        return {"label": "Error", "score": 0.0, "polarity": 0.0}
    