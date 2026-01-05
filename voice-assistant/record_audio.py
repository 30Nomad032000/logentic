"""
Simple audio recorder for Windows
Saves audio file that can be processed by WSL2

Run: python record_audio.py
"""

import sounddevice as sd
import soundfile as sf
import numpy as np

def main():
    print("\n" + "="*50)
    print("AUDIO RECORDER")
    print("Records audio for processing in WSL2")
    print("="*50)

    duration = 6
    sample_rate = 16000
    output_file = "recorded_audio.wav"

    while True:
        choice = input("\nPress ENTER to record (or 'q' to quit): ").strip()
        if choice.lower() == 'q':
            break

        print(f"Recording {duration} seconds... Speak now!")
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.float32
        )
        sd.wait()
        print("Recording complete!")

        # Save file
        sf.write(output_file, audio, sample_rate)
        print(f"\nSaved to: {output_file}")
        print(f"Full path: E:\\Work\\logentic\\voice-assistant\\{output_file}")
        print("\nNow run in WSL2:")
        print(f"  python process_audio.py /mnt/e/Work/logentic/voice-assistant/{output_file}")

    print("Goodbye!")

if __name__ == "__main__":
    main()
