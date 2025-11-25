from django.db import models

# Create your models here.
from apps.users.models import Account


class ChatMessage(models.Model):
    """
    Individual message in a conversation
    
    Each row represents one exchange:
    - User sends message
    - AI generates response
    - Metadata (emotion, risk) stored
    """
    
    # RISK LEVEL CHOICES
    RISK_LEVELS = [
        ('SAFE', 'Safe'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
        ('CRITICAL', 'Critical Risk'),
    ]
    
    # BLOCK 1: CORE FIELDS
    
    # Relationship to user
    user = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='chat_messages',
        help_text="User who sent this message"
    )
    
    # Message content
    message = models.TextField(
        help_text="User's message to the AI"
    )
    
    response = models.TextField(
        help_text="AI's response to the user"
    )
    
    # AI Metadata
    risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVELS,
        default='SAFE',
        help_text="Crisis detection result"
    )
    
    primary_emotion = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Detected emotion (from DistilRoBERTa)"
    )
    
    sentiment_score = models.FloatField(
        blank=True,
        null=True,
        help_text="Sentiment score from -1 (negative) to +1 (positive)"
    )
    
    emotion_confidence = models.FloatField(
        blank=True,
        null=True,
        help_text="Confidence in emotion detection (0-1)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When message was sent"
    )
    
    # BLOCK 2: MODEL METHODS
    
    class Meta:
        ordering = ['-created_at']  # Newest first by default
        
        # BLOCK 3: DATABASE INDEXES (for performance)
        indexes = [
            # Fast queries: "Get user's messages ordered by time"
            models.Index(fields=['user', '-created_at']),
            
            # Fast queries: "Find all crisis messages"
            models.Index(fields=['risk_level', '-created_at']),
            
            # Fast queries: "Get recent messages for user with risk level"
            models.Index(fields=['user', 'risk_level', '-created_at']),
        ]
        
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"
    
    def __str__(self):
        """String representation for admin panel"""
        return f"{self.user.email} - {self.created_at.strftime('%Y-%m-%d %H:%M')} - {self.risk_level}"
    
    def get_emotion_display(self):
        """Human-readable emotion summary"""
        if self.primary_emotion:
            confidence_pct = int(self.emotion_confidence * 100) if self.emotion_confidence else 0
            return f"{self.primary_emotion.title()} ({confidence_pct}%)"
        return "No emotion data"
    
    def is_crisis(self):
        """Check if this message was flagged as crisis"""
        return self.risk_level in ['HIGH', 'CRITICAL']
    
    @classmethod
    def get_user_history(cls, user, limit=10):
        """
        Get recent conversation history for user
        
        Args:
            user: Account object
            limit: Number of recent messages (default 10)
            
        Returns:
            QuerySet of ChatMessage objects (ordered chronologically)
        """
        return cls.objects.filter(
            user=user,
            risk_level='SAFE'  # Exclude crisis messages from context
        ).order_by('-created_at')[:limit][::-1]  # Reverse to chronological
    
    @classmethod
    def get_crisis_messages(cls, user):
        """Get all crisis messages for a user"""
        return cls.objects.filter(
            user=user,
            risk_level__in=['HIGH', 'CRITICAL']
        ).order_by('-created_at')
