from django.apps import AppConfig
from django.db.models.signals import post_migrate


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        post_migrate.connect(create_or_update_site, sender=self)


def create_or_update_site(sender, **kwargs):
    from django.contrib.sites.models import Site
    SITE_ID = 1
    DEFAULT_SITE_DOMAIN = 'sociosphere.uz'
    DEFAULT_SITE_NAME = 'sociosphere.uz'
    try:
        site = Site.objects.get(pk=SITE_ID)
        site.domain = DEFAULT_SITE_DOMAIN
        site.name = DEFAULT_SITE_NAME
        site.save()
    except Site.DoesNotExist:
        Site.objects.create(pk=SITE_ID, domain=DEFAULT_SITE_DOMAIN, name=DEFAULT_SITE_NAME)
