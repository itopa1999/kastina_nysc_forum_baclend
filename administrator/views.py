from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.conf import settings
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.db.models import Q
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from administrator.permissions import IsCDSLeaderPermission
from administrator.swagger import TaggedAutoSchema
from .models import CDS_Group, User, UserVerification
from .serializers import CDS_GroupReadSerializer, CDS_GroupWriteSerializer, ChangePasswordSerializer, ForgetPasswordSerializer, ForgetPasswordVerificationTokenSerializer, RegUserSerializer, ResendVerificationTokenSerializer, UserLoginSerializer, UserVerificationSerializer



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
            
            token = verification.token
            uidb64 = urlsafe_base64_encode(force_bytes(user.id))
            verification_link = request.build_absolute_uri(
                reverse('verify-email', kwargs={'uidb64': uidb64, 'token': token})
            )

            # Send the verification email with the token
            send_mail(
                "Your Verification Code",
                f"Use this code: {verification.token} (expires in 10 minutes)\n"
                f"Or click the link to verify your email: {verification_link} ",
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

            return Response({"message": "Account created. A verification email has been sent.",
                             "email":user.email}, status=status.HTTP_201_CREATED)

        return Response({"error":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    


User = get_user_model()


class VerifyEmailView(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = get_object_or_404(User, id=uid)
            verification = get_object_or_404(UserVerification, user=user, token=token)
            
            if verification.is_token_expired():
                    return Response({'error': 'Link has expired'}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the user has already been verified
            if verification.is_verified:
                return Response({'error': 'Link is already verified'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Activate user
            user.is_active = True
            user.save()

            verification.is_verified = True
            verification.save()

            return Response({"message": "Your email has been verified successfully! please go back to login"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Invalid or expired link."}, status=status.HTTP_400_BAD_REQUEST)
        
        

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
                    
                    token = user_verification.token
                    uidb64 = urlsafe_base64_encode(force_bytes(user.id))
                    verification_link = request.build_absolute_uri(
                        reverse('verify-email', kwargs={'uidb64': uidb64, 'token': token})
                    )

                    # Send the token via email
                    send_mail(
                        "Your Verification Code",
                        f"Use this code: {user_verification.token} (expires in 10 minutes)\n"
                        f"Or click the link to verify your email: {verification_link} ",
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
            


class ForgetPasswordView(generics.GenericAPIView):
    serializer_class = ForgetPasswordSerializer
    swagger_schema = TaggedAutoSchema
    def post(self, request, *args, **kwargs):
        serializer = ForgetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            if not email:
                return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(email=email)
                user_verification, created = UserVerification.objects.get_or_create(user=user)

                # If the token is expired or not verified, generate a new token
                if user_verification.is_token_expired() or user_verification.is_verified == False:
                    user_verification.generate_token()
                    user_verification.is_verified = False 
                    user_verification.save()

                    # Send the token via email
                    send_mail(
                        'Your Verification Token',
                        f'Your verification token is {user_verification.token}, It expires in 10 minutes.',
                        settings.EMAIL_HOST_USER,
                        [user.email],
                        fail_silently=False,
                    )
                    
                    return Response({"message": "A verification token has been sent to your email."}, status=status.HTTP_200_OK)
                
                return Response({"message": "Token is still valid. Please check your email for the verification."}, status=status.HTTP_400_BAD_REQUEST)
            
            except User.DoesNotExist:
                return Response({"error": "User with this email does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    


class ForgetPasswordVerificationView(generics.GenericAPIView):
    serializer_class = ForgetPasswordVerificationTokenSerializer
    swagger_schema = TaggedAutoSchema
    def post(self, request, *args, **kwargs):
        
        serializer = ForgetPasswordVerificationTokenSerializer(data=request.data)

        if serializer.is_valid():
            token = serializer.validated_data['token']
            password = serializer.validated_data['password']
            
            if token == 6:
                return Response({'error': 'Token must be 6 numbers'}, status=status.HTTP_400_BAD_REQUEST)    

            try:
                user_verification = UserVerification.objects.get(token=token)

                # Check if the token has expired
                if user_verification.is_token_expired():
                    return Response({'error': 'Token has expired'}, status=status.HTTP_400_BAD_REQUEST)

                # Check if the user has already been verified
                if user_verification.is_verified:
                    return Response({'error': 'Token has been already verified'}, status=status.HTTP_400_BAD_REQUEST)

                user = user_verification.user
                user.password = make_password(password)
                user.save()
            
                user_verification.is_verified = True
                user_verification.save()
                
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                expiration_time = datetime.fromtimestamp(AccessToken(access_token)["exp"])
                profile_pic_url = request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None
                return Response(
                    {   "message":"Password has been changed successfully",
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



class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    swagger_schema = TaggedAutoSchema
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            password = serializer.validated_data['password']
            password1 = serializer.validated_data['password1']
            password2 = serializer.validated_data['password2']
            
            if len(password) < 8 or len(password1) < 8 or len(password2) < 8:
                return Response({'error': 'Password must be at least 8 characters long.'}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure new password matches confirmation
            if password1 != password2:
                return Response({'error': 'New password and confirm password do not match.'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = request.user
            if not user.check_password(password):
                return Response({"error": "Old Password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

            user.password = make_password(password1)
            user.save()
                
            
            return Response({'message': 'Password Changed'}, status=status.HTTP_200_OK)
    
        return Response({"error":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


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