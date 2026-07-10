from dotenv import load_dotenv
import asyncio
import os

from app.services.conversation_state import ACTIVE_CALLS
from backend_client import notify_call_complete
from finish_call import finish_call, _build_transcript

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
)

from livekit.plugins import sarvam, openai

load_dotenv()


class AppointmentBookingAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="""
You are a professional appointment booking assistant making outbound calls.

RULES:
- Keep every response under 2 sentences.
- Be polite and professional.
- Do not hallucinate or invent details.
- Do not discuss unrelated topics.

CONVERSATION STEPS — follow in exact order:

Step 1: Greet the customer.
  Say: "Hello, I'm calling from the appointment booking service."

Step 2: Ask for the customer's name.
  Wait for their response and remember the name they give you.

Step 3: Ask for the appointment date.
  Wait for their response.

Step 4: Ask for the appointment time.
  Wait for their response.

Step 5: Confirm the details.
  Read back: name, date, and time.
  Ask: "Is that correct?"
  If the customer says NO or wants to change anything, ask which detail to correct and go back to the relevant step.
  If the customer says YES, immediately call the finish_call tool.

When calling finish_call, pass:
  - customer_name: the name from Step 2
  - appointment_date: the date from Step 3
  - appointment_time: the time from Step 4

Do NOT say anything else after the customer confirms — just call the tool.
The tool will handle the goodbye message automatically.
""",
            tools=[finish_call],
        )



async def entrypoint(ctx: JobContext):

    print("=" * 60)
    print("JOB RECEIVED")
    print("=" * 60)

    await ctx.connect()

    print(f"Connected to room: {ctx.room.name}")

    room_name = ctx.room.name

    # This event is set when the room disconnects (i.e. when finish_call
    # deletes the room), which lets the entrypoint exit cleanly.
    shutdown_event = asyncio.Event()

    @ctx.room.on("disconnected")
    def on_room_disconnected(*args):
        shutdown_event.set()

    async def _handle_unexpected_disconnect(reason: str):
        # If finish_call already ran, ACTIVE_CALLS entry is already gone.
        state = ACTIVE_CALLS.pop(room_name, None)
        if state is None:
            return

        print(
            f"Customer disconnected before finish_call ran ({reason}). "
            f"Notifying backend so the campaign can continue."
        )

        # Try to save a partial transcript even for unexpected disconnects.
        session = state.get("session")
        transcript = _build_transcript(session) if session else ""

        await notify_call_complete(
            room_name,
            payload={
                "transcript": transcript or None,
                "customer_name": None,
                "appointment_date": None,
                "appointment_time": None,
            },
        )

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        if participant.identity == "customer":
            asyncio.create_task(
                _handle_unexpected_disconnect("customer hung up")
            )

    session = AgentSession(
        stt=sarvam.STT(),

        llm=openai.LLM(
            model="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY") or "",
            base_url="https://api.deepseek.com/v1",
        ),

        tts=sarvam.TTS(),
    )

    try:

        await session.start(
            room=ctx.room,
            agent=AppointmentBookingAgent(),
        )

        print("Session started")

        ACTIVE_CALLS[ctx.room.name] = {
            "session": session,
        }

        print(f"Registered active call: {ctx.room.name}")

        # Wait for the SIP customer to actually answer and join the room.
        # Since wait_until_answered=False, the room exists before the call
        # is picked up, so we must not greet until the participant is present.
        print("Waiting for customer participant to join...")
        customer_joined = False
        for _ in range(60):  # wait up to 60 seconds
            participants = ctx.room.remote_participants
            if any(p.identity == "customer" for p in participants.values()):
                customer_joined = True
                print("Customer participant joined — starting greeting.")
                break
            await asyncio.sleep(1)

        if not customer_joined:
            print("Timeout: customer never joined. Notifying backend and exiting.")
            ACTIVE_CALLS.pop(room_name, None)
            await notify_call_complete(
                room_name,
                payload={
                    "transcript": None,
                    "customer_name": None,
                    "appointment_date": None,
                    "appointment_time": None,
                },
            )
            shutdown_event.set()
        else:
            # Small buffer to let audio pipeline stabilize
            await asyncio.sleep(0.5)

            await session.generate_reply(
                instructions="""
Introduce yourself as "Hello, I'm calling from the appointment booking service."
Welcome the customer and ask for their name.
"""
            )

            print("Greeting sent")

        # Keep the entrypoint alive until the room is deleted.
        # finish_call deletes the LiveKit room → LiveKit fires the
        # 'disconnected' event → shutdown_event is set → we exit here.
        await shutdown_event.wait()

        print("Entrypoint shutting down.")

    finally:
        # Safety cleanup in case finish_call never ran (e.g. connection error).
        ACTIVE_CALLS.pop(ctx.room.name, None)
        print(f"Removed active call: {ctx.room.name}")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )