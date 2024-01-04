from rest_framework.routers import DefaultRouter
from dj_rest_auth.views import *
from django.urls import path, include
from .views import *

router = DefaultRouter()
router.register('likes', LikeViewSet, basename='likes')
router.register('news', NewsViewSet, basename='news')
router.register('posts', PostsViewSet, basename='posts')
router.register('stories', StoriesViewSet, basename='stories')
router.register(r'(?P<model_type>stories|posts)/(?P<model_pk>\d+)/comments', CommentViewSet,
                basename='comments')
router_for_users = DefaultRouter()
router_for_users.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router_for_users.urls)),
    path('users/useless/', UsersUselessView.as_view(), name='users_useless'),
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password/reset/confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('register/', RegisterView.as_view(), name='account_signup'),
    path('register/account-confirm-email/<str:key>/', ConfirmEmailView.as_view(), name='account_confirm_email'),
    path('login/', LoginView.as_view(), name='account_login'),
    path('logout/', LogoutView.as_view(), name='account_logout'),
    path('<str:lang>/', include(router.urls)),
]
