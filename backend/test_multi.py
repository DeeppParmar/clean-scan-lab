import asyncio
import cv2
from loguru import logger
from services.detector import detector

async def main():
    logger.info("Initializing detector pipeline...")
    detector.load()
    
    # We will use the exact battery image from earlier to verify at least one object
    # If the user has a composite image we could test it, but for now let's just test
    # that YOLO finds the object and mobilenet classifies it.
    img_path = r"C:\Users\Abhi\Downloads\archive (1)\garbage_classification\battery\battery1.jpg"
    img = cv2.imread(img_path)
    if img is None:
        logger.error("Failed to load image")
        return
        
    logger.info("Starting detection...")
    detections = await detector.detect(img)
    
    logger.info(f"Found {len(detections)} items")
    for i, d in enumerate(detections):
        logger.info(f"[{i}] {d.label} ({d.category}) - Conf: {d.confidence:.2f} Box: {d.bbox}")

if __name__ == "__main__":
    asyncio.run(main())
