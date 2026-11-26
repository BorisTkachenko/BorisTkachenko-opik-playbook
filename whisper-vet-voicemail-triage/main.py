"""Veterinary-clinic voicemail triage: TTS -> Whisper -> urgency + callbacks.

The scripts in data/voicemails.json are fictional. At run time each one is
spoken with OpenAI TTS into output/audio/, transcribed with Whisper, and
triaged by a chat model into an urgency level and a callback list.
"""

import json
from pathlib import Path

from dotenv import load_dotenv

EXAMPLE_DIR = Path(__file__).resolve().parent
DATA_DIR = EXAMPLE_DIR / "data"
OUTPUT_DIR = EXAMPLE_DIR / "output"

load_dotenv(EXAMPLE_DIR.parent / ".env")

from openai import OpenAI

from triage import TRIAGE_SYSTEM_PROMPT, callback_queue, parse_triage

TTS_MODEL = "tts-1"
TRANSCRIBE_MODEL = "whisper-1"
TRIAGE_MODEL = "gpt-4o-mini"

openai_client = OpenAI()


def load_voicemails() -> list[dict]:
    return json.loads((DATA_DIR / "voicemails.json").read_text())


def synthesize_voicemail(voicemail: dict, audio_path: Path) -> None:
    """Speak the script with TTS and write the MP3."""
    response = openai_client.audio.speech.create(
        model=TTS_MODEL,
        voice=voicemail["voice"],
        input=voicemail["script"],
        response_format="mp3",
    )
    audio_path.write_bytes(response.content)


def transcribe(audio_path: Path) -> str:
    """Speech-to-text with Whisper."""
    with audio_path.open("rb") as audio_file:
        return openai_client.audio.transcriptions.create(
            model=TRANSCRIBE_MODEL, file=audio_file, response_format="text"
        )


def triage_transcript(transcript: str) -> dict:
    """Transcript -> {urgency, urgency_reason, callbacks}."""
    response = openai_client.chat.completions.create(
        model=TRIAGE_MODEL,
        messages=[
            {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
        response_format={"type": "json_object"},
    )
    return parse_triage(response.choices[0].message.content)


def process_voicemail(voicemail: dict) -> dict:
    """The full pipeline for one voicemail."""
    audio_path = OUTPUT_DIR / "audio" / f"{voicemail['id']}.mp3"
    synthesize_voicemail(voicemail, audio_path)
    transcript = transcribe(audio_path)
    result = triage_transcript(transcript)
    record = {"id": voicemail["id"], "transcript": transcript, **result}
    (OUTPUT_DIR / f"{voicemail['id']}.json").write_text(json.dumps(record, indent=2))
    return record


if __name__ == "__main__":
    (OUTPUT_DIR / "audio").mkdir(parents=True, exist_ok=True)
    results = []
    for voicemail in load_voicemails():
        print(f"\n=== {voicemail['id']} ===")
        record = process_voicemail(voicemail)
        results.append(record)
        print(f"Heard:   {record['transcript'].strip()}")
        print(f"Urgency: {record['urgency']} - {record['urgency_reason']}")
    print("\nCallback queue (most urgent first):")
    for row in callback_queue(results):
        print(f"  [{row['urgency']}] {row['owner']} / {row['pet']} / {row['number']}: {row['reason']}")
