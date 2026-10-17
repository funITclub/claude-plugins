from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views import generic

from .forms import IssueFilterForm, IssueForm, ProjectForm
from .models import Issue, Project


SORTABLE = {
    'id': 'pk',
    'tracker': 'tracker',
    'status': 'status',
    'priority': 'priority',
    'subject': 'subject',
    'assignee': 'assignee',
    'due_date': 'due_date',
    'updated_at': 'updated_at',
}


class IssueListView(generic.ListView):
    """チケット一覧。絞り込みと並べ替えができる。"""

    model = Issue
    template_name = 'tracker/issue_list.html'
    context_object_name = 'issues'
    paginate_by = 25
    extra_context = {'section': 'issues'}

    def get_filter_form(self):
        data = self.request.GET.copy()
        data.setdefault('state', 'open')
        return IssueFilterForm(data)

    def get_queryset(self):
        queryset = Issue.objects.select_related('project')
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
        return queryset.order_by(self.get_ordering())

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


class IssueDetailView(generic.DetailView):
    model = Issue
    template_name = 'tracker/issue_detail.html'
    context_object_name = 'issue'
    extra_context = {'section': 'issues'}


class IssueCreateView(generic.CreateView):
    model = Issue
    form_class = IssueForm
    template_name = 'tracker/issue_form.html'
    extra_context = {'section': 'issues'}

    def get_initial(self):
        initial = super().get_initial()
        identifier = self.request.GET.get('project')
        if identifier:
            initial['project'] = Project.objects.filter(
                identifier=identifier).first()
        return initial


class IssueUpdateView(generic.UpdateView):
    model = Issue
    form_class = IssueForm
    template_name = 'tracker/issue_form.html'
    extra_context = {'section': 'issues'}


class IssueDeleteView(generic.DeleteView):
    model = Issue
    template_name = 'tracker/issue_confirm_delete.html'
    context_object_name = 'issue'
    extra_context = {'section': 'issues'}
    success_url = reverse_lazy('tracker:issue_list')


class ProjectListView(generic.ListView):
    model = Project
    template_name = 'tracker/project_list.html'
    context_object_name = 'projects'
    extra_context = {'section': 'projects'}

    def get_queryset(self):
        return Project.objects.annotate(
            open_count=Count('issues', filter=Q(
                issues__status__in=Issue.OPEN_STATUSES)),
            total_count=Count('issues'),
        )


class ProjectDetailView(generic.DetailView):
    model = Project
    template_name = 'tracker/project_detail.html'
    context_object_name = 'project'
    extra_context = {'section': 'projects'}
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


class ProjectCreateView(generic.CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'tracker/project_form.html'
    extra_context = {'section': 'projects'}


class ProjectDeleteView(generic.DeleteView):
    model = Project
    template_name = 'tracker/project_confirm_delete.html'
    context_object_name = 'project'
    slug_field = 'identifier'
    slug_url_kwarg = 'identifier'
    success_url = reverse_lazy('tracker:project_list')
    extra_context = {'section': 'projects'}


class ProjectUpdateView(generic.UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'tracker/project_form.html'
    extra_context = {'section': 'projects'}
    slug_field = 'identifier'
    slug_url_kwarg = 'identifier'
