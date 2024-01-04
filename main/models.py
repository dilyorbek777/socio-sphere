from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .translation import translate_text
from django.db import models

TYPE_CHOICES_TRANSLATIONS = {
    'ru': [('Видео', 'Видео'), ('Фото', 'Фото')],
    'en': [('Видео', 'Video'), ('Фото', 'Photo')],
    'uz': [('Видео', 'Video'), ('Фото', 'Foto')],
}


class Subscription(models.Model):
    subscriber = models.ForeignKey('UserProfile', related_name='subscribes', on_delete=models.CASCADE)
    subscribed_to = models.ForeignKey('UserProfile', related_name='subscribers', on_delete=models.CASCADE)
    subscriber_subscribed_date = models.DateTimeField(auto_now_add=True)
    subscribed_date = models.DateTimeField(auto_now_add=True)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    banner = models.ImageField(upload_to='banners/', null=True, blank=True)
    subscriptions = models.ManyToManyField('self', through='Subscription', symmetrical=False)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            UserProfile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.userprofile.save()

    def __str__(self):
        return self.user.username


class News(models.Model):
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=5, choices=TYPE_CHOICES_TRANSLATIONS)
    src = models.FileField(upload_to='src/')
    title = models.CharField(max_length=100)
    title_en = models.CharField(max_length=100, blank=True)
    title_ru = models.CharField(max_length=100, blank=True)
    title_uz = models.CharField(max_length=100, blank=True)
    body = models.TextField()
    body_en = models.TextField(blank=True)
    body_ru = models.TextField(blank=True)
    body_uz = models.TextField(blank=True)
    create_time = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.title_en = translate_text(self.title, 'en')
        self.title_ru = translate_text(self.title, 'ru')
        self.title_uz = translate_text(self.title, 'uz')
        self.body_en = translate_text(self.body, 'en')
        self.body_ru = translate_text(self.body, 'ru')
        self.body_uz = translate_text(self.body, 'uz')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta():
        verbose_name = "News"
        verbose_name_plural = "News"


class Posts(models.Model):
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=5, choices=TYPE_CHOICES_TRANSLATIONS)
    src = models.FileField(upload_to='src/')
    title = models.CharField(max_length=100)
    title_en = models.CharField(max_length=100, blank=True)
    title_ru = models.CharField(max_length=100, blank=True)
    title_uz = models.CharField(max_length=100, blank=True)
    body = models.TextField()
    body_en = models.TextField(blank=True)
    body_ru = models.TextField(blank=True)
    body_uz = models.TextField(blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='posts')

    def save(self, *args, **kwargs):
        self.title_en = translate_text(self.title, 'en')
        self.title_ru = translate_text(self.title, 'ru')
        self.title_uz = translate_text(self.title, 'uz')
        self.body_en = translate_text(self.body, 'en')
        self.body_ru = translate_text(self.body, 'ru')
        self.body_uz = translate_text(self.body, 'uz')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta():
        verbose_name = "Post"
        verbose_name_plural = "Posts"


class Stories(models.Model):
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=5, choices=TYPE_CHOICES_TRANSLATIONS)
    src = models.FileField(upload_to='src/')
    title = models.TextField()
    title_en = models.TextField(blank=True)
    title_ru = models.TextField(blank=True)
    title_uz = models.TextField(blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='stories')

    def save(self, *args, **kwargs):
        self.title_en = translate_text(self.title, 'en')
        self.title_ru = translate_text(self.title, 'ru')
        self.title_uz = translate_text(self.title, 'uz')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta():
        verbose_name = "Story"
        verbose_name_plural = "Stories"


class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    body = models.TextField()
    body_en = models.TextField(blank=True)
    body_ru = models.TextField(blank=True)
    body_uz = models.TextField(blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    story = models.ForeignKey(Stories, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)

    def save(self, *args, **kwargs):
        self.body_en = translate_text(self.body, 'en')
        self.body_ru = translate_text(self.body, 'ru')
        self.body_uz = translate_text(self.body, 'uz')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.owner.user.username


class Like(models.Model):
    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    create_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.owner.user.username
