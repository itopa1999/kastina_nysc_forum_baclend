from rest_framework import serializers
from rest_framework.exceptions import ParseError

from administrator.models import CDS_Group, User

class RegUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'username', 'state_code', 'password']
        
    def validate_password(self, value):
        if len(value) < 8:
            raise ParseError("Password must be at least 8 characters long.")
        return value


class UserVerificationSerializer(serializers.Serializer):
    token = serializers.IntegerField(required = True)
    
        
class ResendVerificationTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    
class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    
    def validate_password(self, value):
        if len(value) < 8:
            raise ParseError("Password must be at least 8 characters long.")
        return value
    
    
  
class CDS_GroupWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CDS_Group
        fields = ["id",'name', 'description']
        
        
    def create(self, validated_data):
        cds_group = CDS_Group.objects.create(**validated_data)

        return cds_group
        
        
    def update(self, instance: CDS_Group, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance




class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','email', 'username', 'first_name', 'last_name', 'state_code']
        

class CDS_GroupReadSerializer(serializers.ModelSerializer):
    users = UserReadSerializer(many=True, read_only=True)
    class Meta:
        model = CDS_Group
        fields = ["id",'name', 'description','users']