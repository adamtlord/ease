from django.contrib.auth.models import BaseUserManager

from django.db import models
from django.db.models import Q


class CustomUserManager(BaseUserManager):

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class ActiveCustomersManager(models.Manager):
    def get_queryset(self):
        return super(ActiveCustomersManager, self).get_queryset() \
            .filter(is_active=True) \
            .exclude(plan__isnull=True)


class InactiveCustomersManager(models.Manager):
    def get_queryset(self):
        return super(InactiveCustomersManager, self).get_queryset() \
            .filter(Q(is_active=False) | Q(plan__isnull=True))
