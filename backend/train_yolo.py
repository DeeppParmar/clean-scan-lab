import os
import yaml
import time
from ultralytics import YOLO

def main():
    print("======================================================")
    print(" EcoLens - YOLOv8 TACO Trash Detection Training Script")
    print("======================================================")

    # 1. Dataset path
    base_dir = r"C:\Users\Abhi\.cache\kagglehub\datasets\sohamchaudhari2004\taco-trash-detection-dataset\versions\1"
    
    print(f"Waiting for dataset to be fully downloaded at: {base_dir}")
    # Simple wait loop if it's still extracting
    while not os.path.exists(base_dir):
        time.sleep(5)

    yaml_path = os.path.join(base_dir, "data.yaml")
    
    # Check if data.yaml exists (if nested in a subfolder, we find it)
    if not os.path.exists(yaml_path):
        for root, dirs, files in os.walk(base_dir):
            if "data.yaml" in files or "dataset.yaml" in files:
                yaml_name = "data.yaml" if "data.yaml" in files else "dataset.yaml"
                yaml_path = os.path.join(root, yaml_name)
                base_dir = root
                break

    if not os.path.exists(yaml_path):
        print(f"ERROR: Could not find data.yaml in {base_dir}")
        return

    print(f"\nFound dataset YAML: {yaml_path}")

    # 2. Safely Update data.yaml with absolute paths for YOLOv8
    try:
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        # Set the root 'path' variable so ultralytics knows where to look
        data["path"] = base_dir 
        
        with open(yaml_path, "w") as f:
            yaml.dump(data, f)
        print("Updated dataset YAML paths successfully.")
    except Exception as e:
        print(f"Warning: Could not modify YAML automatically. Assuming paths are correct. {e}")

    # 3. Train Model
    print("\nStarting YOLOv8 training on TACO dataset...")
    print("Note: This will take several hours depending on your GPU.\n")
    
    model = YOLO("yolov8n.pt")
    model.train(
        data=yaml_path, 
        epochs=100, 
        imgsz=640, 
        device="cuda",
        batch=16,
        patience=15 # Early stopping if no improvement
    )
    
    print("\n======================================================")
    print(" YOLO Training Complete!")
    print(" Best weights saved to: runs/detect/train/weights/best.pt")
    print(" You can replace your current yolov8n.pt with this file.")
    print("======================================================")

if __name__ == "__main__":
    main()
