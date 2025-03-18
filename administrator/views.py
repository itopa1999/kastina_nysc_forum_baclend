from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.conf import settings
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.db.models import Q

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from administrator.permissions import IsCDSLeaderPermission
from administrator.swagger import TaggedAutoSchema
from .models import CDS_Group, User, UserVerification
from .serializers import CDS_GroupReadSerializer, CDS_GroupWriteSerializer, RegUserSerializer, ResendVerificationTokenSerializer, UserLoginSerializer, UserVerificationSerializer



# Create your views here.


class RegisterUser(generics.GenericAPIView):
    serializer_class = RegUserSerializer
    swagger_schema = TaggedAutoSchema
    def post(self, request, *args, **kwargs):
        serializer = RegUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            # Create user
            user = serializer.save(password=make_password(request.data['password']))
            verification = UserVerification(user=user)
            verification.generate_token()
            verification.save()
            
            user.is_active = False
            user.save()

            # Send the verification email with the token
            send_mail(
                "Your Verification Code",
                f"Your verification code is {verification.token}. It expires in 10 minutes.",
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

            return Response({"message": "Account created. A verification email has been sent.",
                             "email":user.email}, status=status.HTTP_201_CREATED)

        return Response({"error":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    
    


User = get_user_model()

class UserVerificationView(generics.GenericAPIView):
    serializer_class = UserVerificationSerializer
    swagger_schema = TaggedAutoSchema
    def post(self, request, *args, **kwargs):
        
        serializer = UserVerificationSerializer(data=request.data)

        if serializer.is_valid():
            token = serializer.validated_data['token']

            try:
                user_verification = UserVerification.objects.get(token=token)

                # Check if the token has expired
                if user_verification.is_token_expired():
                    return Response({'error': 'Token has expired'}, status=status.HTTP_400_BAD_REQUEST)

                # Check if the user has already been verified
                if user_verification.is_verified:
                    return Response({'error': 'User is already verified'}, status=status.HTTP_400_BAD_REQUEST)

                user = user_verification.user
                
                user.is_active = True
                user.save()

                user_verification.is_verified = True
                user_verification.save()
                
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                expiration_time = datetime.fromtimestamp(AccessToken(access_token)["exp"])
                profile_pic_url = request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None
                return Response(
                    {   "message":"your account has been verified",
                        "id": user.id,
                        "email": user.email,
                        "username":user.username,
                        "profile_pic":profile_pic_url,
                        "refresh": str(refresh),
                        "access": access_token,
                        "expiry": expiration_time,
                    },
                    status=status.HTTP_200_OK,
                )

            except UserVerification.DoesNotExist:
                return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"error":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    

class ResendVerificationTokenView(generics.GenericAPIView):
    serializer_class = ResendVerificationTokenSerializer
    swagger_schema = TaggedAutoSchema
    def post(self, request, *args, **kwargs):
        serializer = ResendVerificationTokenSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            if not email:
                return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Get the user by email
                user = User.objects.get(email=email)
                user_verification, created = UserVerification.objects.get_or_create(user=user)

                # If the user is already verified, inform the user
                if user.is_active:
                    return Response({"error": "User is already verified"}, status=status.HTTP_400_BAD_REQUEST)

                # If the token is expired or not verified, generate a new token
                if user_verification.is_token_expired() or user_verification.is_verified == False:
                    user_verification.generate_token()  # Regenerate token
                    user_verification.is_verified = False  # Reset verification status
                    user_verification.save()

                    # Send the token via email
                    send_mail(
                        'Your Verification Token',
                        f'Your verification token is {user_verification.token}, It expires in 10 minutes.',
                        settings.EMAIL_HOST_USER,
                        [user.email],
                        fail_silently=False,
                    )
                    
                    return Response({"message": "A new verification token has been sent to your email."}, status=status.HTTP_200_OK)
                
                return Response({"message": "Token is still valid. Please check your email for the verification."}, status=status.HTTP_400_BAD_REQUEST)
            
            except User.DoesNotExist:
                return Response({"error": "User with this email does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    
    

class LoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    swagger_schema = TaggedAutoSchema
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get("username")
        password = serializer.validated_data.get("password")
         
        try:
            user = User.objects.get(Q(email=username) | Q(username=username))
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({"error": "Account is inactive"}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        expiration_time = datetime.fromtimestamp(AccessToken(access_token)["exp"])
        profile_pic_url = request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None
        return Response(
            {
                "id": user.id,
                "username":user.username,
                "email": user.email,
                "profile_pic": profile_pic_url, 
                "refresh": str(refresh),
                "access": access_token,
                "expiry": expiration_time,
            },
            status=status.HTTP_200_OK,
        )
            




class CDS_GroupListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = CDS_Group.objects.all()
    serializer_class = CDS_GroupWriteSerializer

    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser and not request.user.is_cds_leader:
            return Response({"error":"Your account doesn't have enough. Please contact support."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"detail": "CDS group created successfully"}, status=status.HTTP_201_CREATED)
    
    
class CDS_GroupUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsCDSLeaderPermission]
    serializer_class = CDS_GroupWriteSerializer
    queryset = CDS_Group.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "id"
    
    
    
class CDS_GroupDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CDS_GroupReadSerializer
    queryset = CDS_Group.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "id"