from rest_framework import serializers
from apps.users.models import Account
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from django.contrib.auth.models import update_last_login

class AccountProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    full_name = serializers.ReadOnlyField(source='get_full_name')
    age = serializers.ReadOnlyField(source='get_age')
    class Meta:
        model = Account
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'phone_number',
            'date_of_birth',
            'age',
            'gender',
            'state',
            'city',
            'has_previous_therapy',
            'preferred_language',
            'is_verified',
            'created_at',
            'last_active',
        ]

class AccountRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(
        write_only=True,
        min_length=8,
        required=True,
        label='Confirm Password'
    )

    class Meta:
        model = Account
        fields = [
            'email',
            'password',
            'password2',
            'first_name',
            'last_name',
            'phone_number',
            'date_of_birth',
            'gender',
            'state',
            'city',
            'preferred_language',
            'consent_data_storage',
        ]
    
    def validate(self, data):
        """Validate that passwords match"""
        if data['password'] != data['password2']:
            raise serializers.ValidationError({
                'passwords': 'Passwords fields don\'t match'
            })
        return data
    
    def validate_phone_number(self, value):
        if value and not value.startswith('+234'):
            raise serializers.ValidationError(
                "Phone number must be in format: +234XXXXXXXXXX"
            )
        return value
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = Account.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number'),
            date_of_birth=validated_data.get('date_of_birth'),
            gender=validated_data.get('gender'),
            state=validated_data.get('state'),
            city=validated_data.get('city'),
            consent_data_storage=validated_data.get('consent_data_storage', False),
        )
        return user


class AccountLoginSerializer(TokenObtainPairSerializer):
    username_field = 'email'
    def validate(self, attrs):
        data = super().validate(attrs)

        data['user'] = AccountProfileSerializer(self.user).data
        data['refresh'] = str(data['refresh'])
        data['access'] = str(data['access'])

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)
        
        return data
