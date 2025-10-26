#!/usr/bin/env python3
"""Check the emotion model labels."""

from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_name = "j-hartmann/emotion-english-distilroberta-base"

print(f"Loading model: {model_name}")
model = AutoModelForSequenceClassification.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

print(f"\nModel config:")
print(f"  Number of labels: {model.config.num_labels}")
print(f"  Label mapping: {model.config.id2label}")

