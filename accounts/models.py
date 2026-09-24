from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class Role(models.TextChoices):
    PHYSICIAN = "physician", "طبیب"
    SECRETARY = "secretary", "منشی"
    MANAGER   = "manager",   "مدیر مطب"


class UserManager(BaseUserManager):
    def create_user(self, national_code, password=None, **extra):
        if not national_code:
            raise ValueError("کد ملی الزامی است")
        user = self.model(national_code=national_code, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, national_code, password, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", Role.MANAGER)
        return self.create_user(national_code, password, **extra)


class User(AbstractUser):
    username = None
    first_name = models.CharField("نام", max_length=100)
    last_name = models.CharField("نام خانوادگی", max_length=100)
    national_code = models.CharField("کد ملی", max_length=10, unique=True)
    role = models.CharField("نقش", max_length=20, choices=Role.choices, default=Role.SECRETARY)
    phone = models.CharField("تلفن همراه", max_length=15, blank=True)

    USERNAME_FIELD = "national_code"
    REQUIRED_FIELDS = ["first_name", "last_name"]
    objects = UserManager()

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self):
        return f"{self.get_full_name()} — {self.get_role_display()}"