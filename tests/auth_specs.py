

# Create your tests here.
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from users.models import Organisation
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import Organisation
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings
from datetime import timedelta
# import pdb


CustomerUser = get_user_model()

class TokenTestCase(TestCase):

	def setUp(self):
		self.user = CustomerUser.objects.create_user(
			email = 'beebee@example.com',
			password = 'mypassword',
			firstName = 'Bee',
			phone = '098123456',
			lastName = 'Limah'
		)

	def test_token_generation(self):
		refresh = RefreshToken.for_user(self.user)

		self.assertIsNotNone(refresh)
		self.assertIsNotNone(refresh.access_token)

	def test_token_expiration(self):
		refresh = RefreshToken.for_user(self.user)
		access_token = refresh.access_token

		expected_expiry = (access_token.current_time + api_settings.ACCESS_TOKEN_LIFETIME).timestamp()

		actual_expiry = access_token.payload['exp']

		delta = timedelta(seconds=5).total_seconds()

		self.assertAlmostEqual(expected_expiry, actual_expiry, delta=delta)

	def test_user_details_in_token(self):
		refresh = RefreshToken.for_user(self.user)
		access_token = refresh.access_token

		

		self.assertEqual(access_token.payload['user_id'], str(self.user.userId))

class RegisterTests(APITestCase):
	def setUp(self):
		self.register_url = reverse('register')

	def test_register_user_successfully_with_default_organisation(self):
		data = {
			"email": "john.doe@example.com",
			"password": "password123",
			"firstName": "John",
			"lastName": "Doe",
			"phone": "1234567890"
		}

		response = self.client.post(self.register_url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data['status'], 'success')
		self.assertIn('accessToken', response.data['data'])

		user = CustomerUser.objects.get(email="john.doe@example.com")
		self.assertIsNotNone(user)
		org = Organisation.objects.get(owner=user)
		self.assertEqual(org.name, "John's Organisation")


	def test_login_user_successfully(self):

		user_data = {
			"email": "jane.doe@example.com",
			"password": "password123",
			"firstName": "Jane",
			"lastName": "Doe",
			"phone": "1234567890"
		}
		self.client.post(self.register_url, user_data, format='json')

		login_data = {
			"email": "jane.doe@example.com",
			"password": "password123"
		}
		response = self.client.post(reverse('token_obtain_pair'), login_data, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('access', response.data)

	def test_fail_if_required_fields_are_missing(self):
		data = {
			"email": "missing.fields@example.com",
			"password": "password123",
			"lastName": "LastName"
		}

		response = self.client.post(self.register_url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
		self.assertIn('firstName', response.data)

		data = {
			"email": "missing.fields@example.com",
			"password": "password123",
			"firstName": "FirstName"
		}

		response = self.client.post(self.register_url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
		self.assertIn('lastName', response.data)

		data = {
			"email": "missing.fields@example.com",
			"firstName": "FirstName",
			"lastName": "LastName"
		}

		response = self.client.post(self.register_url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
		self.assertIn('password', response.data)

		data = {
			"firstName": "FirstName",
			"lastName": "LastName",
			"password": "Pasword123"
		}

		response = self.client.post(self.register_url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
		self.assertIn('email', response.data)


	def test_fail_if_duplicate_email_or_userid(self):
		data1 = {
			"email": "duplicate@example.com",
			"password": "password123",
			"firstName": "First",
			"lastName": "User",
			"phone": "1234567890"
		}

		data2 = {
			"email": "duplicate@example.com",
			"password": "password123",
			"firstName": "Second",
			"lastName": "User",
			"phone": "1234567890"
		}

		self.client.post(self.register_url, data1, format='json')
		response = self.client.post(self.register_url, data2, format='json')
		self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

		self.assertIn('email', response.data)

class OrganisationAccessTestCase(TestCase):

	def setUp(self):
		self.user1 = CustomerUser.objects.create_user(
			email='beebee@example.com',
			password='mypassword',
			firstName='Bee',
			lastName='Limah',
			phone='098123456'
		)
		self.user2 = CustomerUser.objects.create_user(
			email='user2@example.com',
			password='mypassword',
			firstName='Bee',
			lastName='Limah',
			phone='08182828382'
		)

		self.org1 = Organisation.objects.create(
			name="Org One",
			description="First Organisation",
			owner=self.user1
		)
		self.org1.users.add(self.user1)

		self.org2 = Organisation.objects.create(
			name="Org Two",
			description="Second Organisation",
			owner=self.user2
		)
		self.org2.users.add(self.user2)

		self.client = APIClient()

	def test_user1_cannot_access_org2(self):

		self.client.force_authenticate(user=self.user1)

		url = reverse('organisation-detail', args=[self.org2.orgId])
		response = self.client.get(url)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_user2_cannot_access_org1(self):
		self.client.force_authenticate(user=self.user2)

		url = reverse('organisation-detail', args=[self.org1.orgId])
		response = self.client.get(url)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)		