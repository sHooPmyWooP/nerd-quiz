from django.db import models


class Quiz(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()

    def __str__(self):
        return self.name


class Question(models.Model):
    class AnswerType(models.TextChoices):
        MULTIPLE_CHOICE = 'multiple_choice', 'Multiple Choice'
        TEXT = 'text', 'Text'

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    answer_type = models.CharField(max_length=20, choices=AnswerType.choices)
    base_points = models.PositiveIntegerField(default=100)
    image = models.ImageField(upload_to='questions/images/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    answer_notes = models.TextField(blank=True)

    def __str__(self):
        return self.text[:80]


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=500)

    def __str__(self):
        return self.text
