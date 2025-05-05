from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.conf import settings

class CustomUserManager(BaseUserManager):
    
    def create_user(self, email, full_name="Unknown User", password=None, **extra_fields):
        if not email:
            raise ValueError(_('Users must have an email address'))
        if not full_name:
            raise ValueError(_('Users must provide their full name'))

        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        
        UserProfile.objects.create(user=user)

        return user

    def create_superuser(self, email, full_name="Unknown User", password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, full_name, password, **extra_fields)

 
class CustomUser(AbstractBaseUser, PermissionsMixin):
    
    # Basic user fields
    email = models.EmailField(_('email address'), unique=True)
    full_name = models.CharField(_('full name'), max_length=100, default="Unknown User")
    avatar = models.ImageField(_('avatar'), upload_to='avatars/%Y/%m/%d/', null=True, blank=True)
    bio = models.TextField(_('biography'), blank=True, null=True, max_length=500)
    
    # User stats
    sessions_attended = models.PositiveIntegerField(_('sessions attended'), default=0, validators=[MinValueValidator(0)])
    study_hours = models.PositiveIntegerField(_('study hours'), default=0, validators=[MinValueValidator(0)])
    
    # User permissions and states
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_active = models.BooleanField(_('active'), default=True)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_active = models.DateTimeField(_('last active'), auto_now=True)

    # Required fields for user login
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  
    objects = CustomUserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    def get_short_name(self):
        """Return the first name of the user or email if full name is missing."""
        return self.full_name.split()[0] if self.full_name else self.email
    @property
    def settings_safe(self):
        from users.models import Settings
        settings, created = Settings.objects.get_or_create(user=self)
        return settings


class UserProfile(models.Model):
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile', verbose_name=_('user'))
    university = models.CharField(_('university'), max_length=255, blank=True)
    department = models.CharField(_('department'), max_length=255, blank=True)
    academic_level = models.CharField(_('academic level'), max_length=50, blank=True)
    skills = models.TextField(_('skills'), blank=True, help_text=_('Comma-separated list of skills'))
    linkedin_url = models.URLField(_('LinkedIn URL'), blank=True, null=True)
    github_url = models.URLField(_('GitHub URL'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self):
        return f"Profile of {self.user.full_name}"


class Group(models.Model):
    
    name = models.CharField(_('group name'), max_length=255)
    description = models.TextField(_('description'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class GroupMembership(models.Model):
    
    ROLE_CHOICES = [
        ('ADMIN', _('Admin')),
        ('MODERATOR', _('Moderator')),
        ('MEMBER', _('Member')),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='group_memberships')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(_('role'), max_length=10, choices=ROLE_CHOICES, default='MEMBER')
    joined_at = models.DateTimeField(_('joined at'), auto_now_add=True)
    is_active = models.BooleanField(_('is active'), default=True)

    class Meta:
        verbose_name = _('group membership')
        verbose_name_plural = _('group memberships')
        unique_together = ('user', 'group')
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.group.name} ({self.role})"


class StudySession(models.Model):
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(_('session title'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    start_time = models.DateTimeField(_('start time'))
    end_time = models.DateTimeField(_('end time'))
    location = models.CharField(_('location'), max_length=255, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('study session')
        verbose_name_plural = _('study sessions')
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.title} - {self.group.name}"

    @property
    def duration(self):
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds() / 3600
        return 0


class SessionAttendance(models.Model):
    """Track attendance for study sessions."""
    
    STATUS_CHOICES = [
        ('PRESENT', _('Present')),
        ('ABSENT', _('Absent')),
        ('LATE', _('Late')),
    ]

    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name='attendances')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='session_attendances')
    status = models.CharField(_('attendance status'), max_length=7, choices=STATUS_CHOICES, default='PRESENT')
    joined_at = models.DateTimeField(_('joined at'), auto_now_add=True)
    left_at = models.DateTimeField(_('left at'), null=True, blank=True)
    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        verbose_name = _('session attendance')
        verbose_name_plural = _('session attendances')
        unique_together = ('session', 'user')
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.session.title} ({self.status})"


class Resource(models.Model):
    
    RESOURCE_TYPES = [
        ('NOTE', _('Notes')),
        ('BOOK', _('Book')),
        ('SLIDE', _('Slides')),
        ('VIDEO', _('Video')),
        ('OTHER', _('Other')),
    ]

    title = models.CharField(_('title'), max_length=255)
    resource_type = models.CharField(_('resource type'), max_length=5, choices=RESOURCE_TYPES, default='OTHER')
    file = models.FileField(_('file'), upload_to='resources/%Y/%m/%d/')
    description = models.TextField(_('description'), blank=True)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='uploaded_resources_in_users', verbose_name=_('uploaded by'))
    uploaded_at = models.DateTimeField(_('uploaded at'), auto_now_add=True)
    session = models.ForeignKey(StudySession, on_delete=models.SET_NULL, null=True, blank=True, related_name='resources')

    class Meta:
        verbose_name = _('resource')
        verbose_name_plural = _('resources')
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} ({self.get_resource_type_display()})"


class PasswordResetToken(models.Model):
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(_('token'), max_length=255, unique=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'))
    is_used = models.BooleanField(_('is used'), default=False)

    class Meta:
        verbose_name = _('password reset token')
        verbose_name_plural = _('password reset tokens')
        ordering = ['-created_at']

    def __str__(self):
        return f"Password reset token for {self.user.email}"
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
    



class UserSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='settings'
    )

    email_notifications = models.BooleanField(default=True)
    session_reminders = models.BooleanField(default=True)
    group_messages = models.BooleanField(default=True)
    resource_updates = models.BooleanField(default=True)
    new_member_alerts = models.BooleanField(default=True)

    # Appearance settings
    theme = models.CharField(
        max_length=10,
        choices=[('light', 'Light'), ('dark', 'Dark')],
        default='light'
    )

    # Privacy settings
    show_profile_stats = models.BooleanField(default=True)
    show_uploaded_resources = models.BooleanField(default=True)
    show_group_memberships = models.BooleanField(default=True)

    def __str__(self):
        return f"Settings for {self.user.email}"


