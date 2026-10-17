from django.db import models
from django.urls import reverse


class Project(models.Model):
    """チケットを束ねる単位。"""

    name = models.CharField('プロジェクト名', max_length=100)
    identifier = models.SlugField('識別子', max_length=50, unique=True)
    description = models.TextField('説明', blank=True)
    created_at = models.DateTimeField('登録日', auto_now_add=True)

    class Meta:
        verbose_name = 'プロジェクト'
        verbose_name_plural = 'プロジェクト'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tracker:project_detail', args=[self.identifier])

    @property
    def open_issue_count(self):
        return self.issues.filter(status__in=Issue.OPEN_STATUSES).count()

    @property
    def closed_issue_count(self):
        return self.issues.exclude(status__in=Issue.OPEN_STATUSES).count()


class Issue(models.Model):
    """チケット。"""

    class Tracker(models.TextChoices):
        BUG = 'bug', 'バグ'
        FEATURE = 'feature', '機能'
        SUPPORT = 'support', 'サポート'

    class Status(models.TextChoices):
        NEW = 'new', '新規'
        IN_PROGRESS = 'in_progress', '進行中'
        RESOLVED = 'resolved', '解決'
        FEEDBACK = 'feedback', 'フィードバック'
        CLOSED = 'closed', '終了'
        REJECTED = 'rejected', '却下'

    class Priority(models.TextChoices):
        LOW = 'low', '低め'
        NORMAL = 'normal', '通常'
        HIGH = 'high', '高め'
        URGENT = 'urgent', '急いで'

    OPEN_STATUSES = [Status.NEW, Status.IN_PROGRESS, Status.FEEDBACK]

    project = models.ForeignKey(
        Project, verbose_name='プロジェクト',
        on_delete=models.CASCADE, related_name='issues',
    )
    tracker = models.CharField(
        'トラッカー', max_length=20, choices=Tracker.choices, default=Tracker.FEATURE,
    )
    subject = models.CharField('題名', max_length=200)
    description = models.TextField('説明', blank=True)
    status = models.CharField(
        'ステータス', max_length=20, choices=Status.choices, default=Status.NEW,
    )
    priority = models.CharField(
        '優先度', max_length=20, choices=Priority.choices, default=Priority.NORMAL,
    )
    assignee = models.CharField('担当者', max_length=50)
    start_date = models.DateField('開始日', null=True, blank=True)
    due_date = models.DateField('期日', null=True, blank=True)
    done_ratio = models.PositiveSmallIntegerField('進捗率', default=0)
    created_at = models.DateTimeField('登録日', auto_now_add=True)
    updated_at = models.DateTimeField('更新日', auto_now=True)

    class Meta:
        verbose_name = 'チケット'
        verbose_name_plural = 'チケット'
        ordering = ['-updated_at']

    def __str__(self):
        return '#{} {}'.format(self.pk, self.subject)

    def get_absolute_url(self):
        return reverse('tracker:issue_detail', args=[self.pk])

    @property
    def is_open(self):
        return self.status in self.OPEN_STATUSES
