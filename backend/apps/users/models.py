from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class AccountManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be set")
        email = self.normalize_email(email)
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError("Please enter a valid email address.")
        
        first_name = extra_fields.get('first_name')
        last_name = extra_fields.get('last_name')

        if not first_name:
            raise ValueError("First name is required")
        
        if not last_name:
            raise ValueError("Last name is required")
        
        user = self.model(
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)
# Create your models here.
class Account(AbstractUser):
    # Remove username, use email instead
    username = None
    # Basic Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(
        unique=True,
        help_text='Required. Must be a valid email address.'
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text='Nigerian phone number format: +234XXXXXXXXXX'
    )

    # Demographics
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text='Used for age-appropriate interventions'
    )

    gender = models.CharField(
        max_length=20,
        choices=[
            ('Male', 'male'),
            ('Female', 'female'),
            ('Non-binary', 'non-binary'),
            ('Prefer not to say', 'prefer not to say'),
        ],
        blank=True,
        null=True
    )


    # Location
    state = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Nigerian state (e.g., Lagos, Abuja)'
    )
    city = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    has_previous_therapy = models.BooleanField(
        default=False, help_text='Has the user received therapy before?'
    )

    # Emergency Contact
    emergency_contact_name = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )
    emergency_contact_phone = models.CharField(
        max_length=15,
        null=True,
        blank=True
    )

    # Account setting
    is_verified = models.BooleanField(
        default=False,
        help_text='Email verification status'
    )
    is_superuser = models.BooleanField(
        default=False
    )    

    preferred_language = models.CharField(
        max_length=10,
        choices=[
            ('en', 'English'),
            ('yo', 'Yoruba'),
            ('ig', 'Igbo'),
            ('ha', 'Hausa'),
            ('pid', 'Pidgin'),
        ],
        default='en'
    )

    # Consent and Privacy
    consent_data_storage = models.BooleanField(
        default=False,
        help_text='User consents to data storage for service delivery'
    )
    consent_anonymized_research = models.BooleanField(
        default=False,
        help_text='User consents to anonymized data use for research'
    )

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(auto_now=True)
    
    # Override username requirement - we use email as username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = AccountManager()

    class Meta:
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at'])
        ]
    
    def __str__(self):
        return f"{self.email} - ({self.get_full_name})"
    
    @property
    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email
    
    @property
    def get_age(self):
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        age = today.year - self.date_of_birth.year
        if today.month < self.date_of_birth.month or \
        (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            age -= 1
        return age
    
    @property
    def is_minor(self):
        age = self.get_age()
        return age is not None and age < 18
