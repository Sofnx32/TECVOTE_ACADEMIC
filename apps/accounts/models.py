from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.organizations.models import Organization


class CustomUserManager(BaseUserManager):
    def create_user(self, email, institutional_id, password=None, **extra_fields):
        if not email:
            raise ValueError(_("El correo electrónico es obligatorio."))
        if not institutional_id:
            raise ValueError(_("El ID institucional es obligatorio."))
        
        email = self.normalize_email(email)
        
        username = extra_fields.get("username")
        if not username:
            username = email.split('@')[0]
            
            counter = 1
            base_username = username
            while self.model.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1
        
        extra_fields["username"] = username
        extra_fields.setdefault("is_active", True)
        
        user = self.model(email=email, institutional_id=institutional_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "ADMIN")
        extra_fields.setdefault("must_change_password", False)
        institutional_id = extra_fields.get("institutional_id", email)
        
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("El superusuario debe tener is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("El superusuario debe tener is_superuser=True."))
        
        return self.create_user(email, institutional_id, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "STUDENT", _("Estudiante")
        TEACHER = "TEACHER", _("Docente")
        ADMIN = "ADMIN", _("Administrador")
        ELECTORAL_COMMISSION = "ELECTORAL_COMMISSION", _("Comisión Electoral")
        OBSERVER = "OBSERVER", _("Observador")

    email = models.EmailField(
        unique=True, 
        verbose_name=_("Correo electrónico")
    )
    
    institutional_id = models.CharField(
        max_length=30,
        unique=True,
        verbose_name=_("ID Institucional"),
        help_text=_("Código único (Ej: ADMIN-TECSUP, 20210001)")
    )
    
    username = models.CharField(
        max_length=150, 
        unique=True, 
        verbose_name=_("Nombre de usuario")
    )
    
    role = models.CharField(
        max_length=40, 
        choices=Role.choices, 
        default=Role.STUDENT,
        verbose_name=_("Rol")
    )
    
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Email verificado")
    )
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True,
        verbose_name=_("Organización")
    )
    
    two_factor_enabled = models.BooleanField(
        default=False,
        verbose_name=_("2FA Activo")
    )
    
    two_factor_secret = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        verbose_name=_("Secreto 2FA")
    )
    
    two_factor_backup_codes = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Códigos de respaldo 2FA")
    )
    
    must_change_password = models.BooleanField(
        default=True,
        verbose_name=_("Forzar cambio de contraseña")
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["institutional_id"]

    class Meta:
        verbose_name = _("Usuario")
        verbose_name_plural = _("Usuarios")
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"