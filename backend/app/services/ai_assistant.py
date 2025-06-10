# Contents for backend/app/services/ai_assistant.py
import asyncio
import random
import datetime

class AIAssistantService:
    def __init__(self):
        self.dummy_responses = [
            "That's an interesting point!",
            "Could you tell me more about that?",
            "I'm still learning, but I'll try my best to understand.",
            "Let me think about that for a moment...",
            "Fascinating! What else is on your mind?",
            "I see. And how does that make you feel? (Just kidding, I'm a basic AI!)",
            "Processing... please stand by.",
            "Hmm, that's a good question."
        ]
        self.ai_sid = "AI_ASSISTANT_SID"

    async def generate_dummy_response(self, user_message: str, user_sid: str) -> dict:
        delay = random.uniform(0.5, 2.5)
        await asyncio.sleep(delay)
        response_text = random.choice(self.dummy_responses)

        if "hello" in user_message.lower() or "hi" in user_message.lower():
            response_text = "Hello there! How can I help you today?"
        elif "bye" in user_message.lower():
            response_text = "Goodbye! Have a great day."
        elif "?" in user_message:
            response_text = "That's a great question! Unfortunately, I'm just a dummy AI."

        return {
            "sender_sid": self.ai_sid,
            "text": response_text,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "is_ai": True
        }

ai_assistant_service = AIAssistantService()
