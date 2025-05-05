from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.urls import reverse


class StudyGroup(models.Model):
    name = models.CharField(_('name'), max_length=100)
    subject = models.CharField(_('subject'), max_length=50)
    description = models.TextField(_('description'))
    created_at = models.DateTimeField(_('created at'), default=timezone.now)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='dashboard_study_groups', 
        verbose_name=_('members')
    )

    class Meta:
        verbose_name = _('study group')
        verbose_name_plural = _('study groups')
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('studygroup-detail', kwargs={'pk': self.pk})


class StudySession(models.Model):
    title = models.CharField(_('title'), max_length=100)
    group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_('group')
    )
    start_time = models.DateTimeField(_('start time'))
    end_time = models.DateTimeField(_('end time'))
    attendees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='dashboard_attended_sessions', 
        blank=True,
        verbose_name=_('attendees')
    )

    class Meta:
        verbose_name = _('study session')
        verbose_name_plural = _('study sessions')
        ordering = ['-start_time']

    def duration(self):
        """Returns duration in minutes"""
        return (self.end_time - self.start_time).total_seconds() / 60

    def __str__(self):
        return f"{self.title} ({self.group.name})"


class Resource(models.Model):
    RESOURCE_TYPE_CHOICES = [
        ('DOC', _('Document')),
        ('PPT', _('Presentation')),
        ('IMG', _('Image')),
        ('CODE', _('Code')),
    ]

    title = models.CharField(_('title'), max_length=100)
    file = models.FileField(
        _('file'),
        upload_to='resources/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'ppt', 'pptx', 'jpg', 'png', 'py'])]
    )
    file_type = models.CharField(
        _('file type'),
        max_length=10,
        choices=RESOURCE_TYPE_CHOICES
    )
    size = models.PositiveIntegerField(
        _('size'),
        help_text=_("Size in bytes"),
        default=0
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_uploaded_resources',  
        verbose_name=_('uploaded by')
    )
    uploaded_at = models.DateTimeField(_('uploaded at'), auto_now_add=True)
    groups = models.ManyToManyField(
        StudyGroup,
        related_name='dashboard_resources',  
        verbose_name=_('groups')
    )

    class Meta:
        verbose_name = _('resource')
        verbose_name_plural = _('resources')
        ordering = ['-uploaded_at']

    def save(self, *args, **kwargs):
        if self.file and not self.size:
            self.size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('resource-detail', kwargs={'pk': self.pk})


class UserActivity(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_activity',  
        verbose_name=_('user')
    )
    study_hours = models.PositiveIntegerField(_('study hours'), default=0)
    sessions_attended = models.PositiveIntegerField(_('sessions attended'), default=0)
    groups_joined = models.PositiveIntegerField(_('groups joined'), default=0)
    resources_shared = models.PositiveIntegerField(_('resources shared'), default=0)
    last_updated = models.DateTimeField(_('last updated'), auto_now=True)

    class Meta:
        verbose_name = _('user activity')
        verbose_name_plural = _('user activities')

    def __str__(self):
        return _("%(username)s's Activity") % {'username': self.user.username}
    
