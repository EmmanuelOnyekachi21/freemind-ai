"""
Test the full AI pipeline: Emotion Detection + Crisis Detection
"""

from apps.chat.ai_engine import analyze_emotion
from apps.chat.crisis_detection import detect_crisis_with_emotion

test_cases = [
    "I'm feeling really anxious about my exams tomorrow",
    "I want to kill myself, I can't do this anymore",
    "I'm so happy today! Everything is working out!",
    "This exam is killing me, so much stress",
    "I hate myself and feel hopeless",
]

print("=" * 70)
print("COMBINED AI PIPELINE TEST")
print("Emotion Detection (DistilRoBERTa) + Crisis Detection (NLP)")
print("=" * 70)

for message in test_cases:
    print(f"\n📝 Message: \"{message}\"")
    
    # Step 1: Emotion analysis (ML)
    emotion_data = analyze_emotion(message)
    print(f"🎯 Emotion: {emotion_data['primary_emotion']} ({emotion_data['confidence']*100:.0f}%)")
    
    # Step 2: Crisis detection (NLP + emotion context)
    crisis_data = detect_crisis_with_emotion(message, emotion_data)
    print(f"🚨 Risk Level: {crisis_data['risk_level']}")
    print(f"📊 Detection Confidence: {crisis_data['confidence']*100:.0f}%")
    print(f"💡 Recommendation: {crisis_data['recommendation']}")
    
    if crisis_data['triggers']:
        print(f"⚠️  Triggers: {', '.join(crisis_data['triggers'])}")
    
    print("-" * 70)