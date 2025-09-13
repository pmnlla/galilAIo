#!/usr/bin/env python3

import asyncio
import websockets
import json

async def test_client():
    uri = "ws://127.0.0.1:8765"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            print("Listening for transcriptions... (Press Ctrl+C to stop)")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get("type") == "transcription":
                        print(f"[{data.get('timestamp')}] {data.get('text')}")
                except json.JSONDecodeError:
                    print(f"Received non-JSON message: {message}")
                except Exception as e:
                    print(f"Error processing message: {e}")
                    
    except websockets.exceptions.ConnectionRefused:
        print("Could not connect to WebSocket server. Make sure the server is running with --enable_websocket flag.")
    except KeyboardInterrupt:
        print("\nDisconnected from server.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_client())
