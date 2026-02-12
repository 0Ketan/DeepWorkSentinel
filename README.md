# Deep Work Sentinel 🛡️

An AI-powered focus assistant that uses real-time Computer Vision and a Local Large Language Model (LLM) to keep you off your phone.

## How it Works
1. **The Eyes:** Uses **YOLOv8** (Small) to scan your webcam for cell phones at 30+ FPS.
2. **The Brain:** If a phone is detected for more than 3 seconds, the system triggers **Ollama (Llama 3.2 1B)** to generate a unique, sarcastic insult.
3. **The Voice:** The insult is converted to speech via **gTTS** and played through your system audio to shame you back to work.

## Features
- **GPU Accelerated:** Optimized for NVIDIA RTX GPUs using CUDA.
- **Local & Private:** The LLM runs entirely on your machine via Ollama.
- **Asynchronous:** Uses Python `threading` so the video feed never freezes while the AI is "thinking" or talking.

## Prerequisites
- **Python:** 3.10 or higher (Tested on 3.14).
- **OS:** Linux (Designed for Ubuntu/Fedora) or Windows.
- **Hardware:** NVIDIA GPU recommended for best FPS.

## Setup Instructions

### 1. Install System Dependencies (Linux)
```bash
sudo apt update && sudo apt install mpg123
