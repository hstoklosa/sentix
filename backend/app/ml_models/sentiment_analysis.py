import os
import logging
from pathlib import Path

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent / "finetuned_cryptobert"


class SentimentAnalyser:
    """A class to handle sentiment analysis for crypto-related text using a fine-tuned model."""
    
    def __init__(self, model_dir=None):
        self.model_dir = model_dir or self.MODEL_DIR
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cpu")
        self.is_loaded = False
    
    def load_model(self):
        """Load model and tokenizer if not already loaded."""
        if self.is_loaded:
            return self
            
        logger.info("Loading model and tokenizer...")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir, use_fast=True)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_dir, num_labels=3)
            self.model.to(self.device)
            self.model.eval()
            self.is_loaded = True
            logger.info(f"Loaded model and tokenizer from {self.model_dir}")
            logger.info(f"Model label mapping: {self.model.config.id2label}")
            return self
        except Exception as e:
            logger.error(f"Error loading model and tokenizer: {e}")
            raise RuntimeError(f"Error loading model and tokenizer: {e}")
    
    def predict(self, text: str) -> dict:
        if not self.is_loaded:
            logger.error("Model not loaded. Cannot predict.")
            return {"label": "Unknown", "score": 0.0, "polarity": 0.0}
        
        try:
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                padding='max_length',
                truncation=True, 
                max_length=64
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                
                probs = F.softmax(logits, dim=1)
                
                probabilities = probs[0].tolist()
                predicted_class = torch.argmax(probs, dim=1).item()
                confidence = probs[0][predicted_class].item()
                label = self.model.config.id2label[predicted_class]
                
                # Calculate polarity for 3-class sentiment (bearish/neutral/bullish)
                bearish_prob = probs[0][0].item() if 0 in self.model.config.id2label else 0
                neutral_prob = probs[0][1].item() if 1 in self.model.config.id2label else 0
                bullish_prob = probs[0][2].item() if 2 in self.model.config.id2label else 0
                
                polarity = bullish_prob - bearish_prob

            return {
                "label": label,
                "score": confidence,
                "polarity": polarity
            }
        except Exception as e:
            logger.error(f"Error during prediction for text '{text[:50]}...': {e}", exc_info=True)
            return {"label": "Error", "score": 0.0, "polarity": 0.0}


sentiment_analyser = SentimentAnalyser()
