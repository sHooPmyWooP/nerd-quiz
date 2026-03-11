from django import forms
from django.forms import formset_factory, inlineformset_factory

from .models import Category, GameSession, Question, Quiz, Team


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['name', 'description', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
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
        fields = ['category', 'text', 'answer_type', 'base_points', 'image', 'video_url', 'answer_notes']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
            'answer_notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, quiz, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = quiz.categories.all()


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
