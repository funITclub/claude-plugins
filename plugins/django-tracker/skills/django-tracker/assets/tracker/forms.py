from django import forms

from .models import Issue, Project


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = [
            'project', 'tracker', 'subject', 'description', 'status',
            'priority', 'assignee', 'start_date', 'due_date', 'done_ratio',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 8}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned = super().clean()
        start, due = cleaned.get('start_date'), cleaned.get('due_date')
        if start and due and due < start:
            self.add_error('due_date', '期日は開始日より後にしてください。')
        return cleaned

    def clean_done_ratio(self):
        ratio = self.cleaned_data['done_ratio']
        if ratio > 100:
            raise forms.ValidationError('進捗率は 0〜100 で入れてください。')
        return ratio


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'identifier', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 5})}


class IssueFilterForm(forms.Form):
    """一覧の絞り込み。すべて任意。"""

    OPEN_CHOICES = [('open', '未完了'), ('closed', '完了'), ('all', 'すべて')]

    state = forms.ChoiceField(label='状態', choices=OPEN_CHOICES, required=False)
    project = forms.ModelChoiceField(
        label='プロジェクト', queryset=Project.objects.all(),
        required=False, empty_label='（すべて）',
    )
    tracker = forms.ChoiceField(
        label='トラッカー', choices=[('', '（すべて）')] + Issue.Tracker.choices,
        required=False,
    )
    status = forms.ChoiceField(
        label='ステータス', choices=[('', '（すべて）')] + Issue.Status.choices,
        required=False,
    )
    priority = forms.ChoiceField(
        label='優先度', choices=[('', '（すべて）')] + Issue.Priority.choices,
        required=False,
    )
    assignee = forms.CharField(label='担当者', max_length=50, required=False)
