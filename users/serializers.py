from rest_framework import serializers
from .models import CustomUser, Organisation
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import status

class UserSerializer(serializers.ModelSerializer):
	email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=CustomUser.objects.all())])
	password = serializers.CharField(write_only=True, required=True)
	phone = serializers.CharField(required=False, allow_blank=True)

	def validate(self, attrs):
		errors = {}

		if not attrs['firstName']:
			errors['firstName']= "First name is required."
		if not attrs['email']:
			errors['email']= "Email is required."
		if not attrs['password']:
			errors['password']= "Password is required."
		if not attrs['lastName']:
			errors['lastName'] = "Last name is required."

		if attrs.get('phone'):  
			if not attrs['phone'].isdigit():
				errors['phone'] = 'Phone number must be numeric.'
		
		if errors:
			raise serializers.ValidationError(errors, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
		return attrs
	
	def create(self, validated_data):
		user = CustomUser.objects.create_user(**validated_data)
		return user
	
	class Meta:
		model = CustomUser
		fields = ('email', 'password', 'firstName', 'lastName', 'phone', 'userId')
		read_only_fields = ['userId']



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
	def update_token_claims(self, token, user):
		token['email'] = user.email
		token['firstName'] = user.firstName
		token['lastName'] = user.lastName

		return token

class OrganisationSerializer(serializers.ModelSerializer):
	class Meta:
		model = Organisation
		fields = ('orgId', 'name', 'description')


class OrganisationCreateSerializer(serializers.ModelSerializer):
	class Meta:
		model = Organisation
		fields = ('orgId', 'name', 'description')
		read_only_fields = ['orgId']

	def validate(self, data):
		name = data['name']
		if Organisation.objects.filter(name=name).exists():
			raise serializers.ValidationError("An organisation with this name already exists.")
		return data
	

class OrganisationUserSerializer(serializers.Serializer):
	userId = serializers.CharField(required=True)

	def validate_userId(self, user_id):
		try:
			CustomUser.objects.get(userId=user_id)
		except CustomUser.DoesNotExist:
			raise serializers.ValidationError("User with the provided ID does not exsist")
		return user_id
	


