from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging

from apps.chat.models import ChatMessage
from apps.chat.serializers import ChatMessageSerializer, ChatHistorySerializer
from apps.chat.ai_engine import analyze_emotion
from apps.chat.crisis_detection import detect_crisis_with_emotion, get_crisis_response
from apps.chat.ai_response import get_ai_response, format_chat_history

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    """
    MAIN CHAT ENDPOINT - THE COMPLETE AI PIPELINE
    
    Endpoint: POST /api/chat/
    
    Request Body:
    {
        "message": "I'm feeling anxious about my exams"
    }
    
    Response:
    {
        "response": "I hear the anxiety you're feeling...",
        "emotion": {
            "primary_emotion": "fear",
            "sentiment_score": -0.42,
            "confidence": 0.78,
            "urgency": "high"
        },
        "risk_level": "SAFE",
        "is_crisis": false,
        "timestamp": "2024-01-15T10:30:00Z"
    }
    
    OR (if crisis detected):
    {
        "response": "I'm very concerned about what you've shared...",
        "resources": [
            {"name": "Emergency", "contact": "112"},
            ...
        ],
        "risk_level": "CRITICAL",
        "is_crisis": true,
        "immediate_action_required": true
    }
    """
    
    # ============================================
    # EXTRACT & VALIDATE INPUT
    # ============================================
    
    user = request.user
    user_message = request.data.get('message', '').strip()
    
    # Validate message exists
    if not user_message:
        return Response(
            {'error': 'Message cannot be empty'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate message length (prevent abuse)
    if len(user_message) > 2000:
        return Response(
            {'error': 'Message too long. Please keep messages under 2000 characters.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(user_message) < 3:
        return Response(
            {'error': 'Message too short. Please share more about what you\'re feeling.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    logger.info(f"User {user.email} sent message (length: {len(user_message)})")
    
    # ============================================
    # AI EMOTION ANALYSIS
    # ============================================
    
    try:
        emotion_data = analyze_emotion(user_message)
        logger.info(f"Emotion detected: {emotion_data['primary_emotion']} "
                   f"({emotion_data['confidence']*100:.0f}%)")
    except Exception as e:
        logger.error(f"Emotion analysis failed: {e}")
        # Continue with empty emotion data (non-critical failure)
        emotion_data = {
            'primary_emotion': 'neutral',
            'sentiment_score': 0.0,
            'confidence': 0.0,
            'urgency': 'low'
        }
    
    # ============================================
    # CRISIS DETECTION
    # ============================================
    
    try:
        crisis_data = detect_crisis_with_emotion(user_message, emotion_data)
        risk_level = crisis_data['risk_level']
        
        logger.info(f"Risk level: {risk_level} "
                   f"(confidence: {crisis_data['confidence']*100:.0f}%)")
        
        if crisis_data['triggers']:
            logger.warning(f"Crisis triggers: {crisis_data['triggers']}")
    
    except Exception as e:
        logger.error(f"Crisis detection failed: {e}")
        # Fail-safe: assume safe if detection fails
        crisis_data = {
            'risk_level': 'SAFE',
            'confidence': 0.0,
            'triggers': [],
            'recommendation': 'STANDARD_THERAPEUTIC_RESPONSE'
        }
        risk_level = 'SAFE'
    
    # ============================================
    # CRISIS RESPONSE (If Detected)
    # ============================================
    
    if risk_level in ['CRITICAL', 'HIGH']:
        logger.critical(f"CRISIS DETECTED for user {user.email}: {risk_level}")
        
        # Get crisis response with resources
        crisis_response = get_crisis_response(risk_level)
        
        # Save to database (with crisis flag)
        chat_message = ChatMessage.objects.create(
            user=user,
            message=user_message,
            response=crisis_response['response'],
            risk_level=risk_level,
            primary_emotion=emotion_data.get('primary_emotion'),
            sentiment_score=emotion_data.get('sentiment_score'),
            emotion_confidence=emotion_data.get('confidence')
        )
        
        # TODO: Send alert to admin/support team (implement later)
        # send_crisis_alert(user, chat_message)
        
        # Return crisis response immediately
        return Response({
            'response': crisis_response['response'],
            'resources': crisis_response['resources'],
            'risk_level': risk_level,
            'is_crisis': True,
            'immediate_action_required': crisis_response.get('immediate_action_required', False),
            'emotion': emotion_data,
            'timestamp': chat_message.created_at,
            'message_id': chat_message.id
        }, status=status.HTTP_201_CREATED)
    
    # ============================================
    # STEP 5: GET CONVERSATION HISTORY (Context)
    # ============================================
    
    try:
        # Get last 10 non-crisis messages for context
        history_queryset = ChatMessage.get_user_history(user, limit=10)
        conversation_history = format_chat_history(history_queryset)
        
        logger.info(f"Retrieved {len(conversation_history)//2} previous exchanges")
    
    except Exception as e:
        logger.error(f"Failed to retrieve history: {e}")
        conversation_history = []
    
    # ============================================
    # STEP 6: GENERATE AI THERAPEUTIC RESPONSE
    # ============================================
    
    try:
        ai_response = get_ai_response(
            user_message=user_message,
            conversation_history=conversation_history,
            emotion_data=emotion_data
        )
        
        logger.info(f"AI response generated (length: {len(ai_response)})")
    
    except Exception as e:
        logger.error(f"AI response generation failed: {e}")
        return Response(
            {
                'error': 'AI service temporarily unavailable. Please try again in a moment.',
                'fallback': True
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # ============================================
    # STEP 7: SAVE TO DATABASE
    # ============================================
    
    try:
        chat_message = ChatMessage.objects.create(
            user=user,
            message=user_message,
            response=ai_response,
            risk_level=risk_level,
            primary_emotion=emotion_data.get('primary_emotion'),
            sentiment_score=emotion_data.get('sentiment_score'),
            emotion_confidence=emotion_data.get('confidence')
        )
        
        logger.info(f"Chat message saved (ID: {chat_message.id})")
    
    except Exception as e:
        logger.error(f"Failed to save message: {e}")
        # Still return response even if save fails
        return Response({
            'response': ai_response,
            'emotion': emotion_data,
            'risk_level': risk_level,
            'is_crisis': False,
            'warning': 'Message not saved to history',
            'timestamp': None
        }, status=status.HTTP_201_CREATED)
    
    # ============================================
    # STEP 8: RETURN SUCCESS RESPONSE
    # ============================================
    
    return Response({
        'response': ai_response,
        'emotion': {
            'primary_emotion': emotion_data.get('primary_emotion'),
            'sentiment_score': emotion_data.get('sentiment_score'),
            'confidence': emotion_data.get('confidence'),
            'urgency': emotion_data.get('urgency'),
            'all_emotions': emotion_data.get('all_emotions', [])[:3]  # Top 3
        },
        'risk_level': risk_level,
        'is_crisis': False,
        'timestamp': chat_message.created_at,
        'message_id': chat_message.id
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_history(request):
    """
    GET CONVERSATION HISTORY
    
    Endpoint: GET /api/chat/history/
    Query Params:
        - limit: Number of messages to retrieve (default: 50, max: 100)
        - include_crisis: Include crisis messages (default: true)
    
    Response:
    {
        "count": 45,
        "messages": [
            {
                "id": 1,
                "message": "I'm feeling anxious",
                "response": "I hear you...",
                "risk_level": "SAFE",
                "primary_emotion": "fear",
                "created_at": "2024-01-15T10:30:00Z"
            },
            ...
        ]
    }
    """
    
    user = request.user
    
    # Parse query parameters
    limit = int(request.query_params.get('limit', 50))
    limit = min(limit, 100)  # Cap at 100
    
    include_crisis = request.query_params.get('include_crisis', 'true').lower() == 'true'
    
    # Build query
    queryset = ChatMessage.objects.filter(user=user)
    
    if not include_crisis:
        queryset = queryset.filter(risk_level='SAFE')
    
    # Order by newest first, limit results
    messages = queryset.order_by('-created_at')[:limit]
    
    # Serialize
    serializer = ChatHistorySerializer(messages, many=True)
    
    return Response({
        'count': messages.count(),
        'messages': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_chat_history(request):
    """
    DELETE ALL CHAT HISTORY (for user privacy)
    
    Endpoint: DELETE /api/chat/history/
    
    Deletes all messages for the authenticated user
    """
    
    user = request.user
    
    # Count before deleting
    count = ChatMessage.objects.filter(user=user).count()
    
    # Delete all messages
    ChatMessage.objects.filter(user=user).delete()
    
    logger.info(f"User {user.email} deleted {count} messages")
    
    return Response({
        'message': f'Successfully deleted {count} messages',
        'deleted_count': count
    }, status=status.HTTP_200_OK)
