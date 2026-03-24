from django.db.models import Count, F, OuterRef, Prefetch, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import POINT_VALUES, CategoryFormSet, ChoiceFormSet, QuestionForm, QuizForm, TeamFormSet
from .models import Bonus, Deduction, GameSession, Question, Quiz, Score


def homepage(request):
    quizzes = Quiz.objects.annotate(
        question_count=Count('categories__questions')
    ).order_by('-id')
    return render(request, 'homepage.html', {'quizzes': quizzes})


# ── Quiz creation wizard ──────────────────────────────────────────────────────

def quiz_create(request):
    form = QuizForm(request.POST or None)
    if form.is_valid():
        quiz = form.save()
        return redirect('quiz_add_categories', pk=quiz.pk)
    return render(request, 'quiz_create.html', {'form': form})


def quiz_edit(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    form = QuizForm(request.POST or None, instance=quiz)
    if form.is_valid():
        form.save()
        return redirect('homepage')
    return render(request, 'quiz_edit.html', {'quiz': quiz, 'form': form})


def quiz_delete(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    if request.method == 'POST':
        quiz.delete()
        return redirect('homepage')
    return render(request, 'quiz_delete.html', {'quiz': quiz})


def quiz_add_categories(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    formset = CategoryFormSet(request.POST or None, instance=quiz)
    if formset.is_valid():
        formset.save()
        return redirect('quiz_add_questions', pk=quiz.pk)
    return render(request, 'quiz_add_categories.html', {'quiz': quiz, 'formset': formset})


def quiz_add_questions(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)

    if request.method == 'POST' and 'finish' in request.POST:
        return redirect('homepage')

    # ── Delete ────────────────────────────────────────────────────────────────
    if request.method == 'POST' and 'delete_pk' in request.POST:
        Question.objects.filter(pk=request.POST['delete_pk'], category__quiz=quiz).delete()
        return redirect('quiz_add_questions', pk=quiz.pk)

    # ── Edit or Add ───────────────────────────────────────────────────────────
    editing = None
    edit_pk = request.POST.get('edit_pk') or request.GET.get('edit')
    if edit_pk:
        editing = get_object_or_404(Question, pk=edit_pk, category__quiz=quiz)

    form = QuestionForm(quiz, request.POST or None, request.FILES or None, instance=editing)

    if request.method == 'POST':
        choice_formset = ChoiceFormSet(request.POST)
    elif editing:
        initial = [{'text': c.text} for c in editing.choices.all()]
        choice_formset = ChoiceFormSet(initial=initial)
    else:
        choice_formset = ChoiceFormSet()

    if request.method == 'POST' and 'finish' not in request.POST and 'delete_pk' not in request.POST:
        form_valid = form.is_valid()
        choices_valid = choice_formset.is_valid()

        if form_valid and choices_valid:
            question = form.save()
            question.choices.all().delete()
            for f in choice_formset:
                text = f.cleaned_data.get('text', '').strip()
                if text:
                    question.choices.create(text=text)
            return redirect('quiz_add_questions', pk=quiz.pk)


    questions = Question.objects.filter(
        category__quiz=quiz
    ).select_related('category').order_by('category__name', 'base_points')

    # Build per-category completion grid
    points_by_cat = {}
    for q in questions:
        points_by_cat.setdefault(q.category_id, []).append(q.base_points)

    category_grid = []
    for cat in quiz.categories.all():
        used = points_by_cat.get(cat.pk, [])
        slots = []
        for pts in POINT_VALUES:
            count = used.count(pts)
            slots.append({'pts': pts, 'count': count})
        category_grid.append({'category': cat, 'slots': slots})

    return render(request, 'quiz_add_questions.html', {
        'quiz': quiz,
        'form': form,
        'choice_formset': choice_formset,
        'questions': questions,
        'category_grid': category_grid,
        'point_values': POINT_VALUES,
        'editing': editing,
    })


# ── Play ──────────────────────────────────────────────────────────────────────

def quiz_sessions(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)

    if request.method == 'POST' and 'delete_pk' in request.POST:
        GameSession.objects.filter(pk=request.POST['delete_pk'], quiz=quiz).delete()
        return redirect('quiz_sessions', pk=quiz.pk)

    sessions = quiz.sessions.annotate(
        team_count=Count('teams', distinct=True),
        answered_count=Count('scores', distinct=True),
    ).order_by('-started_at')
    return render(request, 'quiz_sessions.html', {'quiz': quiz, 'sessions': sessions})


def play_start(request, quiz_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    session = GameSession.objects.create(quiz=quiz)
    return redirect('play_add_teams', session_pk=session.pk)


def play_add_teams(request, session_pk):
    session = get_object_or_404(GameSession, pk=session_pk)
    formset = TeamFormSet(request.POST or None, instance=session)
    if formset.is_valid():
        formset.save()
        return redirect('play', session_pk=session.pk)
    return render(request, 'play_add_teams.html', {'session': session, 'formset': formset})


def play(request, session_pk):
    session = get_object_or_404(
        GameSession.objects.select_related('quiz'),
        pk=session_pk,
    )

    categories_qs = session.quiz.categories.prefetch_related(
        Prefetch('questions', queryset=Question.objects.order_by('base_points'))
    )
    categories_list = list(categories_qs)

    scores = Score.objects.filter(session=session).select_related('team')
    answered = {s.question_id: s for s in scores}

    earned_sq = Score.objects.filter(
        session=session, team=OuterRef('pk'),
    ).values('team').annotate(s=Sum('points')).values('s')
    deducted_sq = Deduction.objects.filter(
        session=session, team=OuterRef('pk'),
    ).values('team').annotate(s=Sum('points')).values('s')
    bonus_sq = Bonus.objects.filter(
        session=session, team=OuterRef('pk'),
    ).values('team').annotate(s=Sum('points')).values('s')

    team_scores = session.teams.annotate(
        earned=Coalesce(Subquery(earned_sq), Value(0)),
        deducted=Coalesce(Subquery(deducted_sq), Value(0)),
        bonus=Coalesce(Subquery(bonus_sq), Value(0)),
        total=F('earned') - F('deducted') + F('bonus'),
    ).order_by('name')

    total_questions = Question.objects.filter(category__quiz=session.quiz).count()
    answered_count = len(answered)

    # Build grid aligned by point value so rows stay in sync across categories
    all_point_values = sorted({
        q.base_points
        for cat in categories_list
        for q in cat.questions.all()
    })
    cat_question_map = {
        cat.pk: {q.base_points: q for q in cat.questions.all()}
        for cat in categories_list
    }
    board_rows = [
        [cat_question_map.get(cat.pk, {}).get(pts) for cat in categories_list]
        for pts in all_point_values
    ]

    selected_question = None
    question_deductions = []
    deducted_team_ids = set()
    q_pk = request.GET.get('question')
    if q_pk:
        selected_question = get_object_or_404(
            Question, pk=q_pk, category__quiz=session.quiz
        )
        question_deductions = list(
            Deduction.objects.filter(session=session, question=selected_question)
            .select_related('team').order_by('pk')
        )
        deducted_team_ids = {d.team_id for d in question_deductions}

    return render(request, 'play.html', {
        'session': session,
        'categories': categories_list,
        'board_rows': board_rows,
        'answered': answered,
        'team_scores': team_scores,
        'selected_question': selected_question,
        'question_deductions': question_deductions,
        'deducted_team_ids': deducted_team_ids,
        'multiplier': 2 if session.points_doubled else 1,
        'total_questions': total_questions,
        'answered_count': answered_count,
        'current_selector': session.current_selector,
    })


def play_award(request, session_pk):
    if request.method != 'POST':
        return redirect('play', session_pk=session_pk)

    session = get_object_or_404(GameSession, pk=session_pk)
    question = get_object_or_404(
        Question,
        pk=request.POST.get('question_pk'),
        category__quiz=session.quiz,
    )

    if not Score.objects.filter(session=session, question=question).exists():
        team_pk = request.POST.get('team_pk') or None
        team = get_object_or_404(session.teams, pk=team_pk) if team_pk else None
        multiplier = 2 if session.points_doubled else 1
        face_value = question.base_points * multiplier          # Face value (for display)
        stolen = Deduction.objects.filter(session=session, question=question).exists()
        awarded = face_value // 2 if stolen else face_value     # actually awarded
        Score.objects.create(
            session=session,
            question=question,
            team=team,
            points=awarded if team else 0,
            effective_points=face_value,
        )
        if team:
            session.current_selector = team
            session.save(update_fields=['current_selector'])

    return redirect('play', session_pk=session_pk)


def play_deduct(request, session_pk):
    if request.method != 'POST':
        return redirect('play', session_pk=session_pk)

    session = get_object_or_404(GameSession, pk=session_pk)
    question = get_object_or_404(
        Question,
        pk=request.POST.get('question_pk'),
        category__quiz=session.quiz,
    )
    team = get_object_or_404(session.teams, pk=request.POST.get('team_pk'))

    if not Score.objects.filter(session=session, question=question).exists():
        multiplier = 2 if session.points_doubled else 1
        stolen = Deduction.objects.filter(session=session, question=question).exists()
        deduct_pts = question.base_points * multiplier // (2 if stolen else 1)
        Deduction.objects.get_or_create(
            session=session,
            question=question,
            team=team,
            defaults={'points': deduct_pts},
        )

    play_url = reverse('play', kwargs={'session_pk': session_pk})
    return redirect(f'{play_url}?question={question.pk}')


def play_reset(request, session_pk):
    if request.method != 'POST':
        return redirect('play', session_pk=session_pk)

    session = get_object_or_404(GameSession, pk=session_pk)
    Score.objects.filter(session=session).delete()
    Deduction.objects.filter(session=session).delete()
    Bonus.objects.filter(session=session).delete()
    session.current_selector = None
    session.points_doubled = False
    session.save(update_fields=['current_selector', 'points_doubled'])
    return redirect('play', session_pk=session_pk)


def play_grant_points(request, session_pk):
    if request.method != 'POST':
        return redirect('play', session_pk=session_pk)

    session = get_object_or_404(GameSession, pk=session_pk)
    team = get_object_or_404(session.teams, pk=request.POST.get('team_pk'))

    try:
        points = int(request.POST.get('points', 0))
    except (TypeError, ValueError):
        points = 0

    if points != 0:
        Bonus.objects.create(session=session, team=team, points=points)

    return redirect('play', session_pk=session_pk)


def play_set_selector(request, session_pk):
    if request.method != 'POST':
        return redirect('play', session_pk=session_pk)

    session = get_object_or_404(GameSession, pk=session_pk)
    team_pk = request.POST.get('team_pk') or None
    session.current_selector = get_object_or_404(session.teams, pk=team_pk) if team_pk else None
    session.save(update_fields=['current_selector'])
    return redirect('play', session_pk=session_pk)


def play_double_points(request, session_pk):
    if request.method != 'POST':
        return redirect('play', session_pk=session_pk)

    session = get_object_or_404(GameSession, pk=session_pk)
    if request.POST.get('reset'):
        session.points_doubled = False
    elif not session.points_doubled:
        session.points_doubled = True
    session.save(update_fields=['points_doubled'])

    return redirect('play', session_pk=session_pk)
