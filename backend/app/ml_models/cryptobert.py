import os
import logging
from pathlib import Path

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)

# Global variables to hold the model and tokenizer, which 
# ensures they are loaded only once when the module is imported.
model, tokenizer, device = None, None, None

# MODEL_DIR = Path(__file__).parent / "cryptobert"
# TOKENIZER_DIR = Path(__file__).parent / "cryptobert"
MODEL_NAME = "ElKulako/cryptobert"

def load_model():
    global model, tokenizer, device

    if model is None or tokenizer is None:
        logger.info("Loading model and tokenizer...")
        
        try:
            # Load directly from the Hugging Face Hub
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
            model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=3)
            logger.info(f"Loaded model and tokenizer from {MODEL_NAME}")
            logger.info(f"Model label mapping: {model.config.id2label}")

            if torch.cuda.is_available():
                device = torch.device("cuda")
                logger.info("CUDA (GPU) is available. Using GPU.")
            else:
                device = torch.device("cpu")
                logger.info("CUDA not available. Using CPU.")
            
            model.to(device) # move to the selected device
            model.eval() # set model to evaluation mode
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
    
        # Move inputs to the same device as the model
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Disable gradient calculation for inference
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            
            # Apply softmax to get probabilities
            probs = F.softmax(logits, dim=1)
            
            # Get all class probabilities
            probabilities = probs[0].tolist()
            
            # Get predicted class index and its probability
            predicted_class = torch.argmax(probs, dim=1).item()
            confidence = probs[0][predicted_class].item()
            
            # Get the label from the model's configuration
            label = model.config.id2label[predicted_class]
            
            # Calculate polarity for 3-class sentiment (bearish/neutral/bullish):
            # -1.0 for fully bearish, 0.0 for neutral, 1.0 for fully bullish
            bearish_prob = probs[0][0].item() if 0 in model.config.id2label else 0
            neutral_prob = probs[0][1].item() if 1 in model.config.id2label else 0
            bullish_prob = probs[0][2].item() if 2 in model.config.id2label else 0
            
            # Weighted sum: bearish (-1) + neutral (0) + bullish (1)
            polarity = bullish_prob - bearish_prob
        
        return {
            "label": label,
            "score": confidence,
            "polarity": polarity
        }
    except Exception as e:
        logger.error(f"Error during prediction for text '{text[:50]}...': {e}", exc_info=True)
        return {"label": "Error", "score": 0.0, "polarity": 0.0}
    