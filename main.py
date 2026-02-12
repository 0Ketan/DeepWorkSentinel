import cv2
import time
import torch
import threading
import queue
import os
import ollama  # <--- The new Brain
from ultralytics import YOLO
from gtts import gTTS

# --- CONFIGURATION ---
PHONE_CLASS_ID = 67         
CONFIDENCE_THRESHOLD = 0.5  
DISTRACTION_LIMIT = 3.0     
COOLDOWN_SECONDS = 8.0      # Increased cooldown so it doesn't interrupt itself

# --- 1. THE BRAIN & VOICE (THREADED) ---
speech_queue = queue.Queue()

def brain_worker():
    """Generates insults using Local LLM and speaks them."""
    while True:
        # Wait for a trigger
        trigger = speech_queue.get()
        if trigger is None: break 
        
        try:
            print("\n[BRAIN] Generating insult...")
            
            # 1. Ask Llama 3.2 for a short, mean sentence
            response = ollama.chat(model='llama3.2:1b', messages=[
                {
                    'role': 'user',
                    'content': 'You are a strict study supervisor. I just got distracted by my phone. Give me a ONE sentence, harsh, sarcastic command to get back to work. Do not use quotes.'
                },
            ])
            
            insult = response['message']['content']
            print(f"[BRAIN] Says: '{insult}'")

            # 2. Generate Audio (gTTS)
            tts = gTTS(text=insult, lang='en', tld='co.uk')
            filename = "shout.mp3"
            
            if os.path.exists(filename):
                os.remove(filename)
            tts.save(filename)
            
            # 3. Play Audio
            os.system(f"mpg123 -q {filename}")
            
        except Exception as e:
            print(f"Brain Error: {e}")
            
        speech_queue.task_done()

# Start the brain thread
brain_thread = threading.Thread(target=brain_worker, daemon=True)
brain_thread.start()

def trigger_punishment():
    if speech_queue.empty():
        speech_queue.put("TRIGGER")

# --- 2. THE EYES (OPTIMIZED) ---
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Running on: {device}")

# Use Small model for balance of Speed/Accuracy
# It will auto-download 'yolov8s.pt' if you don't have it
print("Loading YOLOv8 Small...")
model = YOLO('yolov8s.pt') 
model.to(device)

# Camera Setup
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# --- 3. MAIN LOOP ---
distraction_start = 0
last_shout_time = 0
phone_detected = False

print("SENTINEL ONLINE. Don't touch your phone.")

while True:
    start_loop = time.time()
    success, frame = cap.read()
    if not success: break

    # Inference
    results = model(frame, stream=True, device=device, verbose=False)
    phone_detected = False

    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            
            if cls == PHONE_CLASS_ID and conf > CONFIDENCE_THRESHOLD:
                phone_detected = True
                
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                cv2.putText(frame, f"PHONE {conf:.2f}", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # Logic
    current_time = time.time()

    if phone_detected:
        if distraction_start == 0:
            distraction_start = current_time
        
        elapsed = current_time - distraction_start
        
        if elapsed > DISTRACTION_LIMIT:
            cv2.putText(frame, "VIOLATION!", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)
            
            if (current_time - last_shout_time) > COOLDOWN_SECONDS:
                trigger_punishment()
                last_shout_time = current_time
        else:
            remaining = DISTRACTION_LIMIT - elapsed
            cv2.putText(frame, f"WARNING: {remaining:.1f}s", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)
    else:
        distraction_start = 0

    fps = 1.0 / (time.time() - start_loop)
    cv2.putText(frame, f"FPS: {fps:.0f}", (10, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow('Deep Work Sentinel', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()