from django.db import models


class Quiz(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Question(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    base_points = models.PositiveIntegerField(default=100)
    image = models.ImageField(upload_to='questions/images/', blank=True, null=True)
    audio_file = models.FileField(upload_to='questions/audio/', blank=True, null=True)
    video_file = models.FileField(upload_to='questions/videos/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    answer_notes = models.TextField(blank=True)

    def __str__(self):
        return self.text[:80]


class GameSession(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    points_doubled = models.BooleanField(default=False)
    current_selector = models.ForeignKey(
        'Team', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='selector_sessions',
    )

    def __str__(self):
        return f"{self.quiz.name} — {self.started_at:%Y-%m-%d %H:%M}"


class Team(models.Model):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Score(models.Model):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='scores')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='scores')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='scores', null=True, blank=True)
    points = models.IntegerField(default=0)
    effective_points = models.IntegerField(default=0)

    class Meta:
        unique_together = [('session', 'question')]

    def __str__(self):
        return f"{self.question} → {self.team} ({self.points}pts)"


class Deduction(models.Model):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='deductions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='deductions')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='deductions')
    points = models.IntegerField()

    class Meta:
        unique_together = [('session', 'question', 'team')]

    def __str__(self):
        return f"{self.question} → -{self.points}pts ({self.team})"


class Bonus(models.Model):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='bonuses')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='bonuses')
    points = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.team} +{self.points}pts"


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=500)

    def __str__(self):
        return self.text
