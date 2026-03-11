from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CategoryFormSet, ChoiceFormSet, QuestionForm, QuizForm, TeamFormSet
from .models import GameSession, Question, Quiz


def homepage(request):
    quizzes = Quiz.objects.annotate(
        question_count=Count('categories__questions')
    ).order_by('-date')
    return render(request, 'homepage.html', {'quizzes': quizzes})


# ── Step 1: Quiz details ──────────────────────────────────────────────────────

def quiz_create(request):
    form = QuizForm(request.POST or None)
    if form.is_valid():
        quiz = form.save()
        return redirect('quiz_add_categories', pk=quiz.pk)
    return render(request, 'quiz_create.html', {'form': form})


def play_start(request, quiz_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    session = GameSession.objects.create(quiz=quiz)
    return redirect('play_add_teams', session_pk=session.pk)


def play_add_teams(request, session_pk):
    session = get_object_or_404(GameSession, pk=session_pk)
    formset = TeamFormSet(request.POST or None, instance=session)
    if formset.is_valid():
        formset.save()
        return redirect('homepage')  # placeholder until the play view exists
    return render(request, 'play_add_teams.html', {'session': session, 'formset': formset})


def quiz_edit(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    form = QuizForm(request.POST or None, instance=quiz)
    if form.is_valid():
        form.save()
        return redirect('homepage')
    return render(request, 'quiz_edit.html', {'quiz': quiz, 'form': form})


# ── Step 2: Categories ────────────────────────────────────────────────────────

def quiz_add_categories(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    formset = CategoryFormSet(request.POST or None, instance=quiz)
    if formset.is_valid():
        formset.save()
        return redirect('quiz_add_questions', pk=quiz.pk)
    return render(request, 'quiz_add_categories.html', {'quiz': quiz, 'formset': formset})


# ── Step 3: Questions ─────────────────────────────────────────────────────────

def quiz_add_questions(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)

    if request.method == 'POST' and 'finish' in request.POST:
        return redirect('homepage')

    form = QuestionForm(quiz, request.POST or None, request.FILES or None)
    choice_formset = ChoiceFormSet(request.POST if request.method == 'POST' else None)

    if request.method == 'POST' and 'finish' not in request.POST:
        is_mc = request.POST.get('answer_type') == Question.AnswerType.MULTIPLE_CHOICE
        form_valid = form.is_valid()
        choices_valid = (not is_mc) or choice_formset.is_valid()

        if form_valid and choices_valid:
            question = form.save()
            if is_mc:
                for f in choice_formset:
                    text = f.cleaned_data.get('text', '').strip()
                    if text:
                        question.choices.create(text=text)
            form = QuestionForm(quiz)
            choice_formset = ChoiceFormSet()

    questions = Question.objects.filter(
        category__quiz=quiz
    ).select_related('category').order_by('category__name', 'base_points')

    return render(request, 'quiz_add_questions.html', {
        'quiz': quiz,
        'form': form,
        'choice_formset': choice_formset,
        'questions': questions,
    })
