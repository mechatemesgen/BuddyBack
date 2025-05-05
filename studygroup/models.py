from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from django.core.validators import FileExtensionValidator
from django.utils import timezone

User = get_user_model()


class StudyGroupManager(models.Manager):
    def annotate_member_count(self):
        return self.annotate(member_count=Count('members'))

    def with_last_activity(self):
        return self.annotate(
            last_activity=models.Subquery(
                Session.objects.filter(
                    group=models.OuterRef('pk')
                ).order_by('-start_time').values('start_time')[:1]
            )
        )

class Subject(models.Model):
    name = models.CharField(_('name'), max_length=100, unique=True)
    code = models.CharField(_('code'), max_length=10, unique=True)
    description = models.TextField(_('description'), blank=True)
    icon = models.CharField(_('icon'), max_length=50, blank=True)
    color = models.CharField(_('color'), max_length=7, default='#6c757d')

    class Meta:
        verbose_name = _('subject')
        verbose_name_plural = _('subjects')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return self.name

class StudyGroup(models.Model):
    PRIVACY_CHOICES = [
        ('PUBLIC', _('Public - Anyone can join')),
        ('PRIVATE', _('Private - Invite only')),
        ('RESTRICTED', _('Restricted - Request to join')),
    ]

    name = models.CharField(_('name'), max_length=255, help_text=_('Name of the study group'))
    description = models.TextField(_('description'), help_text=_('Detailed description of the group'))
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='study_groups', verbose_name=_('subject'), help_text=_('Primary subject area of the group'))
    creator = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_groups', verbose_name=_('creator'), help_text=_('User who created this group'))
    members = models.ManyToManyField(User, through='GroupMembership', related_name='study_groups_set', verbose_name=_('members'), help_text=_('Users who are members of this group'))
    avatar = models.ImageField(_('avatar'), upload_to='group_avatars/%Y/%m/%d/', null=True, blank=True, help_text=_('Group profile picture'))
    privacy = models.CharField(_('privacy'), max_length=10, choices=PRIVACY_CHOICES, default='PUBLIC', help_text=_('Visibility and join permissions for the group'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True, help_text=_('When the group was created'))
    updated_at = models.DateTimeField(_('updated at'), auto_now=True, help_text=_('Last time the group was updated'))

    objects = StudyGroupManager()

    class Meta:
        verbose_name = _('study group')
        verbose_name_plural = _('study groups')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['privacy']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.subject})"

    @property
    def member_count(self):
        """Return the number of active members in the group."""
        return self.memberships.filter(is_active=True).count()

    @property
    def last_activity(self):
        """Return the timestamp of the last activity in the group."""
        last_session = self.sessions.order_by('-start_time').first()
        last_chat = self.chats.order_by('-created_at').first()

        dates = [self.updated_at]
        if last_session:
            dates.append(last_session.start_time)
        if last_chat:
            dates.append(last_chat.created_at)

        return max(dates) if dates else self.created_at

class GroupMembership(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', _('Admin - Full management rights')),
        ('MODERATOR', _('Moderator - Can manage content and members')),
        ('MEMBER', _('Member - Regular participant')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships_set', verbose_name=_('user'), help_text=_('User who is a member of the group'))
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='memberships_set', verbose_name=_('group'), help_text=_('Group the user belongs to'))
    role = models.CharField(_('role'), max_length=10, choices=ROLE_CHOICES, default='MEMBER', help_text=_('Role of the user in the group'))
    joined_at = models.DateTimeField(_('joined at'), auto_now_add=True, help_text=_('When the user joined the group'))
    is_active = models.BooleanField(_('is active'), default=True, help_text=_('Whether the membership is currently active'))

    class Meta:
        verbose_name = _('group membership')
        verbose_name_plural = _('group memberships')
        unique_together = ('user', 'group')
        ordering = ['-joined_at']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.user} in {self.group} ({self.role})"


class Session(models.Model):
    STATUS_CHOICES = [
        ('UPCOMING', _('Upcoming')),
        ('ONGOING', _('Ongoing')),
        ('COMPLETED', _('Completed')),
        ('CANCELLED', _('Cancelled')),
    ]

    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='sessions', verbose_name=_('group'), help_text=_('Group this session belongs to'))
    title = models.CharField(_('title'), max_length=255, help_text=_('Title or topic of the study session'))
    description = models.TextField(_('description'), blank=True, help_text=_('Detailed description of the session'))
    start_time = models.DateTimeField(_('start time'), help_text=_('When the session starts'))
    end_time = models.DateTimeField(_('end time'), null=True, blank=True, help_text=_('When the session ends'))
    location = models.CharField(_('location'), max_length=255, blank=True, help_text=_('Physical or virtual location of the session'))
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_sessions', verbose_name=_('created by'), help_text=_('User who created this session'))
    status = models.CharField(_('status'), max_length=10, choices=STATUS_CHOICES, default='UPCOMING', help_text=_('Current status of the session'))
    max_attendees = models.PositiveIntegerField(_('max attendees'), default=10, help_text=_('Maximum number of attendees allowed'))
    is_virtual = models.BooleanField(_('is virtual'), default=False, help_text=_('Whether this is a virtual session'))
    meeting_link = models.URLField(_('meeting link'), blank=True, help_text=_('Link for virtual sessions'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True, help_text=_('When the session was created'))

    class Meta:
        verbose_name = _('session')
        verbose_name_plural = _('sessions')
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['start_time']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.title} - {self.group.name}"

    @property
    def duration(self):
        """Calculate duration of the session in hours."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds() / 3600
        return 0.0

    def clean(self):
        """Validate the session before saving."""
        if self.end_time and self.end_time <= self.start_time:
            raise ValidationError(
                {'end_time': _('End time must be after start time.')}
            )


class GroupChat(models.Model):
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='chats', verbose_name=_('group'), help_text=_('Group this chat belongs to'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_chats', verbose_name=_('user'), help_text=_('User who sent the message'))
    message = models.TextField(_('message'), help_text=_('Content of the chat message'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True, help_text=_('When the message was sent'))
    updated_at = models.DateTimeField(_('updated at'), auto_now=True, help_text=_('When the message was last updated'))
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies', verbose_name=_('parent message'), help_text=_('Original message this is replying to'))

    class Meta:
        verbose_name = _('group chat')
        verbose_name_plural = _('group chats')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['group', 'created_at']),
        ]

    def __str__(self):
        return f"Chat from {self.user} in {self.group}"


class ChatAttachment(models.Model):
    FILE_TYPES = [
        ('DOCUMENT', _('Document')),
        ('IMAGE', _('Image')),
        ('AUDIO', _('Audio')),
        ('VIDEO', _('Video')),
        ('OTHER', _('Other')),
    ]

    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='attachments', verbose_name=_('chat'), help_text=_('Chat message this attachment belongs to'))
    file = models.FileField(_('file'), upload_to='chat_attachments/%Y/%m/%d/', help_text=_('Uploaded file attachment'), validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif', 'mp3', 'mp4', 'txt'])])
    file_type = models.CharField(_('file type'), max_length=10, choices=FILE_TYPES, help_text=_('Type of the attached file'))
    uploaded_at = models.DateTimeField(_('uploaded at'), auto_now_add=True, help_text=_('When the file was uploaded'))

    class Meta:
        verbose_name = _('chat attachment')
        verbose_name_plural = _('chat attachments')
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Attachment for chat {self.chat.id}"

    @property
    def filename(self):
        return self.file.name.split('/')[-1]

    @property
    def filesize(self):
        return self.file.size
