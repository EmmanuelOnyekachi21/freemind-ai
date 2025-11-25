"""
CHAT SERIALIZERS
Convert ChatMessage models to/from JSON
"""

from rest_framework import serializers
from apps.chat.models import ChatMessage

class ChatMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for ChatMessage model
    
    Converts database objects to JSON for API responses
    """
    user_name = serializers.ReadOnlyField(source="user.get_full_name")
    emotion_display = serializers.ReadOnlyField(source='get_emotion_display')
    is_crisis = serializers.ReadOnlyField()
    
    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'message',
            'response',
            'risk_level',
            'primary_emotion',
            'sentiment_score',
            'emotion_confidence',
            'emotion_display',
            'is_crisis',
            'created_at',
            'user_name',
        ]
        read_only_fields = [
            'id',
            'response',
            'risk_level',
            'primary_emotion',
            'sentiment_score',
            'emotion_confidence',
            'created_at',
        ]

class ChatHistorySerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for chat history
    Shows only essential fields
    """
    
    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'message',
            'response',
            'risk_level',
            'primary_emotion',
            'created_at',
        ]
