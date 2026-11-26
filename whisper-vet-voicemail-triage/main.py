"""Veterinary-clinic voicemail triage: TTS -> Whisper -> urgency + callbacks.

Each voicemail is one trace in the "whisper-vet-voicemail-triage" project:

    triage-voicemail                  <- whole pipeline, playable MP3 attached
    |- synthesize-voicemail           <- TTS
    |- transcribe                     <- whisper-1
    '- triage                         <- gpt-4o-mini -> urgency + callbacks

The scripts in data/voicemails.json are fictional. At run time each one is
spoken with OpenAI TTS into output/audio/, transcribed with Whisper, and
triaged by a chat model into an urgency level and a callback list.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

EXAMPLE_DIR = Path(__file__).resolve().parent
DATA_DIR = EXAMPLE_DIR / "data"
OUTPUT_DIR = EXAMPLE_DIR / "output"

load_dotenv(EXAMPLE_DIR.parent / ".env")
# Pin the Opik project before opik is imported so no trace lands in "Default Project".
os.environ["OPIK_PROJECT_NAME"] = "whisper-vet-voicemail-triage"
os.environ.pop("OPENAI_BASE_URL", None)

import opik
from openai import OpenAI
from opik import Attachment, opik_context
from opik.integrations.openai import track_openai

from triage import TRIAGE_SYSTEM_PROMPT, callback_queue, parse_triage

TTS_MODEL = "tts-1"
TRANSCRIBE_MODEL = "whisper-1"
TRIAGE_MODEL = "gpt-4o-mini"

# track_openai wraps the client: the TTS, Whisper and chat calls each become an
# llm span nested under the @opik.track span that made them (chat gets tokens + cost).
openai_client = track_openai(OpenAI())


def load_voicemails() -> list[dict]:
    return json.loads((DATA_DIR / "voicemails.json").read_text())


# @opik.track opens a span for this step; the trace's span tree mirrors the pipeline.
@opik.track(name="synthesize-voicemail")
def synthesize_voicemail(voicemail: dict, audio_path: Path) -> None:
    """Speak the script with TTS and write the MP3."""
    response = openai_client.audio.speech.create(
        model=TTS_MODEL,
        voice=voicemail["voice"],
        input=voicemail["script"],
        response_format="mp3",
    )
    audio_path.write_bytes(response.content)


@opik.track(name="transcribe")
def transcribe(audio_path: Path) -> str:
    """Speech-to-text with Whisper."""
    with audio_path.open("rb") as audio_file:
        return openai_client.audio.transcriptions.create(
            model=TRANSCRIBE_MODEL, file=audio_file, response_format="text"
        )


@opik.track(name="triage")
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


# The outermost tracked call is the trace root: one trace per voicemail.
@opik.track(name="triage-voicemail")
def process_voicemail(voicemail: dict) -> dict:
    """The full pipeline for one voicemail."""
    audio_path = OUTPUT_DIR / "audio" / f"{voicemail['id']}.mp3"
    synthesize_voicemail(voicemail, audio_path)
    transcript = transcribe(audio_path)
    result = triage_transcript(transcript)
    # Attachment uploads the MP3 to the trace, where the UI plays it inline:
    # you can hear what the pipeline heard next to what it concluded.
    opik_context.update_current_trace(
        attachments=[Attachment(data=str(audio_path), content_type="audio/mpeg")]
    )
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
    # Traces are sent in the background; flush so none are lost at exit.
    opik.flush_tracker()
    print("\nDone. Open the whisper-vet-voicemail-triage project in Opik.")
