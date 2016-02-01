import os
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from adminsortable.models import SortableMixin
from adminsortable.fields import SortableForeignKey

MDHELP = 'This field supports <a target="_blank" href="http://daringfireball.net/projects/markdown/syntax">Markdown syntax</a>'
TICKET_LENGTH = 4

class Programme(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Course(SortableMixin):
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(help_text=MDHELP)
    programmes = models.ManyToManyField(Programme, related_name='courses')
    order = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    def colloquial_name(self):
        return self.slug.replace('-', ' ').replace('mto', 'mto-').upper()

    def __str__(self):
        return '%s (%s)' % (self.name, self.colloquial_name())

    def get_absolute_url(self):
        return reverse('course', args=[self.slug])

    class Meta:
        ordering = ['order']

class Session(SortableMixin):
    name = models.CharField(max_length=255)
    description = models.TextField(help_text=MDHELP)
    course = SortableForeignKey(Course, related_name="sessions")
    order = models.PositiveIntegerField(default=0, editable=False, db_index=True)
    registration_enabled = models.BooleanField(default=True)

    def __str__(self):
        return '%s: Session %i' % (self.course.colloquial_name(), self.get_number())

    def get_number(self):
        return self.course.sessions.filter(order__lt=self.order).count() + 1

    def get_absolute_url(self):
        return reverse('session', args=[self.course.slug, self.get_number()])

    class Meta:
        ordering = ['order']

class Assignment(SortableMixin):
    name = models.CharField(max_length=255)
    session = SortableForeignKey(Session, related_name="assignments")
    order = models.PositiveIntegerField(default=0, editable=False, db_index=True)
    type = models.IntegerField(choices=(
        (1, 'Preliminary assignment'),
        (2, 'In-class assignment'),
    ))
    locked = models.BooleanField(default=False, help_text='Locked assignments will automatically unlock when students register their attendance to class. If registration is disabled, it can only be unlocked by a staff member')

    def __str__(self):
        return '%s: %s' % (self.session.name, self.name)

    def get_number(self):
        return self.session.assignments.filter(order__lt=self.order).count() + 1

    def get_absolute_url(self):
        return reverse('assignment', args=[self.session.course.slug, self.session.get_number(), self.get_number()])

    class Meta:
        ordering = ['order']

class Step(SortableMixin):
    name = models.CharField(max_length=255)
    assignment = SortableForeignKey(Assignment, related_name='steps')
    description = models.TextField(help_text=MDHELP)
    order = models.PositiveIntegerField(default=0, editable=False, db_index=True)
    answer_required = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def get_number(self):
        return self.assignment.steps.filter(order__lt=self.order).count() + 1

    def get_absolute_url(self):
        return reverse('assignment', args=[
            self.assignment.session.course.slug,
            self.assignment.session.get_number(),
            self.assignment.get_number(),
        ]) + '?step=' + str(self.get_number())

    class Meta:
        ordering = ['order']

class CompletedStep(models.Model):
    step = models.ForeignKey(Step, related_name='completed')
    whom = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='completed')
    date = models.DateTimeField(auto_now_add=True)
    answer = models.TextField(blank=True)

    def __str__(self):
        return '%s has completed %s' % (self.whom.username, self.step.name)

    class Meta:
        verbose_name_plural = 'completed steps'

class Class(models.Model):
    session = models.ForeignKey(Session, related_name='classes')
    number = models.CharField(max_length=16)
    ticket = models.CharField(unique=True, max_length=16)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='attends', blank=True)

    def __str__(self):
        return 'Class %s of %s' % (self.number, str(self.session))

    class Meta:
        verbose_name_plural = 'classes'

class Download(models.Model):
    file = models.FileField()
    session = models.ManyToManyField(Session, related_name='downloads')

    def __str__(self):
        return os.path.basename(str(self.file))

    def url(self):
        return self.file.url
