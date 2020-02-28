import os
from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe
from pandocfield import PandocField
from numberedmodel.models import NumberedModel
from .utils import clean

class Tag(models.Model):
    slug = models.SlugField('name', unique=True)

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('tag', args=[self.slug])

    class Meta:
        ordering = ['slug']

class Course(NumberedModel):
    order = models.PositiveIntegerField(blank=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = PandocField(blank=True)
    active = models.BooleanField(default=False, help_text='Inactive courses are not visible to students')

    def __str__(self):
        return '%s (%s)' % (self.name, self.colloquial_name())

    def colloquial_name(self):
        return self.slug.replace('-', ' ').replace('mto', 'mto-').upper()

    def url(self):
        return mark_safe('<a href="%(url)s">%(url)s</a>' % {'url': self.get_absolute_url()})

    def get_absolute_url(self):
        return reverse('course', args=[self.slug])

    class Meta:
        ordering = ['order']

class Session(NumberedModel):
    number = models.PositiveIntegerField(blank=True)
    course = models.ForeignKey(Course, related_name="sessions", on_delete=models.PROTECT)
    name = models.CharField(max_length=255, blank=True)
    description = PandocField(blank=True)
    registration_enabled = models.BooleanField(default=True, help_text='When enabled, class attendance will be registered')
    active = models.BooleanField(default=False, help_text='Inactive sessions are not visible to students')
    tags = models.ManyToManyField(Tag, related_name='sessions', blank=True)

    def __str__(self):
        return '%s: Session %i' % (self.course.colloquial_name(), self.number)

    def get_absolute_url(self):
        return reverse('session', args=[self.course.slug, self.number])

    def number_with_respect_to(self):
        return self.course.sessions.all()

    class Meta:
        ordering = ['number']

class Assignment(NumberedModel):
    number = models.PositiveIntegerField(blank=True)
    session = models.ForeignKey(Session, related_name='assignments', help_text='You can move assignments between sessions by using this dropdown menu', on_delete=models.PROTECT)
    name = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=False, help_text='Inactive assignments are not visible to students')
    locked = models.BooleanField(default=False, help_text='Locked assignments can only be made by students in class')

    def __str__(self):
        return self.name if self.name else 'Assignment {}'.format(self.number)

    def nr_of_steps(self):
        return self.steps.count()

    def get_absolute_url(self):
        return reverse('assignment', args=[self.session.course.slug, self.session.number, self.number])

    def number_with_respect_to(self):
        return self.session.assignments.all()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Ensure at least one step
        if not self.steps.first():
            Step(assignment=self).save()

    class Meta:
        ordering = ['number']

class Step(NumberedModel):
    number = models.PositiveIntegerField(blank=True)
    assignment = models.ForeignKey(Assignment, related_name='steps', on_delete=models.CASCADE)
    description = PandocField(blank=True)
    answer_required = models.BooleanField(default=False, help_text='If enabled, this step will show students an input field where they can enter their answer. Add one or more right answers below to have students’ answers checked for correctness.')

    def __str__(self):
        return 'Step {}'.format(self.number)

    def get_absolute_url(self):
        if hasattr(self, 'fullscreen') and self.fullscreen == True:
            parameter = '&fullscreen'
        else:
            parameter = ''

        return reverse('assignment', args=[
            self.assignment.session.course.slug,
            self.assignment.session.number,
            self.assignment.number,
        ]) + '?step=' + str(self.number) + parameter

    def number_with_respect_to(self):
        return self.assignment.steps.all()

    class Meta:
        ordering = ['number']

class RightAnswer(models.Model):
    step = models.ForeignKey(Step, related_name='right_answers', on_delete=models.CASCADE)
    value = models.CharField(max_length=255, help_text='This value can either be a case-insensitive string or a numeric value. For numeric values you can use the <a target="_blank" href="https://docs.moodle.org/23/en/GIFT_format">GIFT notation</a> of "answer:tolerance" or "low..high".')

    def __str__(self):
        return 'Right answer for {}'.format(self.step)

class WrongAnswer(models.Model):
    step = models.ForeignKey(Step, related_name='wrong_answers', on_delete=models.CASCADE)
    value = models.CharField(max_length=255, help_text='Supplying one or more wrong answers will turn this into a multiple choice question.')

    def __str__(self):
        return 'Wrong answer for {}'.format(self.step)

class CompletedStep(models.Model):
    step = models.ForeignKey(Step, related_name='completed', on_delete=models.CASCADE)
    whom = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='completed', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    answer = models.TextField(blank=True)
    passed = models.BooleanField(default=True)

    def __str__(self):
        return '%s has completed %s' % (self.whom.username, str(self.step))

    class Meta:
        verbose_name_plural = 'completed steps'

class Download(models.Model):
    session = models.ForeignKey(Session, related_name='downloads', on_delete=models.CASCADE)
    file = models.FileField()

    def __str__(self):
        return os.path.basename(str(self.file))

    def url(self):
        return self.file.url

    class Meta:
        ordering = ['file']

class Presentation(models.Model):
    session = models.ForeignKey(Session, related_name='presentations', on_delete=models.CASCADE)
    file = models.FileField()
    visibility = models.IntegerField(choices=(
        (0, 'Invisible'),
        (1, 'Only visible to teacher'),
        (2, 'Visible to students in class'),
        (3, 'Visible to everyone'),
    ), default=1)

    def __str__(self):
        return os.path.basename(str(self.file))

    def url(self):
        return self.file.url

    class Meta:
        ordering = ['file']

class Clarification(NumberedModel):
    number = models.PositiveIntegerField(blank=True)
    step = models.ForeignKey(Step, related_name='clarifications', on_delete=models.CASCADE)
    description = PandocField(blank=True)
    image = models.ImageField(blank=True)

    def __str__(self):
        return 'Clarification for %s' % str(self.step)

    def number_with_respect_to(self):
        return self.step.clarifications.all()

    class Meta:
        ordering = ['number']

class StepFile(models.Model):
    step = models.ForeignKey(Step, related_name='files', on_delete=models.CASCADE)
    file = models.FileField()

    def __str__(self):
        return os.path.basename(str(self.file))

    class Meta:
        ordering = ['file']
