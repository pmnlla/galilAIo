#! python3.7

import argparse
import os
import numpy as np
import speech_recognition as sr
import whisper
import torch
import asyncio
import websockets
import json
import subprocess
import psutil
from websockets.server import WebSocketServerProtocol
from typing import Set, Optional

from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from sys import platform


def main():
    print("Starting up...")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="tiny", help="Model to use",
                        choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--non_english", action='store_true',
                        help="Don't use the english model.")
    parser.add_argument("--energy_threshold", default=1000,
                        help="Energy level for mic to detect.", type=int)
    parser.add_argument("--record_timeout", default=4,
                        help="How real time the recording is in seconds.", type=float)
    parser.add_argument("--phrase_timeout", default=1,
                        help="How much empty space between recordings before we "
                             "consider it a new line in the transcription.", type=float)
    parser.add_argument("--websocket_host", default="127.0.0.1",
                        help="WebSocket host to serve transcriptions on.", type=str)
    parser.add_argument("--websocket_port", default=8765,
                        help="WebSocket port to serve transcriptions on.", type=int)
    parser.add_argument("--enable_websocket", action='store_true',
                        help="Enable WebSocket server for broadcasting transcriptions.")
    parser.add_argument("--kill_ffplay", action='store_true',
                        help="Kill ffplay processes when speech is detected.")
    if 'linux' in platform:
        parser.add_argument("--default_microphone", default='pulse',
                            help="Default microphone name for SpeechRecognition. "
                                 "Run this with 'list' to view available Microphones.", type=str)
    args = parser.parse_args()

    # The last time a recording was retrieved from the queue.
    phrase_time = None
    # Thread safe Queue for passing data from the threaded recording callback.
    data_queue = Queue()
    # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold
    # Definitely do this, dynamic energy compensation lowers the energy threshold dramatically to a point where the SpeechRecognizer never stops recording.
    recorder.dynamic_energy_threshold = False

    # Important for linux users.
    # Prevents permanent application hang and crash by using the wrong Microphone
    if 'linux' in platform:
        mic_name = args.default_microphone
        if not mic_name or mic_name == 'list':
            print("Available microphone devices are: ")
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                print(f"Microphone with name \"{name}\" found")
            return
        else:
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                if mic_name in name:
                    source = sr.Microphone(sample_rate=16000, device_index=index)
                    break
    else:
        source = sr.Microphone(sample_rate=16000)

    cuda = torch.cuda.is_available()
    # Enhanced diagnostic prints
    print("\n=== CUDA Diagnostics ===")
    print(f"PyTorch version: {torch.__version__}")
    print(f"PyTorch built with CUDA: {torch.backends.cuda.is_built()}")
    print(f"CUDA available: {cuda}")
    print(f"CUDA version: {torch.version.cuda if cuda else 'N/A'}")
    print(f"GPU device count: {torch.cuda.device_count() if cuda else 0}")
    if cuda:
        print(f"Current GPU device: {torch.cuda.get_device_name()}")
    print("=====================\n")

    # Load / Download model
    model = args.model
    if args.model != "large" and not args.non_english:
        model = model + ".en"
    audio_model = whisper.load_model(model, device="cuda" if cuda else "cpu")

    record_timeout = args.record_timeout
    phrase_timeout = args.phrase_timeout

    transcription = ['']
    
    # WebSocket server setup
    connected_clients: Set[WebSocketServerProtocol] = set()
    websocket_server = None
    
    # ffplay process management
    def kill_ffplay_processes():
        """Kill all running ffplay processes"""
        print("Killing ffplay processes...")
        try:
            killed_count = 0
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and 'ffplay' in proc.info['name'].lower():
                        proc.kill()
                        killed_count += 1
                        print(f"Killed ffplay process (PID: {proc.info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            if killed_count > 0:
                print(f"Total ffplay processes killed: {killed_count}")
        except Exception as e:
            print(f"Error killing ffplay processes: {e}")
    
    async def handle_client(websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket client connections"""
        connected_clients.add(websocket)
        print(f"Client connected. Total clients: {len(connected_clients)}")
        try:
            await websocket.wait_closed()
        finally:
            connected_clients.remove(websocket)
            print(f"Client disconnected. Total clients: {len(connected_clients)}")
    
    async def broadcast_transcription(text: str):
        """Broadcast transcription to all connected clients"""
        if connected_clients:
            message = json.dumps({
                "type": "transcription",
                "text": text,
                "timestamp": datetime.utcnow().isoformat()
            })
            # Create a copy of the set to avoid modification during iteration
            clients_to_remove = set()
            for client in connected_clients.copy():
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    clients_to_remove.add(client)
                except Exception as e:
                    print(f"Error sending to client: {e}")
                    clients_to_remove.add(client)
            
            # Remove disconnected clients
            connected_clients.difference_update(clients_to_remove)
    
    # Start WebSocket server if enabled
    if args.enable_websocket:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            websocket_server = websockets.serve(
                handle_client, 
                args.websocket_host, 
                args.websocket_port
            )
            
            # Start the server in a separate thread
            import threading
            def run_websocket_server():
                loop.run_until_complete(websocket_server)
                loop.run_forever()
            
            websocket_thread = threading.Thread(target=run_websocket_server, daemon=True)
            websocket_thread.start()
            
            print(f"WebSocket server started on ws://{args.websocket_host}:{args.websocket_port}")
        except Exception as e:
            print(f"Failed to start WebSocket server: {e}")
            websocket_server = None

    with source:
        recorder.adjust_for_ambient_noise(source)

    def record_callback(_, audio:sr.AudioData) -> None:
        """
        Threaded callback function to receive audio data when recordings finish.
        audio: An AudioData containing the recorded bytes.
        """
        # Grab the raw bytes and push it into the thread safe queue.
        data = audio.get_raw_data()
        data_queue.put(data)

    # Create a background thread that will pass us raw audio bytes.
    # We could do this manually but SpeechRecognizer provides a nice helper.
    recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)

    # Cue the user that we're ready to go.
    print("Model loaded.\n")
    print("Listening... (Press Ctrl+C to stop)")

    while True:
        try:
            now = datetime.utcnow()
            # Pull raw recorded audio from the queue.
            if not data_queue.empty():
                # Kill ffplay when speech is detected
                if args.kill_ffplay:
                    kill_ffplay_processes()
                
                phrase_complete = False
                # If enough time has passed between recordings, consider the phrase complete.
                # Clear the current working audio buffer to start over with the new data.
                if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                    phrase_complete = True
                # This is the last time we received new audio data from the queue.
                phrase_time = now
                
                # Combine audio data from queue
                audio_data = b''.join(data_queue.queue)
                data_queue.queue.clear()
                
                # Convert in-ram buffer to something the model can use directly without needing a temp file.
                # Convert data from 16 bit wide integers to floating point with a width of 32 bits.
                # Clamp the audio stream frequency to a PCM wavelength compatible default of 32768hz max.
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                # Read the transcription.
                result = audio_model.transcribe(audio_np, fp16=torch.cuda.is_available())
                text = result['text'].strip()

                # If we detected a pause between recordings, add a new item to our transcription.
                # Otherwise edit the existing one.
                if phrase_complete:
                    transcription.append(text)
                    # Broadcast to WebSocket clients only when phrase is complete AND has meaningful content
                    # Filter out very short phrases that are likely incomplete
                    if (args.enable_websocket and text.strip() and connected_clients):
                        try:
                            # Run the async broadcast in the event loop
                            asyncio.run_coroutine_threadsafe(
                                broadcast_transcription(text), 
                                loop
                            )
                        except Exception as e:
                            print(f"WebSocket broadcast error: {e}")
                    
                    # Only display complete phrases to console
                    os.system('cls' if os.name=='nt' else 'clear')
                    for line in transcription:
                        if line.strip():  # Only show non-empty lines
                            print(line)
                    print('', end='', flush=True)
                else:
                    transcription[-1] = text
                    # Don't display partial transcriptions to console
            else:
                # Infinite loops are bad for processors, must sleep.
                sleep(0.25)
        except KeyboardInterrupt:
            break

    # Close WebSocket server
    if websocket_server:
        try:
            loop.call_soon_threadsafe(loop.stop)
            print("WebSocket server stopped.")
        except Exception as e:
            print(f"Error stopping WebSocket server: {e}")

    print("\n\nFinal Transcription:")
    for line in transcription:
        print(line)


if __name__ == "__main__":
    main()
