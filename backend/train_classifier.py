"""
EcoLens — MobileNetV2 Waste Classifier Training Script
Trains on the 12-class garbage_classification dataset and saves
waste_classifier.pth + waste_classifier_classes.json

Usage:
    cd backend
    python train_classifier.py
"""

import oson
import os
import sys
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms, models

# ─── Config ──────────────────────────────────────────────────────────────────

DATASET_DIR = r"C:\Users\Abhi\Downloads\archive (1)\garbage_classification"
OUTPUT_WEIGHTS = "waste_classifier.pth"
OUTPUT_CLASSES = "waste_classifier_classes.json"

BATCH_SIZE = 32
NUM_EPOCHS = 20
LEARNING_RATE = 1e-3
FINE_TUNE_LR = 1e-4       # Lower LR for backbone fine-tuning phase
VAL_SPLIT = 0.20
NUM_WORKERS = 0            # Windows compat — set higher on Linux
IMAGE_SIZE = 224
EARLY_STOP_PATIENCE = 5

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ─── Data Augmentation ───────────────────────────────────────────────────────

train_transforms = transforms.Compose([
    transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.7, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(p=0.2),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.1),
    transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    transforms.RandomErasing(p=0.15),
])

val_transforms = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


# ─── Dataset ─────────────────────────────────────────────────────────────────

class SplitImageFolder(torch.utils.data.Dataset):
    """Applies different transforms to train/val subsets of the same ImageFolder."""
    def __init__(self, subset, transform):
        self.subset = subset
        self.transform = transform

    def __len__(self):
        return len(self.subset)

    def __getitem__(self, idx):
        img, label = self.subset[idx]
        if self.transform:
            img = self.transform(img)
        return img, label


def build_dataloaders():
    """Load dataset, split into train/val, return loaders + class names."""
    if not os.path.isdir(DATASET_DIR):
        print(f"ERROR: Dataset directory not found: {DATASET_DIR}")
        sys.exit(1)

    # Load without transforms (raw PIL images)
    full_dataset = datasets.ImageFolder(DATASET_DIR, transform=None)
    class_names = full_dataset.classes
    print(f"Found {len(full_dataset)} images across {len(class_names)} classes:")
    for i, cls in enumerate(class_names):
        count = sum(1 for _, label in full_dataset.samples if label == i)
        print(f"  {i:>2}: {cls:<15} ({count} images)")

    # Split
    val_size = int(len(full_dataset) * VAL_SPLIT)
    train_size = len(full_dataset) - val_size

    train_subset, val_subset = random_split(
        full_dataset, [train_size, val_size],
        generator=torch.Generator().manual_seed(42)
    )

    # Wrap with transforms
    train_dataset = SplitImageFolder(train_subset, train_transforms)
    val_dataset = SplitImageFolder(val_subset, val_transforms)

    train_loader = DataLoader(
        train_dataset, batch_size=BATCH_SIZE, shuffle=True,
        num_workers=NUM_WORKERS, pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset, batch_size=BATCH_SIZE, shuffle=False,
        num_workers=NUM_WORKERS, pin_memory=True
    )

    print(f"\nTrain: {train_size} | Val: {val_size}")
    return train_loader, val_loader, class_names


# ─── Model ───────────────────────────────────────────────────────────────────

def build_model(num_classes: int) -> nn.Module:
    """MobileNetV2 pretrained on ImageNet with custom classifier head."""
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)

    # Freeze backbone initially
    for param in model.features.parameters():
        param.requires_grad = False

    # Replace classifier head
    model.classifier = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(model.last_channel, 512),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(512, num_classes),
    )

    return model.to(DEVICE)


# ─── Training ────────────────────────────────────────────────────────────────

def train_one_epoch(model, loader, criterion, optimizer):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    return running_loss / total, 100.0 * correct / total


@torch.no_grad()
def validate(model, loader, criterion):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)

        outputs = model(images)
        loss = criterion(outputs, labels)

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    return running_loss / total, 100.0 * correct / total


def main():
    print("=" * 60)
    print(" EcoLens — MobileNetV2 Waste Classifier Training")
    print("=" * 60)
    print(f"Device: {DEVICE}")
    print(f"Dataset: {DATASET_DIR}\n")

    train_loader, val_loader, class_names = build_dataloaders()
    model = build_model(num_classes=len(class_names))

    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

    # ── Phase 1: Train classifier head only ─────────────────────────────
    print("\n── Phase 1: Training classifier head (backbone frozen) ──")
    optimizer = optim.Adam(model.classifier.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=8)

    best_val_acc = 0.0
    patience_counter = 0

    for epoch in range(1, 9):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer)
        val_loss, val_acc = validate(model, val_loader, criterion)
        scheduler.step()
        elapsed = time.time() - t0

        print(
            f"  Epoch {epoch:>2}/8  |  "
            f"Train Loss: {train_loss:.4f}  Acc: {train_acc:.1f}%  |  "
            f"Val Loss: {val_loss:.4f}  Acc: {val_acc:.1f}%  |  "
            f"{elapsed:.1f}s"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), OUTPUT_WEIGHTS)
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= 3:
                print("  Early stop in Phase 1 — moving to Phase 2")
                break

    print(f"  Best Phase 1 val acc: {best_val_acc:.1f}%")

    # ── Phase 2: Fine-tune entire network ────────────────────────────────
    print("\n── Phase 2: Fine-tuning entire network ──")

    # Unfreeze backbone
    for param in model.features.parameters():
        param.requires_grad = True

    # Different learning rates for backbone vs head
    optimizer = optim.Adam([
        {"params": model.features.parameters(), "lr": FINE_TUNE_LR * 0.1},
        {"params": model.classifier.parameters(), "lr": FINE_TUNE_LR},
    ])
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS - 8)

    patience_counter = 0

    for epoch in range(1, NUM_EPOCHS - 8 + 1):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer)
        val_loss, val_acc = validate(model, val_loader, criterion)
        scheduler.step()
        elapsed = time.time() - t0

        marker = ""
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), OUTPUT_WEIGHTS)
            patience_counter = 0
            marker = " ★ BEST"
        else:
            patience_counter += 1

        print(
            f"  Epoch {epoch:>2}/{NUM_EPOCHS - 8}  |  "
            f"Train Loss: {train_loss:.4f}  Acc: {train_acc:.1f}%  |  "
            f"Val Loss: {val_loss:.4f}  Acc: {val_acc:.1f}%  |  "
            f"{elapsed:.1f}s{marker}"
        )

        if patience_counter >= EARLY_STOP_PATIENCE:
            print(f"  Early stopping triggered — no improvement for {EARLY_STOP_PATIENCE} epochs")
            break

    # ── Save class names ──────────────────────────────────────────────────
    with open(OUTPUT_CLASSES, "w") as f:
        json.dump(class_names, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f" Training complete!")
    print(f" Best validation accuracy: {best_val_acc:.1f}%")
    print(f" Weights saved to: {OUTPUT_WEIGHTS}")
    print(f" Classes saved to: {OUTPUT_CLASSES}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
