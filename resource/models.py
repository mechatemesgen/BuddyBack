from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.urls import reverse
from django.utils.text import slugify

User = get_user_model()

class StudyGroup(models.Model):
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    members = models.ManyToManyField(
        User,
        related_name='study_groups',
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


class ResourceCategory(models.Model):
    name = models.CharField(_('name'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), max_length=100, unique=True,default='default-slug')
    description = models.TextField(_('description'), blank=True)
    icon = models.CharField(_('icon'), max_length=50, blank=True, default='folder')

    class Meta:
        verbose_name = _('resource category')
        verbose_name_plural = _('resource categories')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(_('name'), max_length=50, unique=True)
    slug = models.SlugField(_('slug'), max_length=50, unique=True,default='default-slug')
    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Resource(models.Model):
    RESOURCE_TYPE_CHOICES = [
        ('DOCUMENT', _('Document')),
        ('PRESENTATION', _('Presentation')),
        ('IMAGE', _('Image')),
        ('CODE', _('Code')),
        ('VIDEO', _('Video')),
        ('AUDIO', _('Audio')),
        ('ARCHIVE', _('Archive')),
        ('OTHER', _('Other')),
    ]

    FILE_EXTENSIONS = {
        'DOCUMENT': ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'],
        'PRESENTATION': ['ppt', 'pptx', 'odp'],
        'IMAGE': ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'],
        'CODE': ['py', 'js', 'java', 'cpp', 'c', 'html', 'css', 'php'],
        'VIDEO': ['mp4', 'mov', 'avi', 'mkv', 'webm'],
        'AUDIO': ['mp3', 'wav', 'ogg', 'm4a'],
        'ARCHIVE': ['zip', 'rar', '7z', 'tar', 'gz'],
    }

    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    file = models.FileField(
        _('file'),
        upload_to='resources/%Y/%m/%d/',
        validators=[FileExtensionValidator(
            allowed_extensions=sum(FILE_EXTENSIONS.values(), [])
        )],
    )
    resource_type = models.CharField(
        _('resource type'),
        max_length=20,
        choices=RESOURCE_TYPE_CHOICES,
        default='DOCUMENT'
    )
    size = models.PositiveBigIntegerField(_('size'), editable=False, default=0)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_resources',
        verbose_name=_('uploaded by')
    )
    groups = models.ManyToManyField(
        StudyGroup,
        related_name='resources',
        blank=True,
        verbose_name=_('shared groups')
    )
    categories = models.ManyToManyField(
        ResourceCategory,
        related_name='resources',
        blank=True,
        verbose_name=_('categories')
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='resources',
        blank=True,
        verbose_name=_('tags')
    )
    is_favorite = models.BooleanField(_('is favorite'), default=False)
    is_public = models.BooleanField(_('is public'), default=False)
    uploaded_at = models.DateTimeField(_('uploaded at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    download_count = models.PositiveIntegerField(_('download count'), default=0)

    class Meta:
        verbose_name = _('resource')
        verbose_name_plural = _('resources')
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['resource_type']),
            models.Index(fields=['uploaded_at']),
            models.Index(fields=['is_public']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_resource_type_display()})"

    def save(self, *args, **kwargs):
        if self.file and not self.pk:  # New instance with file
            self.size = self.file.size
            if not self.resource_type or self.resource_type == 'DOCUMENT':
                self.determine_resource_type()
        super().save(*args, **kwargs)

    def determine_resource_type(self):
        """Auto-detect resource type based on file extension"""
        extension = self.file.name.split('.')[-1].lower()
        for resource_type, extensions in self.FILE_EXTENSIONS.items():
            if extension in extensions:
                self.resource_type = resource_type
                return
        self.resource_type = 'OTHER'

    @property
    def file_extension(self):
        """Get uppercase file extension without the dot"""
        return self.file.name.split('.')[-1].upper()

    @property
    def formatted_size(self):
        """Return human-readable file size"""
        if not self.size:
            return "0 bytes"
            
        size = float(self.size)
        for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def increment_download_count(self):
        """Atomically increment download count"""
        Resource.objects.filter(pk=self.pk).update(
            download_count=models.F('download_count') + 1
        )
        self.refresh_from_db()

    def get_absolute_url(self):
        return reverse('resource-detail', kwargs={'pk': self.pk})
