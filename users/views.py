from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .serializers import UserSerializer, OrganisationSerializer, OrganisationCreateSerializer, OrganisationUserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model, authenticate, login
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from .models import CustomUser, Organisation
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound



User = get_user_model()


class RegisterView(APIView):
	permission_classes = [AllowAny]
	serializer_class = UserSerializer

	def post(self, request):
		serializer = self.serializer_class(data=request.data)
		
		if serializer.is_valid():
			if (User.objects.filter(email=serializer.validated_data['email']).exists()):
				return Response({"status": "Bad request",
					"message": "Registration unsuccessful. Email already exists"},
					status=status.HTTP_422_UNPROCESSABLE_ENTITY)
		
			user = serializer.save()
			refresh = RefreshToken.for_user(user)
			data = {
				"status": "success",
				"message": "Registration Successful",
				"data" : {
					"accessToken": str(refresh.access_token),
					"user": UserSerializer(user).data
				}
			}
			return Response(data, status=status.HTTP_201_CREATED)
		else:
			errors = serializer.errors
			return Response(errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
	

class LoginView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		email = request.data.get('email')
		password = request.data.get('password')

		user = authenticate(request, username=email, password=password)
		if user:
			refresh = RefreshToken.for_user(user)
			login(request, user)

			data = {
				"status": "success",
				"message": "Login successful",
				"data" : {
					"accessToken": str(refresh.access_token),
					"user" : UserSerializer(user).data
				}
			}
			return Response(data, status=status.HTTP_200_OK)
		else:
			data = {
				"status" : "Bad request",
				"message": "Authentication failed",
				"statusCode": 401
			}
			return Response(data, status=status.HTTP_401_UNAUTHORIZED)

class OrganisationView(APIView):
	permission_classes = [IsAuthenticated]
	authentication_classes = [JWTAuthentication]

	
	def get(self, request):
		user = request.user
		organisations = Organisation.objects.filter((Q(owner=user)) | Q(users__in=[user]))
		serializer = OrganisationSerializer(organisations, many=True)
		data = {
			"status": "success",
			"message": "User's organisations retrieved successfully",
			"data": {
				"organisations": serializer.data
			}
		}
		return Response(data, status=status.HTTP_200_OK)
	
	
	def post(self, request):
		serializer = OrganisationCreateSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save(owner=request.user)
			data = {
				"status": "success",
				"message": "Organisation created successfully",
				"data": serializer.data
			}
			return Response(data, status=status.HTTP_201_CREATED)

		else:
			data ={
				"status": "Bad Request",
				"message": "Client error",
				"statusCode": 400
			}
			return Response(data, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
	permission_classes = [IsAuthenticated]
	authentication_classes = [JWTAuthentication]

	def get(self, request, user_id):
		try:
			user = CustomUser.objects.get(userId=user_id)
		except CustomUser.DoesNotExist:
			return Response({
				"status":"error",
				"message": "User not found"
				}, status=status.HTTP_401_UNAUTHORIZED)
		
		if user != request.user:
			return Response({
				"status": "error",
				"message": "Unauthorized to access this record"
				}, status=status.HTTP_401_UNAUTHORIZED)

		serializer = UserSerializer(user)
		data = {
			"status": "success",
			"message": "User details retrieved successfully",
			"data": serializer.data,
		}
		return Response(data, status=status.HTTP_200_OK)
	
class OrganisationUserView(APIView):
	permission_classes = [IsAuthenticated]
	authentication_classes = [JWTAuthentication]

	def post(self, request, org_id):
		try:
			organisation = Organisation.objects.get(orgId=org_id)
		except Organisation.DoesNotExist:
			raise NotFound("Organisation not found")
		

		user_data = request.data

		serializer = OrganisationUserSerializer(data=user_data)

		if serializer.is_valid():
			user_id = serializer.validated_data['userId']

			try:
				user = CustomUser.objects.get(userId=user_id)
			except CustomUser.DoesNotExist:
				return Response(
					{"status": "error", "message":"User with the provided ID not found"},
					status=status.HTTP_404_NOT_FOUND,
				)
			
			if user in organisation.users.all():
				return Response(
					{
						"status": "error",
						"message": "User is already a member of this organisation"
					}, status=status.HTTP_400_BAD_REQUEST
				)
			
			organisation.users.add(user)
			organisation.save()

			data = {
				"status": "success",
				"message": "User added to organisation sucessfully"
			}
			return Response(data, status=status.HTTP_200_OK)
		else:
			return Response(
				{
					"status": "error",
					"message": "Invalid user data",
					"errors": serializer.errors
				}, status=status.HTTP_400_BAD_REQUEST
			)

class OrganisationDetailView(APIView):
	permission_classes = [IsAuthenticated]
	authentication_classes = [JWTAuthentication]

	def get(self, request, org_id):
		user = request.user
		try:
			organisation = Organisation.objects.get(orgId=org_id)
		except Organisation.DoesNotExist:
			return Response({"status": "error", "message":"Organisation not found"}, status=status.HTTP_401_UNAUTHORIZED)
		
		if (user not in organisation.users.all()):
			return Response({"status": "error", "message": "You do not have permission to access this organisation"}, status=status.HTTP_403_FORBIDDEN)
		else:
			serializer = OrganisationSerializer(organisation)
			data = {
				"status": "success",
				"message": "Organisation details retrieved successfully",
				"data": serializer.data
			}
			return Response(data, status=status.HTTP_200_OK)



