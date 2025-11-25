"""
AI Engine - Emotion Detection using Transformer Model
Uses DistilRoBERTa fine-tuned on emotion classification

Model: j-hartmann/emotion-english-distilroberta-base
"""

from transformers import pipeline
import logging

# Suppress transformer warnings
logging.getLogger("transformers").setLevel(logging.ERROR)

# Initialize emotion classifier (loads once, then cached.)
# This is a TRANSFORMER MODEL - 82M parameters.
print("Loading emotional detection model... (one-time setup)")
emotional_classifier = pipeline(
    "text-classification",
    model='/home/d3mxn/Documents/emotion_model',
    top_k = None
)
print("Emotion model loaded successfully!")

def analyze_emotion(text):
    """
    TRANSFORMER-BASED EMOTION DETECTION
    
    Uses DistilRoBERTa (82M parameter neural network) fine-tuned
    on emotion classification task with GoEmotions dataset
    
    Detects 7 emotions: anger, disgust, fear, joy, neutral, sadness, surprise
    
    Args:
        message (str): User's message
        
    Returns:
        dict: {
            'primary_emotion': str,      # dominant emotion
            'emotion_scores': dict,      # all emotion probabilities
            'sentiment_score': float,    # derived overall sentiment
            'confidence': float,         # confidence in primary emotion
            'urgency': str,             # low, medium, high
            'all_emotions': list        # ranked list of emotions
        }
    
    Example:
        >>> analyze_user_emotion("I'm feeling really anxious and scared")
        {
            'primary_emotion': 'fear',
            'emotion_scores': {
                'fear': 0.78,
                'sadness': 0.15,
                'neutral': 0.04,
                ...
            },
            'confidence': 0.78,
            'urgency': 'high'
        }
    """
    # Handle empty messages
    if not text and len(text.strip()) < 3:
        return {
            'primary_emotion': 'neutral',
            'emotion_scores': { 'neutral': 1.0 },
            'sentiment_score': 0.0,
            'confidence_score': 0.0,
            'urgency': 'low',
            'all_emotions': []
        }
    
    try:
        # RUn transformal model inference
        results = emotional_classifier(text)[0]

        # Parse result in a clean format
        emotion_scores = {
            item['label']: round(item['score'], 4)
            for item in results
        }

        # Identify primary emotion (highest score)
        primary_emotion = max(emotion_scores, key=emotion_scores.get)
        confidence = emotion_scores[primary_emotion]

        # Calculate overall sentiment
        # Positive emotions: joy
        # Negative emotions: anger, disgust, fear, sadness
        # Neutral: neutral, surprise (can be either)
        positive_score = emotion_scores.get('joy', 0)
        negative_score = sum(
            [
                emotion_scores.get('anger', 0),
                emotion_scores.get('disgust'),
                emotion_scores.get('fear', 0),
                emotion_scores.get('sadness', 0)
            ]
        )
        neutral_score = emotion_scores.get('neutral', 0)

        # Calculates sentiment score: from -1 to 1
        # -1 -> negative sentiment
        # 0 -> neutral
        # +1 -> positive sentiment
        if positive_score + negative_score > 0:
            sentiment_score = (positive_score - negative_score) / (positive_score + negative_score)
        else:
            sentiment_score = 0.0
        
        # Determine urgency based on emotion + confidence
        urgency = calculate_urgency(primary_emotion, confidence, emotion_scores)

        # Rank all emotions, from highest score to lowest
        all_emotions = sorted(
            [{ 'emotion': k, 'score': v } for k, v in emotion_scores.items()],
            key=lambda x: x['score'],
            reverse=True
        )

        return {
            'primary_emotion': primary_emotion,
            'emotion_scores': emotion_scores,
            'sentiment_score': round(sentiment_score, 3),
            'confidence': round(confidence, 3),
            'urgency': urgency,
            'all_emotions': all_emotions
        }
    except Exception as e:
        # Fallback if model fails
        print(f"Emotion detection error")
        return {
            'primary_emotion': 'neutral',
            'emotion_scores': {'neutral': 1.0},
            'sentiment_score': 0.0,
            'confidence': 0.0,
            'urgency': 'low',
            'all_emotions': [],
            'error': str(e)
        }


def calculate_urgency(primary_emotion, confidence, emotion_scores):
    """
    URGENCY CLASSIFICATION

    Determines response urgency based on detected emotions

    Returns: 'low', 'medium', or 'high'
    """

    # High urgency emotions
    if primary_emotion in ['fear', 'sadness'] and confidence > 0.6:
        return 'high'
    
    # Medium urgency emotions
    if primary_emotion in ['anger', 'disgust'] and confidence > 0.5:
        return 'medium'
    
    # if multiple negative emotions are present
    negative_emotions = [
        'anger',
        'disgust',
        'fear',
        'sadness'
    ]
    negative_total = sum(
        emotion_scores.get(e, 0)
        for e in negative_emotions
    )

    if negative_total > 0.7:
        return 'high'
    elif negative_total < 0.4:
        return 'medium'
    return 'low'

def adapt_prompt_to_emotion(base_prompt, emotion_data):
    """
    DYNAMIC PROMPT ENGINEERING
    
    Adapts AI behavior based on detected emotion
    Different strategies for different emotions
    
    Args:
        base_prompt (str): Base therapist system prompt
        emotion_data (dict): Output from analyze_user_emotion()
        
    Returns:
        str: Emotion-adapted system prompt
    """
    primary_emotion = emotion_data['primary_emotion']
    confidence = emotion_data['confidence']
    urgency = emotion_data['urgency']

    # Build emotion specific adaptations
    adaptations = []

    # FEAR (anxiety, worry, panic)
    if primary_emotion == 'fear':
        adaptations.append("""
DETECTED EMOTION: FEAR/ANXIETY

ADAPTED RESPONSE STRATEGY:
- Prioritize grounding and safety
- Use calming, reassuring language
- Offer immediate anxiety-reduction techniques
- Avoid overwhelming with too many questions
- Create sense of control

Recommended interventions: Breathing exercises, grounding (5-4-3-2-1), progressive muscle relaxation

Example opening: "I hear how anxious you're feeling. Let's take this one step at a time. First, let's try something to help calm your nervous system."
        """)
    
    # SADNESS (depression, grief, loss)
    elif primary_emotion == 'sadness':
        adaptations.append("""
DETECTED EMOTION: SADNESS/DEPRESSION

ADAPTED RESPONSE STRATEGY:
- Lead with deep validation and empathy
- Acknowledge the pain without rushing to fix
- Use gentle, warm language
- Normalize the feeling of sadness
- Explore underlying causes slowly
- Offer hope without dismissing pain

Recommended interventions: Gratitude journaling, behavioral activation, self-compassion

Example opening: "I hear the sadness in your message. It's okay to feel this way, and you're not alone. Can you share what's been weighing most heavily on your heart?"
        """)
    
    # ANGER (frustration, irritation)
    elif primary_emotion == 'anger':
        adaptations.append("""
DETECTED EMOTION: ANGER/FRUSTRATION

ADAPTED RESPONSE STRATEGY:
- Validate the anger as legitimate
- Help identify what's underneath (often hurt, fear, or unmet needs)
- Offer healthy expression outlets
- Avoid dismissing or minimizing
- Help channel anger constructively

Recommended interventions: Anger diary, physical activity, assertiveness training

Example opening: "I hear your frustration, and it sounds like you have good reasons to feel angry. What's at the core of what's upsetting you?"
        """)
    
    # JOY (happiness, excitement)
    elif primary_emotion == 'joy':
        adaptations.append("""
DETECTED EMOTION: JOY/HAPPINESS

ADAPTED RESPONSE STRATEGY:
- Celebrate the positive moment genuinely
- Explore what contributed to this feeling
- Reinforce healthy patterns and coping strategies
- Build on momentum
- Help them savor the positive

Example opening: "It's wonderful to hear you're feeling good! What's been going well for you?"
        """)
    
    # DISGUST (revulsion, contempt)
    elif primary_emotion == 'disgust':
        adaptations.append("""
DETECTED EMOTION: DISGUST

ADAPTED RESPONSE STRATEGY:
- Explore what's triggering this strong reaction
- Often relates to violation of values or boundaries
- Validate their standards while exploring flexibility
- Help process the strong reaction

Example opening: "It sounds like something has really bothered you. What happened that triggered such a strong reaction?"
        """)
    
    # SURPRISE (unexpected events)
    elif primary_emotion == 'surprise':
        adaptations.append("""
DETECTED EMOTION: SURPRISE

ADAPTED RESPONSE STRATEGY:
- Help process the unexpected event
- Explore whether surprise is positive or negative
- Support adjustment to new information

Example opening: "It sounds like something unexpected happened. Tell me more about what surprised you."
        """)
    
    # NEUTRAL or LOW CONFIDENCE
    else:
        adaptations.append("""
DETECTED EMOTION: NEUTRAL or UNCLEAR

ADAPTED RESPONSE STRATEGY:
- Standard therapeutic approach
- Ask open-ended questions to understand more
- Let the conversation develop naturally
- Stay warm and supportive
        """)
    
    # Add urgency note if high
    if urgency == 'high':
        adaptations.append("""
⚠️ HIGH URGENCY DETECTED
- User may be in significant distress
- Prioritize immediate support and safety
- Consider crisis resources if appropriate
- Be especially gentle and validating
        """)
    
    # Combine base prompt with adaptations
    adapted = base_prompt + "\n\n" + "\n".join(adaptations)
    
    return adapted

def get_emotion_insights(emotion_data):
    """
    HUMAN-READABLE EMOTION SUMMARY
    
    Converts technical emotion scores into insights for user/therapist
    
    Returns: str - Plain English summary
    """
    primary = emotion_data['primary_emotion']
    confidence = emotion_data['confidence']
    all_emotions = emotion_data['all_emotions']

    # Build insight message
    insight = (
        f"Primary emotion detected: "
        f"{primary.upper()} ({confidence*100:.0f}% confidence)"
    )

    # Add secondary emotions if significant
    secondary = [
        e for e in all_emotions[1:3] if e['score'] > 0.3
    ]
    if secondary:
        secondary_names = [e['emotion'] for e in secondary]
        insight += f"\nAlso detecting: {', '.join(secondary_names)}"
    return insight

# TEST FUNCTION
if __name__ == "__main__":
    """
    Test the emotion detector with various messages
    Run: python backend/apps/chat/ai_engine.py
    """
    
    test_messages = [
        "I'm feeling really anxious about my exams tomorrow",
        "I'm so happy today! Everything is going well!",
        "I don't know what to do anymore. Life feels pointless.",
        "I'm so angry at my boss for treating me unfairly",
        "I'm scared I'll fail and disappoint everyone",
        "Just checking in, nothing special today",
        "I dey feel very sad. Nothing dey work for this country.",
        "I wan kpai myself today.",
        "This is disgusting! I can't believe they did this!",
        """I keep telling everyone I’m fine, and they smile because they want to believe it.
But the truth is, I only sound fine when I rehearse the words long enough.
It’s strange—people say I’ve been doing better lately, even though I’m just getting better at being invisible.
I guess that counts as progress in some way.
Yesterday someone told me they were proud of how strong I’ve become, and I thanked them, even though I wasn’t sure if they were praising the strength it takes to keep going,
or the strength it takes to pretend I still want to.
The hopeful part is that I still wake up every morning; the sad part is that I don’t remember wanting to.
So yes, I suppose everything is improving—
just not in any way that helps."""
    ]
    
    print("=" * 70)
    print("TRANSFORMER-BASED EMOTION DETECTION TEST")
    print("Model: DistilRoBERTa (82M parameters)")
    print("=" * 70)
    
    for message in test_messages:
        print(f"\n📝 Message: \"{message}\"")
        emotion = analyze_emotion(message)
        
        print(f"🎯 Primary Emotion: {emotion['primary_emotion'].upper()}")
        print(f"📊 Confidence: {emotion['confidence']*100:.1f}%")
        print(f"😊 Sentiment Score: {emotion['sentiment_score']:.3f}")
        print(f"⚡ Urgency: {emotion['urgency']}")
        
        # Show top 3 emotions
        print(f"📈 Top 3 Emotions:")
        for i, e in enumerate(emotion['all_emotions'][:3], 1):
            print(f"   {i}. {e['emotion']}: {e['score']*100:.1f}%")
        
        print("-" * 70)

