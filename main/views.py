from dj_rest_auth.registration.views import RegisterView as DefaultRegisterView
from dj_rest_auth.registration.views import VerifyEmailView
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.decorators import action
from rest_framework.response import Response
from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404, redirect
from django.core.mail import EmailMessage
from rest_framework import viewsets, generics, status
from .permissions import *
from .serializers import *
from django.http import Http404
from django.urls import reverse
from django.apps import apps
from .models import *


class UsersUselessView(APIView):
    def get(self, request):
        users = User.objects.all()
        data = {"count": users.count(), "usernames": [user.username for user in users],
                "emails": [user.email for user in users]}
        return Response(data)


class RegisterView(DefaultRegisterView):
    serializer_class = CustomRegisterSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        email = request.data.get('email', '')
        username = request.data.get('username', '')
        if email:
            try:
                email_confirmation = EmailConfirmationHMAC(
                    EmailConfirmation.create(EmailConfirmation, email, created_by=username))
                confirm_url = request.build_absolute_uri(
                    reverse('account_confirm_email', args=[email_confirmation.key]))
                EmailMessage('sociosphere.uz',
                             f"Hello from sociosphere.uz!\n\nYou're receiving this email because user {username} has given yours email address to register an account on sociosphere.uz.\n\nTo confirm this is correct, go to {confirm_url}",
                             'sociosphere@gmail.com', [email]).send()
                return Response({"Email": False}, status=500)
            except:
                return Response({"Email": True}, status=200)
        return response


class ConfirmEmailView(VerifyEmailView):
    def get(self, *args, **kwargs):
        self.kwargs['key'] = self.kwargs['key']
        confirmation = self.get_object()
        confirmation.confirm(self.request)
        return redirect('http://127.0.0.1:3000/users/')

    def get_object(self, queryset=None):
        key = self.kwargs['key']
        email_confirmation = EmailConfirmationHMAC.from_key(key)
        if not email_confirmation:
            email_confirmation = EmailConfirmation.objects.confirm_email(key)
        if not email_confirmation:
            raise NotFound('No confirmation matching the key was found')
        return email_confirmation


class UserViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all().order_by('-user__date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsOwnerOrReadOnlyForUsers, ]

    def create(self, request, *args, **kwargs):
        return Response({"message": "Go to 'http://127.0.0.1:3000/register/' for authentication"},
                        status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['get', 'post'])
    def subscribe(self, request, pk=None):
        userprofile = self.get_object()
        if request.method == 'GET':
            count = userprofile.subscribers.count()
            return Response({'subscribers_count': count})
        elif request.method == 'POST':
            subscriber = UserProfile.objects.get(user=request.user)
            if subscriber == userprofile:
                return Response({"message": "Ты не можешь подписаться на себя."})
            if subscriber.subscribe(userprofile):
                return Response({"message": f"Ты подписался на {userprofile.user.username}"})
            return Response({"message": f"Ты уже подписался на {userprofile.user.username}"})

    @action(detail=True, methods=['get', 'post'])
    def unsubscribe(self, request, pk=None):
        userprofile = self.get_object()
        if request.method == 'GET':
            count = userprofile.subscribers.count()
            return Response({'subscribers_count': count})
        elif request.method == 'POST':
            subscriber = UserProfile.objects.get(user=request.user)
            if subscriber == userprofile:
                return Response({"message": "Ты не можешь отписаться от себя."})
            if subscriber.unsubscribe(userprofile):
                return Response({"message": f"Ты отписался от {userprofile.user.username}"})
            return Response({"message": f"Ты не подписан на {userprofile.user.username}"})


class LikeViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, ]
    queryset = Like.objects.all()
    serializer_class = LikeSerializer


class CommentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrReadOnly, ]
    serializer_class = CommentSerializer

    def get_queryset(self):
        model_type = self.kwargs['model_type'].capitalize()
        model = apps.get_model('main', model_type)
        model_instance = get_object_or_404(model, pk=self.kwargs['model_pk'])
        if model_type == 'Stories':
            return Comment.objects.filter(story=model_instance).order_by('-create_time')
        else:
            return Comment.objects.filter(post=model_instance).order_by('-create_time')

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            model_type = self.kwargs['model_type'].capitalize()
            model = apps.get_model('main', model_type)
            model_instance = get_object_or_404(model, pk=self.kwargs['model_pk'])
            if model_type == 'Stories':
                serializer.save(owner=self.request.user.userprofile, story=model_instance)
            else:
                serializer.save(owner=self.request.user.userprofile, post=model_instance)
        else:
            raise PermissionDenied("Ты должен быть авторизован, чтобы оставить комментарий.")

    @action(detail=True, methods=['get', 'post'])
    def like(self, request, model_type=None, model_pk=None, pk=None, lang=None):
        comment = self.get_object()
        content_type = ContentType.objects.get_for_model(comment)
        user_profile = UserProfile.objects.get(user=request.user)
        if request.method == 'POST':
            like, created = Like.objects.get_or_create(owner=user_profile, content_type=content_type,
                                                       object_id=comment.id)
            if created:
                return Response({'status': 'Comment liked.'})
            else:
                return Response({'status': 'You already liked this comment.'})
        elif request.method == 'GET':
            likes_count = Like.objects.filter(content_type=content_type, object_id=comment.id).count()
            return Response({'likes_count': likes_count})

    @action(detail=True, methods=['get', 'post'])
    def unlike(self, request, model_type=None, model_pk=None, pk=None, lang=None):
        comment = self.get_object()
        content_type = ContentType.objects.get_for_model(comment)
        user_profile = UserProfile.objects.get(user=request.user)
        like = Like.objects.filter(owner=user_profile, content_type=content_type, object_id=comment.id)
        if request.method == 'POST':
            if like.exists():
                like.delete()
                return Response({'status': 'Comment unliked.'})
            else:
                return Response({'status': 'You have not liked this comment yet.'})
        elif request.method == 'GET':
            likes_count = Like.objects.filter(content_type=content_type, object_id=comment.id).count()
            return Response({'likes_count': likes_count})


class NewsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly, ]
    serializer_class = NewsSerializer

    def get_queryset(self):
        lang = self.kwargs.get('lang')
        return News.objects.filter(**{f'title_{lang}__isnull': False, f'body_{lang}__isnull': False}).order_by(
            '-create_time')

    def perform_create(self, serializer):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            serializer.save()
        else:
            raise PermissionDenied("Ты должен быть авторизован как админ, чтобы создать новость.")

    @action(detail=True, methods=['get', 'post'])
    def like(self, request, pk=None, lang=None):
        news = self.get_object()
        content_type = ContentType.objects.get_for_model(news)
        user_profile = UserProfile.objects.get(user=request.user)
        if request.method == 'POST':
            like, created = Like.objects.get_or_create(owner=user_profile, content_type=content_type, object_id=news.id)
            if created:
                return Response({'status': 'News liked.'})
            else:
                return Response({'status': 'You already liked this news.'})
        elif request.method == 'GET':
            likes_count = Like.objects.filter(content_type=content_type, object_id=news.id).count()
            return Response({'likes_count': likes_count})

    @action(detail=True, methods=['get', 'post'])
    def unlike(self, request, pk=None, lang=None):
        news = self.get_object()
        content_type = ContentType.objects.get_for_model(news)
        user_profile = UserProfile.objects.get(user=request.user)
        like = Like.objects.filter(owner=user_profile, content_type=content_type, object_id=news.id)
        if request.method == 'POST':
            if like.exists():
                like.delete()
                return Response({'status': 'News unliked.'})
            else:
                return Response({'status': 'You have not liked this news yet.'})
        elif request.method == 'GET':
            likes_count = Like.objects.filter(content_type=content_type, object_id=news.id).count()
            return Response({'likes_count': likes_count})


class PostsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrReadOnly, ]
    serializer_class = PostsSerializer

    def get_queryset(self):
        lang = self.kwargs.get('lang')
        return Posts.objects.filter(**{f'title_{lang}__isnull': False, f'body_{lang}__isnull': False}).order_by(
            '-create_time')

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(owner=self.request.user.userprofile)
        else:
            raise PermissionDenied("Ты должен быть авторизован, чтобы создать пост.")

    @action(detail=True, methods=['get', 'post'])
    def like(self, request, pk=None, lang=None):
        post = self.get_object()
        content_type = ContentType.objects.get_for_model(post)
        user_profile = UserProfile.objects.get(user=request.user)
        if request.method == 'POST':
            like, created = Like.objects.get_or_create(owner=user_profile, content_type=content_type, object_id=post.id)
            if created:
                return Response({'status': 'Post liked.'})
            else:
                return Response({'status': 'You already liked this post.'})
        elif request.method == 'GET':
            likes_count = Like.objects.filter(content_type=content_type, object_id=post.id).count()
            return Response({'likes_count': likes_count})

    @action(detail=True, methods=['get', 'post'])
    def unlike(self, request, pk=None, lang=None):
        post = self.get_object()
        content_type = ContentType.objects.get_for_model(post)
        user_profile = UserProfile.objects.get(user=request.user)
        like = Like.objects.filter(owner=user_profile, content_type=content_type, object_id=post.id)
        if request.method == 'POST':
            if like.exists():
                like.delete()
                return Response({'status': 'Post unliked.'})
            else:
                return Response({'status': 'You have not liked this post yet.'})
        elif request.method == 'GET':
            likes_count = Like.objects.filter(content_type=content_type, object_id=post.id).count()
            return Response({'likes_count': likes_count})


class StoriesViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrReadOnly, ]
    serializer_class = StoriesSerializer

    def get_queryset(self):
        lang = self.kwargs.get('lang')
        return Stories.objects.filter(**{f'title_{lang}__isnull': False}).order_by('-create_time')

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(owner=self.request.user.userprofile)
        else:
            raise PermissionDenied("Ты должен быть авторизован, чтобы создать историю.")

    @action(detail=True, methods=['get', 'post'])
    def like(self, request, pk=None, lang=None):
        story = self.get_object()
        content_type = ContentType.objects.get_for_model(story)
        user_profile = UserProfile.objects.get(user=request.user)
        if request.method == 'POST':
            like, created = Like.objects.get_or_create(owner=user_profile, content_type=content_type,
                                                       object_id=story.id)
            if created:
                return Response({'status': 'Story liked.'})
            else:
                return Response({'status': 'You already liked this story.'})
        elif request.method == 'GET':
            likes_count = Like.objects.filter(content_type=content_type, object_id=story.id).count()
            return Response({'likes_count': likes_count})

    @action(detail=True, methods=['get', 'post'])
    def unlike(self, request, pk=None, lang=None):
        story = self.get_object()
        content_type = ContentType.objects.get_for_model(story)
        user_profile = UserProfile.objects.get(user=request.user)
        like = Like.objects.filter(owner=user_profile, content_type=content_type, object_id=story.id)
        if request.method == 'POST':
            if like.exists():
                like.delete()
                return Response({'status': 'Story unliked.'})
            else:
                return Response({'status': 'You have not liked this story yet.'})
        elif request.method == 'GET':
            likes_count = Like.objects.filter(content_type=content_type, object_id=story.id).count()
            return Response({'likes_count': likes_count})
