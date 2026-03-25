import os
import sys
import time

import torch
import torch.nn as nn
import torch.optim as optim

from train_classifier import (
    build_dataloaders, build_model, train_one_epoch, validate,
    DEVICE, OUTPUT_WEIGHTS, FINE_TUNE_LR
)

def main():
    print("=" * 60)
    print(" EcoLens — MobileNetV2 Incremental Fine-Tuning")
    print("=" * 60)

    train_loader, val_loader, class_names = build_dataloaders()
    model = build_model(num_classes=len(class_names))
    
    if not os.path.exists(OUTPUT_WEIGHTS):
        print(f"Error: Base weights {OUTPUT_WEIGHTS} not found!")
        sys.exit(1)
        
    print(f"Loading base weights from {OUTPUT_WEIGHTS}...")
    model.load_state_dict(torch.load(OUTPUT_WEIGHTS, map_location=DEVICE))
    model.to(DEVICE)
    
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    
    print("\n── Fine-tuning entire network (Trash Bag Focus) ──")
    for param in model.features.parameters():
        param.requires_grad = True

    optimizer = optim.Adam([
        {"params": model.features.parameters(), "lr": FINE_TUNE_LR * 0.1},
        {"params": model.classifier.parameters(), "lr": FINE_TUNE_LR},
    ])
    epochs = 6
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_acc = 0.0

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer)
        val_loss, val_acc = validate(model, val_loader, criterion)
        scheduler.step()
        elapsed = time.time() - t0

        marker = ""
        if val_acc >= best_val_acc: # Save if it meets or beats to ensure we get a checkpoint
            best_val_acc = val_acc
            torch.save(model.state_dict(), OUTPUT_WEIGHTS)
            marker = " ★ BEST"

        print(
            f"  Epoch {epoch:>2}/{epochs}  |  "
            f"Train Loss: {train_loss:.4f}  Acc: {train_acc:.1f}%  |  "
            f"Val Loss: {val_loss:.4f}  Acc: {val_acc:.1f}%  |  "
            f"{elapsed:.1f}s{marker}"
        )

    print(f"\nIncremental fine-tuning complete! Best Val Acc: {best_val_acc:.1f}%")

if __name__ == "__main__":
    main()
