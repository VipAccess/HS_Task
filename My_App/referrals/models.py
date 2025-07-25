from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    phone = models.CharField(max_length=15, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    invite_code = models.CharField(max_length=6, null=True, blank=True,
                                   unique=True)
    activated_invite = models.CharField(max_length=6, null=True, blank=True)

    def __str__(self):
        return f'{self.phone}'


class ReferralRelationship(models.Model):
    inviter = models.ForeignKey(Profile, related_name='invited_users',
                               on_delete=models.CASCADE)
    referral = models.ForeignKey(Profile, related_name='inviter',
                               on_delete=models.CASCADE)
    referral_token = models.CharField(max_length=6)