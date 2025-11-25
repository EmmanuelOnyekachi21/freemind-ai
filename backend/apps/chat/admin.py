from django.contrib import admin


# Register your models here.
from apps.chat.models import ChatMessage
from django.utils.html import format_html


@admin.register(ChatMessage)
class ChatAdmin(admin.ModelAdmin):
    list_display = [
         'id',
        'user_email',
        'short_message',
        'risk_level_badge',
        'primary_emotion',
        'sentiment_score',
        'created_at',
    ]

    # Make these methods allow HTML for coloring badges
    list_display_links = ('id', 'short_message')

    # Filters in the right sidebar
    list_filter = (
        'risk_level',
        'primary_emotion',
        'created_at',
    )

    # Search bar configuration
    search_fields = (
        'user__email',
        'message',
        'response',
    )

    # Order by newest first (same as model Meta)
    ordering = ('-created_at',)

    # Read-only fields in detail view
    readonly_fields = (
        'created_at',
    )

    # Performance: avoid N+1 queries by joining user table
    list_select_related = ('user',)

    # Reduce noise in admin logs
    save_on_top = True

    # ------ CUSTOM DISPLAY METHODS ------ #

    def user_email(self, obj):
        """Show email instead of Account object."""
        return obj.user.email
    user_email.short_description = "User Email"

    def short_message(self, obj):
        """Short preview of user message."""
        return (obj.message[:50] + "...") if len(obj.message) > 50 else obj.message
    short_message.short_description = "Message"

    def risk_level_badge(self, obj):
        """Color-coded risk level badge for clarity."""
        color_map = {
            'SAFE': 'green',
            'MEDIUM': 'orange',
            'HIGH': 'red',
            'CRITICAL': 'darkred',
        }
        color = color_map.get(obj.risk_level, 'gray')

        return format_html(
            '<span style="padding:4px 8px; border-radius:4px; '
            'color:white; background-color:{}; font-weight:600;">{}</span>',
            color,
            obj.risk_level
        )
    risk_level_badge.short_description = "Risk Level"
    risk_level_badge.allow_tags = True
