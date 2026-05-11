import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import os
import argparse
import time
import json

def load_class_mapping(json_path):
    if not os.path.exists(json_path):
        # Fallback if json is missing
        print(f"Warning: {json_path} not found. Using default mapping.")
        return ['Abrasions', 'Bruises', 'Burns', 'Cut', 'Laceration', 'Stab_wound']
    with open(json_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    return [mapping[str(i)] for i in range(len(mapping))]

def main(args):
    # 1. Config
    MODEL_PATH = args.model
    IMAGE_PATH = args.image
    MAPPING_PATH = args.mapping
    
    # Jetson Nano optimization: use CUDA if available
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Using device: {DEVICE}")

    CLASS_NAMES = load_class_mapping(MAPPING_PATH)
    
    # 2. Define Model (MobileNetV3 Small)
    print(f"[*] Loading model structure (MobileNetV3 Small)...")
    try:
        model = models.mobilenet_v3_small(weights=None) # pretrained=False equivalent
    except TypeError:
        model = models.mobilenet_v3_small(pretrained=False) # Fallback for older torchvision
        
    num_classes = len(CLASS_NAMES)
    num_ftrs = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(num_ftrs, num_classes)
    
    # 3. Load Weights
    if not os.path.exists(MODEL_PATH):
        print(f"[!] Error: Model file not found at {MODEL_PATH}")
        return
        
    print(f"[*] Loading weights from {MODEL_PATH}...")
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model = model.to(DEVICE)
    model.eval()

    # 4. Preprocessing
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    if not os.path.exists(IMAGE_PATH):
        print(f"[!] Error: Image not found at {IMAGE_PATH}")
        return

    try:
        print(f"[*] Preprocessing image {IMAGE_PATH}...")
        img = Image.open(IMAGE_PATH).convert('RGB')
        img_t = preprocess(img)
        batch_t = torch.unsqueeze(img_t, 0).to(DEVICE)
        
        # 5. Inference
        print("[*] Running inference...")
        start_time = time.time()
        with torch.no_grad():
            outputs = model(batch_t)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, index = torch.max(probabilities, 0)
        end_time = time.time()
            
        result = CLASS_NAMES[index]
        
        print("\n" + "="*30)
        print("        [ INFERENCE RESULT ]      ")
        print("="*30)
        print(f" File: {os.path.basename(IMAGE_PATH)}")
        print(f" Diagnosis: {result}")
        print(f" Confidence: {confidence.item()*100:.2f}%")
        print(f" Inference Time: {(end_time - start_time)*1000:.2f} ms")
        print("="*30 + "\n")
        
    except Exception as e:
        print(f"[!] Error processing image: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wound Detection Inference for Jetson Nano")
    parser.add_argument("--image", type=str, required=True, help="Path to the test image")
    parser.add_argument("--model", type=str, default="mobilenet_v3_wound_best.pth", help="Path to the model file")
    parser.add_argument("--mapping", type=str, default="wound_class_mapping.json", help="Path to the class mapping JSON")
    
    args = parser.parse_args()
    main(args)
