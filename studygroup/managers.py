from django.db import models
from django.db.models import Count

class StudyGroupManager(models.Manager):
    def annotate_member_count(self):
        return self.annotate(
            member_count=Count('members')
        )

    def public_groups(self):
        return self.filter(privacy='PUBLIC')

    def for_user(self, user):
        return self.filter(
            models.Q(privacy='PUBLIC') | 
            models.Q(members=user)
        ).distinct()