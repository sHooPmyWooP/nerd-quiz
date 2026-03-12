from django import forms
from django.forms import formset_factory, inlineformset_factory

from .models import Category, GameSession, Question, Quiz, Team

POINT_VALUES = [100, 200, 300, 600, 1000]


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['name', 'description']
        labels = {
            'name': 'Name',
            'description': 'Beschreibung',
        }


CategoryFormSet = inlineformset_factory(
    Quiz, Category,
    fields=['name'],
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['category', 'text', 'base_points', 'image', 'video_url', 'answer_notes']
        labels = {
            'category': 'Kategorie',
            'text': 'Frage',
            'image': 'Bild',
            'video_url': 'Video-URL',
            'answer_notes': 'Antwort & Notizen',
        }
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
            'answer_notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, quiz, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = quiz.categories.all()
        self.fields['base_points'] = forms.TypedChoiceField(
            choices=[(v, f'{v} pts') for v in POINT_VALUES],
            coerce=int,
            label='Points',
        )


class ChoiceForm(forms.Form):
    text = forms.CharField(
        max_length=500,
        required=False,
        label='',
        widget=forms.TextInput(attrs={'placeholder': 'Choice text…'}),
    )


ChoiceFormSet = formset_factory(ChoiceForm, extra=4)


TeamFormSet = inlineformset_factory(
    GameSession, Team,
    fields=['name'],
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
