"""
AI RESPONSE GENERATOR
Integrates Groq LLM for therapeutic conversation

This module orchestrates:
1. Conversation history formatting
2. Prompt adaptation based on emotion
3. Groq API calls
4. Error handling and fallbacks
"""

import os
from groq import Groq
from decouple import config
import logging
from apps.chat.prompts import FULL_THERAPIST_PROMPT
from apps.chat.ai_engine import adapt_prompt_to_emotion, analyze_emotion

# setup logger
logger = logging.getLogger(__name__)

try:
    groq_client = Groq(
        api_key=config('GROQ_API_KEY')
    )
    print('GROQ client initialized successfully')
except Exception as e:
    logger.error(f"Failed to initialize Groq client: {e}")
    groq_client = None


def format_chat_history(messages_queryset):
    """
    FORMAT CONVERSATION HISTORY

    Converts Django QuerySet of ChatMessage objects into format Groq expects
    
    Args:
        messages_queryset: QuerySet of ChatMessage objects (ordered chronologically)
        
    Returns:
        List of message dicts in format:
        [
            {"role": "user", "content": "I'm feeling sad"},
            {"role": "assistant", "content": "I hear you..."},
            ...
        ]
    
    Example:
        history = ChatMessage.objects.filter(user=user)[:10]
        formatted = format_chat_history(history)
    """

    formatted_messages = []

    for msg in messages_queryset:
        # Add user message
        formatted_messages.append(
            {
                "role": "user",
                "content": msg.message
            }
        )

        # Add ai response
        formatted_messages.append({
            'role': 'assistant',
            'content': msg.response
        })

    return formatted_messages

def get_ai_response(
    user_message,
    conversation_history,
    emotion_data,
    max_retries=2
):
    """
    MAIN AI RESPONSE FUNCTION
    
    Generates therapeutic response using Groq LLM
    
    This is where the magic happens:
    1. Adapts prompt based on user's emotion
    2. Builds full conversation context
    3. Calls Groq's 70B parameter model
    4. Returns empathetic, contextual response
    
    Args:
        user_message (str): Current message from user
        conversation_history (list): Previous messages in conversation
        emotion_data (dict): Output from analyze_user_emotion()
        max_retries (int): Number of retry attempts if API fails
        
    Returns:
        str: AI-generated therapeutic response
        
    Example:
        emotion = analyze_user_emotion("I'm anxious")
        response = get_ai_response(
            user_message="I'm anxious about exams",
            conversation_history=[],
            emotion_data=emotion
        )
        # Returns: "I hear the anxiety you're feeling..."
    """

    # Check if groq has been initialized yet
    if groq_client is None:
        logger.error("Groq client not initialized")
        return get_fallback_response()
    try:
        adapted_prompt = adapt_prompt_to_emotion(
            FULL_THERAPIST_PROMPT, emotion_data
        )

        # Build complete message array for Groq
        messages = [
            # System message - defines AI behaviour
            {
                "role": "system",
                "content": adapted_prompt
            }
        ]

        # STEP 3: Add conversation history (context)
        # This allows AI to remember previous messages
        messages.extend(conversation_history)

        # Add current user's message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Call Groq API
        # This is the actual AI inference using 70B parameters
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            
            # Temperature controls randomness
            # 0.7 = balanced (not too robotic, not too random)
            temperature=0.7,
            
            # Max tokens = max response length
            # ~300 tokens ≈ 150-200 words
            max_tokens=300,
            
            # Top-p sampling (nucleus sampling)
            # 0.9 = consider top 90% probable tokens
            top_p=0.9,
            
            # Stop sequences (optional - stops generation if these appear)
            stop=None
        )
        
        # STEP 6: Extract response text
        ai_response = completion.choices[0].message.content.strip()
        
        # STEP 7: Validate response (basic checks)
        if not ai_response or len(ai_response) < 10:
            logger.warning("AI response too short, using fallback")
            return get_fallback_response()
        
        return ai_response
    
    except Exception as e:
        # BLOCK 4: ERROR HANDLING
        logger.error(f"Groq API error: {e}")
        
        # Retry logic
        if max_retries > 0:
            logger.info(f"Retrying... ({max_retries} attempts left)")
            return get_ai_response(
                user_message,
                conversation_history,
                emotion_data,
                max_retries - 1
            )
        
        # If all retries failed, return fallback
        return get_fallback_response()


def get_fallback_response():
    """
    FALLBACK RESPONSE (when AI unavailable)
    
    Returns a helpful message when Groq API is down or fails
    This ensures the app never completely breaks
    """
    
    return """I apologize, but I'm having trouble connecting right now. Please try again in a moment.

If you're in crisis and need immediate help, please reach out to:
- National Emergency: 112 or 767
- Mentally Aware Nigeria: +234 809 210 6493 (24/7)
- LUTH Psychiatry: +234 1 593 6394

If this is not urgent, please try sending your message again, and I'll do my best to support you."""


def test_groq_integration():
    """
    TEST FUNCTION
    Verify Groq integration works end-to-end
    """
    
    print("=" * 70)
    print("GROQ LLM INTEGRATION TEST")
    print("=" * 70)
    
    # Test case 1: Simple message, no history
    print("\n📝 Test 1: First message (no history)")
    print("-" * 70)
    
    
    test_message = "I'm feeling really anxious about my exams tomorrow"
    emotion = analyze_emotion(test_message)
    
    print(f"Message: \"{test_message}\"")
    print(f"Emotion: {emotion['primary_emotion']} ({emotion['confidence']*100:.0f}%)")
    print("\nCalling Groq AI...")
    
    response = get_ai_response(
        user_message=test_message,
        conversation_history=[],
        emotion_data=emotion
    )
    
    print(f"\n🤖 AI Response:\n{response}")
    print("-" * 70)
    
    # Test case 2: With conversation history
    print("\n📝 Test 2: Follow-up message (with history)")
    print("-" * 70)
    
    history = [
        {"role": "user", "content": "I'm feeling really anxious about my exams tomorrow"},
        {"role": "assistant", "content": response}
    ]
    
    followup = "What if I fail?"
    emotion2 = analyze_emotion(followup)
    
    print(f"Follow-up: \"{followup}\"")
    print("\nCalling Groq AI with context...")
    
    response2 = get_ai_response(
        user_message=followup,
        conversation_history=history,
        emotion_data=emotion2
    )
    
    print(f"\n🤖 AI Response:\n{response2}")
    print("-" * 70)
    
    # Test case 3: Nigerian Pidgin
    print("\n📝 Test 3: Pidgin English")
    print("-" * 70)
    
    pidgin_msg = "I dey feel very sad. My mama dey pressure me say make I marry."
    emotion3 = analyze_emotion(pidgin_msg)
    
    print(f"Message: \"{pidgin_msg}\"")
    print("\nCalling Groq AI...")
    
    response3 = get_ai_response(
        user_message=pidgin_msg,
        conversation_history=[],
        emotion_data=emotion3
    )
    
    print(f"\n🤖 AI Response:\n{response3}")
    print("-" * 70)
    
    print("\n" + "=" * 70)
    print("✅ GROQ INTEGRATION TEST COMPLETE")
    print("=" * 70)


# Run test when script executed directly
if __name__ == "__main__":
    test_groq_integration()


