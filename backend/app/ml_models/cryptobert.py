import os
import logging
from pathlib import Path

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

logger = logging.getLogger(__name__)

# Global variables to hold the model and tokenizer, which 
# ensures they are loaded only once when the module is imported.
model, tokenizer, device = None, None, None

MODEL_DIR = Path(__file__).parent / "cryptobert"
TOKENIZER_DIR = Path(__file__).parent / "cryptobert"

LABEL_MAP = { 0: "Negative", 1: "Neutral", 2: "Positive" }

def load_model():
    global model, tokenizer, device

    if model is None or tokenizer is None:
        logger.info("Loading model and tokenizer...")
        
        try:
            tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_DIR)
            model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
            logger.info(f"Loaded model and tokenizer from {MODEL_DIR}")

            if torch.cuda.is_available():
                device = torch.device("cuda")
                logger.info("CUDA (GPU) is available. Using GPU.")
            else:
                device = torch.device("cpu")
                logger.info("CUDA not available. Using CPU.")
            
            model.to(device) # Move model to the selected device
            model.eval() # Set model to evaluation mode
        except Exception as e:
            logger.error(f"Error loading model and tokenizer: {e}")
            raise RuntimeError(f"Error loading model and tokenizer: {e}")
