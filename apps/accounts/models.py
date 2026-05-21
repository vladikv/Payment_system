from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar_initials = models.CharField(max_length=2, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.avatar_initials and self.user:
            first = self.user.first_name[:1].upper() if self.user.first_name else ''
            last = self.user.last_name[:1].upper() if self.user.last_name else ''
            self.avatar_initials = (first + last) or self.user.username[:2].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Profile {self.user.username}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        # Create wallet automatically
        from apps.wallets.models import Wallet
        Wallet.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
