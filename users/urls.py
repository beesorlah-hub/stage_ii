from django.urls import path
from .views import RegisterView, LoginView, UserDetailView, OrganisationView, OrganisationDetailView, OrganisationUserView
from rest_framework_simplejwt.views import (
	TokenObtainPairView,
	TokenRefreshView
)

urlpatterns = [
	path('auth/register', RegisterView.as_view(), name='register'),
	path('auth/login', LoginView.as_view(), name='login'),
	path('api/users/<str:user_id>', UserDetailView.as_view(), name='user_details'),
	path('api/organisations', OrganisationView.as_view(), name='organisation'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
	path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
	path('api/organisations/<str:org_id>', OrganisationDetailView.as_view(), name='organisation-detail'),
	path('api/organisations/<str:org_id>/users', OrganisationUserView.as_view(), name='organisation-users'),
]