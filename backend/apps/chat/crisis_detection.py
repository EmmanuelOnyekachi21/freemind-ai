"""
CRISIS DETECTION SYSTEM
Multi-layer approach combining:
1. Keyword pattern matching (NLP)
2. Emotion analysis integration (ML)
3. Context-aware filtering (reduce false positives)
4. Multi-level risk classification
"""

import re
from typing import Dict, List
import spacy


nlp = spacy.load('en_core_web_sm')

# CRISIS KEYWORD DATABASE
# Organized by risk severity - this is NLP pattern recognition

CRISIS_KEYWORDS = {
    'CRITICAL': {
        'english': [
            # Direct suicide mentions (BASE FORMS)
            'kill myself', 'commit suicide', 'end my life', 'take my life',
            'suicide plan', 'how to die', 'way to die', 'end it all',  # "ways" → "way"
            'be off dead', 'world without I',  # "better" → "be", "me" → "I"
            'say goodbye', 'final goodbye', 'last message',
            'no reason to live', 'want to die', 'go to die', 'plan to die',
            'hang myself', 'overdose', 'jump off', 'no reason to live',
            
            # Common variations
            'buy pill', 'write note', 'final arrangement',  # Lemmatized forms
            'feel unstable',
        ],
        'pidgin': [
            # Nigerian Pidgin (these don't change much in lemmatization)
            'i wan die', 'make i just die', 'i go kill myself',
            'make i comot for this world', 'i don taya for life',
            'nothing dey for me again', 'i fit just end am',
            'make i just finish am', 'i go end myself', 'wan kpai', 'kpai myself',
        ]
    },
    
    'HIGH': {
        'english': [
            # Self-harm indicators (BASE FORMS)
            'hurt myself', 'cut myself', 'harm myself', 'self harm',
            'burn myself', 'punish myself',  # "burning" → "burn"
            'hate myself', 'deserve pain', 'want to hurt',
            
            # Severe hopelessness (BASE FORMS)
            'no point live', 'life be meaningless', 'can not go on',  # "living" → "live", "is" → "be"
            'give up everything', 'nothing matter',  # "matters" → "matter"
            'no hope leave', 'everyone hate I',  # "left" → "leave", "me" → "I"
            'burden to everyone', 'world hate I',
            'disappear forever', 'run away forever', 'leave forever',
            'can not do this anymore', 'can not take it anymore',  # "can't" → "can not"
            'everybody good without I', 'waste of space',  # "better" → "good"
            'can\'t go on', 'no hope', 'give up everything',
            'everyone hates me', 'worthless',
            'hurt myself', 'self harm', 'cut myself',
        
            # Nigerian context
            'this country don finish me', 'nobody go miss me',
        ],
        'pidgin': [
            'nobody go miss me', 'this country don finish me',
            'i no fit continue', 'wahala too much abeg',
            'make i just disappear', 'person wey born me no happy',
        ]
    },
    
    'MEDIUM': {
        'english': [
            # Moderate distress (BASE FORMS)
            'feel hopeless', 'very depressed', 'extremely anxious',
            'panic attack', 'can not cope', 'overwhelm completely',  # "can't" → "can not", "overwhelmed" → "overwhelm"
            'tired of try', 'nothing work', 'give up',  # "trying" → "try", "works" → "work", "giving" → "give"
            'do not want to wake up', 'wish i be not here',  # "don't" → "do not", "wasn't" → "be not"
            'wish i could sleep forever', 'tired of life',
            'feel hopeless', 'very depressed', 'extremely anxious',
            'panic attack', 'can\'t cope', 'overwhelmed',
            'nothing matters', 'tired of trying', 'too much to handle'
            
            # Isolation (BASE FORMS)
            'nobody care', 'all alone', 'no one understand',  # "cares" → "care", "understands" → "understand"
            'push everyone away', 'isolate myself',  # "pushing" → "push", "isolating" → "isolate"
            'nobody listen', 'invisible to everyone',  # "listens" → "listen"
        ],
        'pidgin': [
            'this life no balance', 'e don do for me',
            'wetin i dey do for this world', 'i don tire',
        ]
    }
}

# FALSE POSITIVE FILTERS
# These contexts suggest metaphorical usage, not literal crisis

METAPHORICAL_CONTEXTS = {
    'academic': [
        'exam', 'test', 'assignment', 'deadline', 'interview',
        'presentation', 'project', 'quiz', 'homework', 'study',  # "studying" → "study"
    ],
    
    'entertainment': [
        'movie', 'film', 'show', 'game', 'video', 'song',
        'book', 'story', 'comedy', 'funny', 'laugh',  # "laughing" → "laugh"
    ],
    
    'positive': [
        'excited', 'can not wait', 'look forward', 'eager',  # "can't" → "can not", "looking" → "look"
        'thrilled', 'amazing', 'wonderful', 'great',
    ],
    
    'figurative': [
        'die to see', 'kill I', 'to die for', 'dead tired',  # "dying" → "die", "me" → "I", "killing" → "kill"
        'kill it', 'slay', 'murder', 'destroy',  # "slaying" → "slay", "murdered" → "murder", "destroyed" → "destroy"
    ],
}

def lemmatize_text(text):
    """
    Converts words to their base forms (lemmas)

    Examples:
        "killing" → "kill"
        "wanted" → "want"
        "myself" → "myself" (already base form)
    
    Args:
        text (str): Original message
        
    Returns:
        str: Lemmatized text
    """
    try:
        # Process text with spaCy
        doc = nlp(text.lower())
        
        # Extract lemmas (base forms)
        lemmas = [token.lemma_ for token in doc]
        
        # Join back into sentence
        return " ".join(lemmas)
    
    except Exception as e:
        # If lemmatization fails, return original
        print(f"Lemmatization error: {e}")
        return text

def detect_crisis_enhanced(message):
    """
    ENHANCED CRISIS DETECTION

    Two pass detection:
    1. Check original message (catches exact matches - fast)
    2. Check lemmatized message (catches variations - thorough)
    
    Returns highest risk level found from both passes
    
    Args:
        message (str): User's message
        
    Returns:
        str: Risk level - 'SAFE', 'MEDIUM', 'HIGH', or 'CRITICAL'
    
    Examples:
        "I want to kill myself" → CRITICAL (original match)
        "I am killing myself" → CRITICAL (lemmatized match)
        "This exam killed me" → SAFE (metaphorical context)
    """
    if not message or len(message.strip()) < 3:
        return "SAFE"
    
    #  PASS 1: Check original message (fast path)
    # This catches exact matches immediately
    risk_original = detect_crisis_level(message)
    
    # If we found critical/high risk already, return immediately
    if risk_original in ['CRITICAL', 'HIGH']:
        return risk_original
    try:
        # Pass 2: Lemmatize and check again (catches variations)
        lemmatized_message = lemmatize_text(message)

        if lemmatized_message != message.lower():
            risk_lemmatized = detect_crisis_level(lemmatized_message)

            risk_levels = ['SAFE', 'MEDIUM', 'HIGH', 'CRITICAL']
                    
            idx_original = risk_levels.index(risk_original)
            idx_lemmatized = risk_levels.index(risk_lemmatized)
            
            if idx_lemmatized > idx_original:
                return risk_lemmatized
    except Exception as e:
        print(f"Enhanced detection error: {e}")
    
    return risk_original

def detect_crisis_level(message):
    """
    MULTI-LAYER CRISIS DETECTION
    
    Analyzes message for crisis indicators using:
    1. Direct keyword matching
    2. Contextual analysis
    3. Pattern recognition
    
    Args:
        message (str): User's message
        
    Returns:
        str: Risk level - 'SAFE', 'MEDIUM', 'HIGH', or 'CRITICAL'
    
    Example:
        >>> detect_crisis_level("I want to kill myself")
        'CRITICAL'
        
        >>> detect_crisis_level("This exam is killing me")
        'SAFE'  # Metaphorical context
    """
    if not message or len(message.strip()) <= 3:
        return 'SAFE'
    message_lower = message.lower()

    # Check for metaphorical context first
    # If message contains metaphorical indicators, be cautious about flagging
    is_metaphorical = check_metaphorical_context(message_lower)

    # Check critical keywords
    for keyword in CRISIS_KEYWORDS['CRITICAL']['english'] + CRISIS_KEYWORDS['CRITICAL']['pidgin']:
        if keyword in message_lower:
            # If metaphorical context, downgrade the severity
            if is_metaphorical:
                return 'HIGH'
            return 'CRITICAL'
    
    # Check HIGH risk keywords
    for keyword in CRISIS_KEYWORDS['HIGH']['english'] + CRISIS_KEYWORDS['HIGH']['pidgin']:
        if keyword in message_lower:
            if is_metaphorical:
                return 'MEDIUM'
            return 'HIGH'
    
    
    # Check MEDIUM risk keywords
    for keyword in CRISIS_KEYWORDS['MEDIUM']['english'] + CRISIS_KEYWORDS['MEDIUM']['pidgin']:
        if keyword in message_lower:
            if is_metaphorical:
                return 'SAFE'  # Likely just venting about stress
            return 'MEDIUM'
    
    # No crisis indicators found
    return 'SAFE'

def check_metaphorical_context(message):
    """
    Checks if crisis words are used metaphorically.

    Returns True if message contains metaphorically context indicators
    """    
    for key, keywords in METAPHORICAL_CONTEXTS.items():
        for keyword in keywords:
            if keyword in message:
                return True
    
    return False

def detect_crisis_with_emotion(message, emotion_data):
    """
    Combines enhanced keyword detection with emotion analysis
    
    Args:
        message (str): User's message
        emotion_data (dict): Output from analyze_user_emotion()
        
    Returns:
        dict: {
            'risk_level': str,
            'confidence': float,
            'triggers': list,
            'recommendation': str
        }
    """
    # Get base risk from keywords
    keyword_risk = detect_crisis_enhanced(message)

    # Analyze emotion context
    primary_emotion = emotion_data.get('primary_emotion', 'neutral')
    emotion_confidence = emotion_data.get('confidence', 0)
    urgency = emotion_data.get('urgency', 'low')

    # Identify specific triggers
    triggers = identify_triggers(message)

    # Adjust risk based on emotion analyses
    # strong negatives emotions +  crisis keyword = higher confidence

    if keyword_risk in ['HIGH', 'CRITICAL']:
        if primary_emotion in [
            'fear', 'sadness'
        ] and emotion_confidence > 0.6:
            # Emotion confirms keyword risk
            confidence = 0.9
        elif primary_emotion == 'anger' and emotion_confidence > 0.7:
            confidence = 0.75
        else:
            confidence = 0.6
    elif keyword_risk == 'MEDIUM':
        if urgency == 'high' and primary_emotion in ['fear', 'sadness']:
            # Emotion suggests higher risk than keywords alone
            keyword_risk = 'HIGH'
            confidence = 0.7
        else:
            confidence = 0.5
    
    else:  # SAFE
        if urgency == 'high' and primary_emotion in ['fear', 'sadness']:
            # Emotion detected distress without crisis keywords
            keyword_risk = 'MEDIUM'
            confidence = 0.4
        else:
            confidence = 0.95
    
    # Generate recommendation
    recommendation = get_risk_recommendation(keyword_risk, emotion_data)

    return {
        'risk_level': keyword_risk,
        'confidence': round(confidence, 2),
        'triggers': triggers,
        'recommendation': recommendation,
        'emotion_context': {
            'primary_emotion': primary_emotion,
            'emotion_confidence': emotion_confidence,
            'urgency': urgency
        }
    }

def identify_triggers(message):
    """
    Identify specific crisis triggers in message.

    Returns list of detected tigger categories
    """

    triggers = []
    message_lower = message.lower()

    for risk_level, languages in CRISIS_KEYWORDS.items():
        for _, keywords in languages.items():
            for keyword in keywords:
                if keyword in message_lower:
                    triggers.append(f"{risk_level}: '{keyword}'")
    
    return triggers[:5]  # Return the top 5 to avoid overwhelming output

def get_risk_recommendation(risk_level, emotion_data):
    """
    Get appropriate response recommendation based on risk level.
    """
    if risk_level == 'CRITICAL':
        return "IMMEDIATE_CRISIS_RESPONSE"
    elif risk_level == 'HIGH':
        return "URGENT_SUPPORT_NEEDED"
    elif risk_level == 'MEDIUM':
        return "ELEVATED_CONCERN"
    else:
        return "STANDARD_THERAPEUTIC_RESPONSE"

def get_crisis_response(risk_level):
    """
    Generate crisis-appropriate response with resources
    
    Args:
        risk_level (str): 'CRITICAL', 'HIGH', 'MEDIUM', or 'SAFE'
        
    Returns:
        dict: Response message and resources
    """
    if risk_level == 'CRITICAL':
        return {
            'response': """I'm truly concerned about what you're sharing with me. Your safety and wellbeing are what matters most right now.

You don't have to face this moment alone. Help is available, and people who care want to support you. Please reach out to one of the emergency services below—they're trained to help and are available right now.

If you're in immediate danger, please call emergency services (112 or 767) right away. 

We're also notifying our support team, and someone from our team may reach out to you to check in. You're valued, and we're here for you. 💙""",
            
            'resources': [
                {
                    'name': 'National Emergency',
                    'contact': '112 or 767',
                    'available': '24/7',
                    'type': 'emergency'
                },
                {
                    'name': 'Mentally Aware Nigeria (MANI)',
                    'contact': '+2348091116264',
                    'available': '24/7',
                    'type': 'crisis_line'
                },
                {
                    'name': 'LUTH Psychiatry Emergency',
                    'contact': '+234 1 593 6394',
                    'available': '24/7',
                    'type': 'hospital'
                },
                {
                    'name': 'She Writes Woman Crisis Line',
                    'contact': '+234 813 951 3888',
                    'available': 'Mon-Fri 10am-6pm',
                    'type': 'crisis_line'
                },
            ],
            
            'escalate': True,
            'immediate_action_required': True
        }
    elif risk_level == 'HIGH':
        return {
            'response': """I hear you, and I can sense that you're going through something really difficult right now. What you're feeling is valid and important.

The fact that you're reaching out shows strength. You don't have to handle this alone—support is available, and it's okay to ask for help.

If you're feeling overwhelmed, please consider connecting with one of the resources below. They're trained professionals who understand what you're going through and are ready to listen and support you.

Our team may also reach out to check in on you. You matter. 💙""",
            
            'resources': [
                {
                    'name': 'Mentally Aware Nigeria (MANI)',
                    'contact': '+234 809 210 6493',
                    'available': '24/7',
                    'type': 'crisis_line'
                },
                {
                    'name': 'She Writes Woman',
                    'contact': '+234 813 951 3888',
                    'available': 'Mon-Fri 10am-6pm',
                    'type': 'support_line'
                },
                {
                    'name': 'The Agbeyega Care Centre',
                    'contact': '+234 803 333 7574',
                    'available': 'By appointment',
                    'type': 'therapy_center'
                },
            ],
            
            'escalate': True,
            'immediate_action_required': False
        }
    
    elif risk_level == 'MEDIUM':
        return {
            'response': """It sounds like you're dealing with some challenging feelings right now, and I appreciate you sharing that with me. That takes courage.

Let's work through this together. I'm here to listen and support you. Sometimes talking through what's happening can help clarify things and make them feel more manageable.

If you'd like additional support, there are resources available to help. Remember, seeking help is a sign of strength, not weakness. 💙""",
            
            'resources': [
                {
                    'name': 'Mental Health Foundation Nigeria',
                    'contact': '+234 814 652 3537',
                    'available': 'Mon-Fri 9am-5pm',
                    'type': 'information'
                }
            ],
            
            'escalate': False,
            'immediate_action_required': False
        }
    
    else:  # SAFE
        return None  # No crisis response needed


# TEST FUNCTION
if __name__ == "__main__":
    """
    Test crisis detection with various scenarios
    Run: python backend/apps/chat/crisis_detection.py
    """
    
    test_cases = [
        # Critical cases
        ("I want to kill myself", "CRITICAL"),
        ("I'm going to end my life tonight", "CRITICAL"),
        ("I wan die abeg, nothing dey for me again", "CRITICAL"),
        
        # High risk cases
        ("I hate myself and want to hurt myself", "HIGH"),
        ("Nobody would miss me if I disappeared", "HIGH"),
        ("I'm planning to cut myself", "HIGH"),
        
        # Medium risk cases
        ("I feel hopeless and can't cope anymore", "MEDIUM"),
        ("I'm very depressed and nobody understands", "MEDIUM"),
        
        # False positives (should be SAFE)
        ("This exam is killing me!", "SAFE"),  # Metaphorical
        ("I'm dying to see that movie", "SAFE"),  # Figurative
        ("Studying is making me want to die lol", "SAFE"),  # Hyperbole + context
        
        # Safe cases
        ("I'm feeling a bit stressed about work", "SAFE"),
        ("Having a good day today", "SAFE"),
    ]
    
    print("=" * 70)
    print("CRISIS DETECTION SYSTEM TEST")
    print("=" * 70)
    
    correct = 0
    total = len(test_cases)
    
    for message, expected in test_cases:
        detected = detect_crisis_level(message)
        is_correct = detected == expected
        correct += is_correct
        
        status = "✅" if is_correct else "❌"
        print(f"\n{status} Message: \"{message}\"")
        print(f"   Expected: {expected} | Detected: {detected}")
        
        if detected in ['HIGH', 'CRITICAL']:
            response = get_crisis_response(detected)
            print(f"   Resources: {len(response['resources'])} available")
    
    print("\n" + "=" * 70)
    print(f"ACCURACY: {correct}/{total} ({correct/total*100:.1f}%)")
    print("=" * 70)

    # Add to your existing test section
print("\n" + "=" * 70)
print("LEMMATIZATION ENHANCEMENT TEST")
print("=" * 70)

lemma_test_cases = [
    ("I want to kill myself", "CRITICAL"),
    ("I am killing myself", "CRITICAL"),  # Should now detect!
    ("I wanted to end my life", "CRITICAL"),  # Should now detect!
    ("I'm hurting myself", "HIGH"),  # Should now detect!
    ("I was feeling hopeless", "MEDIUM"),  # Should now detect!
]

for message, expected in lemma_test_cases:
    detected = detect_crisis_enhanced(message)
    is_correct = detected == expected
    status = "✅" if is_correct else "❌"
    
    
    
    print(f"\n{status} Original: \"{message}\"")
    print(f"   Expected: {expected} | Detected: {detected}")

