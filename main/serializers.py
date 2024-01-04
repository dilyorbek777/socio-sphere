from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import get_user_model
from moviepy.editor import VideoFileClip
from rest_framework import serializers
from .models import *
from PIL import Image


class CustomRegisterSerializer(RegisterSerializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    def get_cleaned_data(self):
        super().get_cleaned_data()
        return {'first_name': self.validated_data.get('first_name', ''),
                'last_name': self.validated_data.get('last_name', ''),
                'username': self.validated_data.get('username', ''), 'email': self.validated_data.get('email', ''),
                'password1': self.validated_data.get('password1', ''),
                'password2': self.validated_data.get('password2', '')}

    def validate_email(self, email):
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Этот адрес электронной почты уже используется.")
        return email

    def custom_signup(self, request, user):
        user.first_name = self.validated_data.get('first_name', '')
        user.last_name = self.validated_data.get('last_name', '')
        user.save(update_fields=['first_name', 'last_name'])


class UserNestedSerializer(serializers.ModelSerializer):
    date_joined = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'is_active', 'date_joined']

    def get_date_joined(self, obj):
        return obj.date_joined.strftime("%d-%m-%Y %H:%M:%S")


class OwnerSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer()

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'avatar', 'banner']


class LikeSerializer(serializers.ModelSerializer):
    create_time = serializers.SerializerMethodField()
    owner = OwnerSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'create_time', 'owner', 'object_id', 'content_type']

    def get_create_time(self, obj):
        return obj.create_time.strftime("%d-%m-%Y %H:%M:%S")


class UsersLikeSerializer(LikeSerializer):
    content_object_type = serializers.SerializerMethodField()
    content_object = serializers.SerializerMethodField()

    class Meta:
        model = Like
        fields = ['id', 'create_time', 'owner', 'object_id', 'content_type', 'content_object', 'content_object_type']

    def get_content_object_type(self, obj):
        return str(obj.content_object.__class__.__name__)

    def get_content_object(self, obj):
        if isinstance(obj.content_object, Posts):
            return SimplePostsSerializer(obj.content_object).data
        if isinstance(obj.content_object, News):
            return SimpleNewsSerializer(obj.content_object).data
        if isinstance(obj.content_object, Stories):
            return SimpleStoriesSerializer(obj.content_object).data
        if isinstance(obj.content_object, Comment):
            return SimpleCommentSerializer(obj.content_object).data


class CommentSerializer(serializers.ModelSerializer):
    create_time = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    owner = OwnerSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'body', 'body_en', 'body_ru', 'body_uz', 'owner', 'create_time', 'likes_count', 'likes']

    def get_create_time(self, obj):
        return obj.create_time.strftime("%d-%m-%Y %H:%M:%S")

    def get_likes_count(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        return Like.objects.filter(content_type=content_type, object_id=obj.id).count()

    def get_likes(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        likes = Like.objects.filter(content_type=content_type, object_id=obj.id)
        return LikeSerializer(likes, many=True).data


class SimpleCommentSerializer(CommentSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'body', 'body_en', 'body_ru', 'body_uz', 'owner', 'create_time']


class NewsSerializer(serializers.ModelSerializer):
    create_time = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)
    likes = serializers.SerializerMethodField()

    def validate_src(self, value):
        if self.initial_data['type'] == 'Видео' or self.initial_data['type'] == 'Video':
            try:
                clip = VideoFileClip(value.temporary_file_path())
            except IOError:
                raise serializers.ValidationError("Файл должен быть видео")
        elif (self.initial_data['type'] == 'Фото' or self.initial_data['type'] == 'Photo' or
              self.initial_data['type'] == 'Foto'):
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError("Файл должен быть изображением")
            else:
                try:
                    Image.open(value)
                except IOError:
                    raise serializers.ValidationError("Невозможно открыть файл как изображение")
        return value

    class Meta:
        model = News
        fields = ['id', 'type', 'src', 'title', 'title_en', 'title_ru', 'title_uz', 'body', 'body_en', 'body_ru',
                  'body_uz', 'comments', 'create_time', 'likes_count', 'likes']

    def get_create_time(self, obj):
        return obj.create_time.strftime("%d-%m-%Y %H:%M:%S")

    def get_likes_count(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        return Like.objects.filter(content_type=content_type, object_id=obj.id).count()

    def get_likes(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        likes = Like.objects.filter(content_type=content_type, object_id=obj.id)
        return LikeSerializer(likes, many=True).data


class SimpleNewsSerializer(NewsSerializer):
    class Meta:
        model = News
        fields = ['id', 'type', 'src', 'title', 'title_en', 'title_ru', 'title_uz', 'body', 'body_en', 'body_ru',
                  'body_uz', 'comments', 'create_time']


class PostsSerializer(serializers.ModelSerializer):
    create_time = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)
    likes = serializers.SerializerMethodField()
    owner = OwnerSerializer(read_only=True)

    def validate_src(self, value):
        if self.initial_data['type'] == 'Видео' or self.initial_data['type'] == 'Video':
            try:
                clip = VideoFileClip(value.temporary_file_path())
            except IOError:
                raise serializers.ValidationError("Файл должен быть видео")
        elif (self.initial_data['type'] == 'Фото' or self.initial_data['type'] == 'Photo' or
              self.initial_data['type'] == 'Foto'):
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError("Файл должен быть изображением")
            else:
                try:
                    Image.open(value)
                except IOError:
                    raise serializers.ValidationError("Невозможно открыть файл как изображение")
        return value

    class Meta:
        model = Posts
        fields = ['id', 'type', 'src', 'title', 'title_en', 'title_ru', 'title_uz', 'body', 'body_en', 'body_ru',
                  'body_uz', 'comments', 'create_time', 'owner', 'likes_count', 'likes']

    def get_create_time(self, obj):
        return obj.create_time.strftime("%d-%m-%Y %H:%M:%S")

    def get_likes_count(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        return Like.objects.filter(content_type=content_type, object_id=obj.id).count()

    def get_likes(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        likes = Like.objects.filter(content_type=content_type, object_id=obj.id)
        return LikeSerializer(likes, many=True).data


class SimplePostsSerializer(PostsSerializer):
    class Meta:
        model = Posts
        fields = ['id', 'type', 'src', 'title', 'title_en', 'title_ru', 'title_uz', 'body', 'body_en', 'body_ru',
                  'body_uz', 'comments', 'create_time', 'owner']


class StoriesSerializer(serializers.ModelSerializer):
    create_time = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)
    owner = OwnerSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()

    def validate_src(self, value):
        if self.initial_data['type'] == 'Видео' or self.initial_data['type'] == 'Video':
            try:
                clip = VideoFileClip(value.temporary_file_path())
            except IOError:
                raise serializers.ValidationError("Файл должен быть видео")
        elif (self.initial_data['type'] == 'Фото' or self.initial_data['type'] == 'Photo' or
              self.initial_data['type'] == 'Foto'):
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError("Файл должен быть изображением")
            else:
                try:
                    Image.open(value)
                except IOError:
                    raise serializers.ValidationError("Невозможно открыть файл как изображение")
        return value

    class Meta:
        model = Stories
        fields = ['id', 'type', 'src', 'title', 'title_en', 'title_ru', 'title_uz', 'comments', 'create_time', 'owner',
                  'likes_count', 'likes']

    def get_create_time(self, obj):
        return obj.create_time.strftime("%d-%m-%Y %H:%M:%S")

    def get_likes_count(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        return Like.objects.filter(content_type=content_type, object_id=obj.id).count()

    def get_likes(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        likes = Like.objects.filter(content_type=content_type, object_id=obj.id)
        return LikeSerializer(likes, many=True).data


class SimpleStoriesSerializer(StoriesSerializer):
    class Meta:
        model = Stories
        fields = ['id', 'type', 'src', 'title', 'title_en', 'title_ru', 'title_uz', 'comments', 'create_time', 'owner']


class UserSubscriptionSerializer(OwnerSerializer):
    subscriber_subscribed_date = serializers.SerializerMethodField()
    subscribed_date = serializers.SerializerMethodField()

    class Meta(OwnerSerializer.Meta):
        fields = OwnerSerializer.Meta.fields + ['subscriber_subscribed_date', 'subscribed_date']

    def get_subscriber_subscribed_date(self, obj):
        subscription = Subscription.objects.get(subscriber=obj, subscribed_to=self.context['userprofile'])
        return subscription.subscriber_subscribed_date.strftime("%d-%m-%Y %H:%M:%S")

    def get_subscribed_date(self, obj):
        subscription = Subscription.objects.get(subscriber=self.context['userprofile'], subscribed_to=obj)
        return subscription.subscribed_date.strftime("%d-%m-%Y %H:%M:%S")


class UserSerializer(OwnerSerializer):
    stories = StoriesSerializer(many=True, read_only=True)
    posts = PostsSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    likes = serializers.SerializerMethodField()
    subscribers = serializers.SerializerMethodField()
    subscribers_count = serializers.SerializerMethodField()
    subscribes = serializers.SerializerMethodField()
    subscribes_count = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'avatar', 'banner', 'stories', 'posts', 'comments', 'likes', 'subscribers',
                  'subscribers_count', 'subscribes', 'subscribes_count']

    def get_likes(self, obj):
        likes = Like.objects.filter(owner=obj)
        return UsersLikeSerializer(likes, many=True).data

    def get_subscribers(self, obj):
        subscribers = obj.subscribers.all()
        context = self.context
        context['userprofile'] = obj
        return UserSubscriptionSerializer(subscribers, many=True, context=context).data

    def get_subscribers_count(self, obj):
        return obj.subscribers.count()

    def get_subscribes(self, obj):
        subscribes = obj.subscribes.all()
        context = self.context
        context['userprofile'] = obj
        return UserSubscriptionSerializer(subscribes, many=True, context=context).data

    def get_subscribes_count(self, obj):
        return obj.subscribes.count()

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user')
        user = instance.user
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.banner = validated_data.get('banner', instance.banner)
        instance.save()
        user.username = user_data.get('username', user.username)
        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.email = user_data.get('email', user.email)
        user.is_active = user_data.get('is_active', user.is_active)
        user.save()
        return instance
