from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    pass

class Profile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    date_of_birth = models.DateField(blank=True, null=True, verbose_name='Дата рождения')
    photo = models.ImageField(upload_to='users/%Y/%m/%d/', blank=True, null=True, verbose_name='Аватар')

    def __str__(self):
        return f'Профиль пользователя {self.user.username}'