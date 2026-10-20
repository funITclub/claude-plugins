import datetime

from django.contrib.auth.decorators import login_not_required
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.http import Http404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import generic

from . import content
from .forms import IssueFilterForm, IssueForm, ProjectForm
from .models import Issue, Project


# 本番（homepage の中）は既定で全画面がログイン必須で、WG のメンバーには
# ログインのアカウントを配っていない。活動ページは全画面を公開にする
# （各ビューの login_not_required）。公開なので、誰でもチケットを書き換えられる。

SORTABLE = {
    'id': 'pk',
    'tracker': 'tracker',
    'status': 'status_rank',
    'priority': 'priority_rank',
    'subject': 'subject',
    'assignee': 'assignee',
    'due_date': 'due_date',
    'updated_at': 'updated_at',
}

# 期日がこの日数以内のチケットを、トップの「期日が近いチケット」に出す
DUE_SOON_DAYS = 14


def _rank(field, choices):
    """選択肢を定義した順に並べるための番号。値の文字列順では並ばないため。"""
    return Case(
        *[When(**{field: value}, then=Value(i)) for i, value in enumerate(choices.values)],
        output_field=IntegerField(),
    )


class PageMixin:
    """どの画面にも、WG の情報（content.py）とナビの現在地を渡す。"""

    section = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = self.section
        context['wg'] = content.as_dict()
        return context


@method_decorator(login_not_required, name='dispatch')
class HomeView(PageMixin, generic.TemplateView):
    """活動ページのトップ。WG の紹介・構想資料・チケットの様子をまとめて見せる。"""

    template_name = 'WGNAME_activity/home.html'
    section = 'home'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        issues = Issue.objects.select_related('project')
        open_issues = issues.filter(status__in=Issue.OPEN_STATUSES)
        total = issues.count()
        open_count = open_issues.count()
        context.update({
            'today': today,
            'total_count': total,
            'open_count': open_count,
            'closed_count': total - open_count,
            'due_soon': open_issues.filter(
                due_date__isnull=False,
                due_date__lte=today + datetime.timedelta(days=DUE_SOON_DAYS),
            ).order_by('due_date', 'pk')[:10],
            'due_soon_days': DUE_SOON_DAYS,
            'recent_issues': issues.order_by('-updated_at')[:5],
            'projects': Project.objects.annotate(
                open_count=Count('issues', filter=Q(
                    issues__status__in=Issue.OPEN_STATUSES)),
                closed_count=Count('issues', filter=~Q(
                    issues__status__in=Issue.OPEN_STATUSES)),
                total_count=Count('issues'),
            ),
        })
        return context


@method_decorator(login_not_required, name='dispatch')
class SlidesView(PageMixin, generic.TemplateView):
    """構想資料（スライド）。content.SLIDES_TITLE が空のうちは出さない。"""

    template_name = 'WGNAME_activity/slides.html'
    section = 'slides'

    def get(self, request, *args, **kwargs):
        if not content.SLIDES_TITLE:
            raise Http404('構想資料はまだありません')
        return super().get(request, *args, **kwargs)


@method_decorator(login_not_required, name='dispatch')
class IssueListView(PageMixin, generic.ListView):
    """チケット一覧。絞り込みと並べ替えができる。"""

    model = Issue
    template_name = 'WGNAME_activity/issue_list.html'
    context_object_name = 'issues'
    paginate_by = 25
    section = 'issues'

    def get_filter_form(self):
        data = self.request.GET.copy()
        data.setdefault('state', 'open')
        return IssueFilterForm(data)

    def get_queryset(self):
        queryset = Issue.objects.select_related('project').annotate(
            status_rank=_rank('status', Issue.Status),
            priority_rank=_rank('priority', Issue.Priority),
        )
        form = self.get_filter_form()
        if form.is_valid():
            picked = form.cleaned_data
            if picked.get('state') == 'open':
                queryset = queryset.filter(status__in=Issue.OPEN_STATUSES)
            elif picked.get('state') == 'closed':
                queryset = queryset.exclude(status__in=Issue.OPEN_STATUSES)
            for field in ('project', 'tracker', 'status', 'priority'):
                if picked.get(field):
                    queryset = queryset.filter(**{field: picked[field]})
            if picked.get('assignee'):
                queryset = queryset.filter(assignee__icontains=picked['assignee'])
        return queryset.order_by(self.get_ordering(), '-pk')

    def get_ordering(self):
        key = self.request.GET.get('sort', '-updated_at')
        descending = key.startswith('-')
        field = SORTABLE.get(key.lstrip('-'))
        if not field:
            return '-updated_at'
        return ('-' if descending else '') + field

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.get_filter_form()
        context['sort'] = self.request.GET.get('sort', '-updated_at')
        query = self.request.GET.copy()
        query.pop('page', None)
        query.pop('sort', None)
        context['query_string'] = query.urlencode()
        return context


@method_decorator(login_not_required, name='dispatch')
class IssueDetailView(PageMixin, generic.DetailView):
    model = Issue
    template_name = 'WGNAME_activity/issue_detail.html'
    context_object_name = 'issue'
    section = 'issues'


@method_decorator(login_not_required, name='dispatch')
class IssueCreateView(PageMixin, generic.CreateView):
    model = Issue
    form_class = IssueForm
    template_name = 'WGNAME_activity/issue_form.html'
    section = 'issues'

    def get_initial(self):
        initial = super().get_initial()
        identifier = self.request.GET.get('project')
        if identifier:
            initial['project'] = Project.objects.filter(
                identifier=identifier).first()
        return initial


@method_decorator(login_not_required, name='dispatch')
class IssueUpdateView(PageMixin, generic.UpdateView):
    model = Issue
    form_class = IssueForm
    template_name = 'WGNAME_activity/issue_form.html'
    section = 'issues'


@method_decorator(login_not_required, name='dispatch')
class IssueDeleteView(PageMixin, generic.DeleteView):
    model = Issue
    template_name = 'WGNAME_activity/issue_confirm_delete.html'
    context_object_name = 'issue'
    section = 'issues'
    success_url = reverse_lazy('WGNAME_activity:issue_list')


@method_decorator(login_not_required, name='dispatch')
class ProjectListView(PageMixin, generic.ListView):
    model = Project
    template_name = 'WGNAME_activity/project_list.html'
    context_object_name = 'projects'
    section = 'projects'

    def get_queryset(self):
        return Project.objects.annotate(
            open_count=Count('issues', filter=Q(
                issues__status__in=Issue.OPEN_STATUSES)),
            total_count=Count('issues'),
        )


@method_decorator(login_not_required, name='dispatch')
class ProjectDetailView(PageMixin, generic.DetailView):
    model = Project
    template_name = 'WGNAME_activity/project_detail.html'
    context_object_name = 'project'
    section = 'projects'
    slug_field = 'identifier'
    slug_url_kwarg = 'identifier'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        issues = self.object.issues.all()
        context['open_issues'] = issues.filter(status__in=Issue.OPEN_STATUSES)
        context['recent_issues'] = issues[:10]
        context['by_tracker'] = [
            (label, issues.filter(tracker=value).count())
            for value, label in Issue.Tracker.choices
        ]
        return context


@method_decorator(login_not_required, name='dispatch')
class ProjectCreateView(PageMixin, generic.CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'WGNAME_activity/project_form.html'
    section = 'projects'


@method_decorator(login_not_required, name='dispatch')
class ProjectDeleteView(PageMixin, generic.DeleteView):
    model = Project
    template_name = 'WGNAME_activity/project_confirm_delete.html'
    context_object_name = 'project'
    slug_field = 'identifier'
    slug_url_kwarg = 'identifier'
    success_url = reverse_lazy('WGNAME_activity:project_list')
    section = 'projects'


@method_decorator(login_not_required, name='dispatch')
class ProjectUpdateView(PageMixin, generic.UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'WGNAME_activity/project_form.html'
    section = 'projects'
    slug_field = 'identifier'
    slug_url_kwarg = 'identifier'
