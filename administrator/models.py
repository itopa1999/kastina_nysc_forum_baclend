from django.db import models
from django.contrib.auth.models import AbstractUser


from administrator.manager import UserManager

# Create your models here.


# Category model for grouping discussions
class CDS_Group(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),  # Index for the name field
        ]
    
    def __str__(self):
        return self.name
    
    

class User(AbstractUser):
    username = models.CharField(max_length=15)
    email = models.EmailField(max_length=40, unique=True)
    state_code = models.CharField(max_length=15)
    cds_group = models.ForeignKey(CDS_Group, on_delete=models.SET_NULL, null=True, blank=True)
    def save(self, *args, **kwargs):
        self.first_name = self.first_name.capitalize()
        self.last_name = self.last_name.capitalize()
        super().save(*args, **kwargs)

    objects=UserManager( )
    USERNAME_FIELD ='email'
    REQUIRED_FIELDS=['username','first_name','last_name']

    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['-id']),
        ]
    
    def __str__(self):
        return f"{self.email}"