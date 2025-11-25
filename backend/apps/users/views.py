from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

# Create your views here.
from apps.users.serializer import (
    AccountProfileSerializer, AccountRegisterSerializer,
    AccountLoginSerializer
)
from rest_framework import status
from rest_framework.response import Response
from apps.users.models import Account
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

@api_view(['GET'])
@permission_classes([AllowAny])
def get_users(request):
    users = Account.objects.all()
    serializer = AccountProfileSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = AccountRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        res = {
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        }
        return Response({
            'message': 'User registered successfully',
            'user': AccountProfileSerializer(user).data,
            "refresh": res['refresh'],
            "token": res['access']
        }, status=status.HTTP_201_CREATED)
    return Response({
        "message": "Registration failed.",
        'errors': serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    serializer = AccountLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(
        serializer.validated_data,
        status=status.HTTP_200_OK
    )

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh(request):
    serializer = TokenRefreshSerializer(data=request.data)

    try:
        serializer.is_valid(raise_exception=True)
    except TokenError as e:
        raise InvalidToken(e.args[0])
    
    return Response(serializer.validated_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    serializer = AccountProfileSerializer(user)

    # Return serialized profile
    return Response(serializer.data, status=status.HTTP_200_OK)
