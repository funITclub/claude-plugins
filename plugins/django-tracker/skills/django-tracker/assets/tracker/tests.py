from django.test import TestCase
from django.urls import reverse

from .models import Issue, Project


class TrackerTestCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name='サンプルサイト', identifier='sample')
        self.other = Project.objects.create(
            name='社内ツール', identifier='tools')
        self.open_issue = Issue.objects.create(
            project=self.project, subject='ログイン画面を作る',
            tracker=Issue.Tracker.FEATURE, status=Issue.Status.IN_PROGRESS,
            priority=Issue.Priority.HIGH, assignee='tanaka', done_ratio=40,
        )
        self.closed_issue = Issue.objects.create(
            project=self.other, subject='古いリンクを直す',
            tracker=Issue.Tracker.SUPPORT, status=Issue.Status.CLOSED,
            assignee='yamada',
        )


class IssueListTests(TrackerTestCase):
    def test_list_is_shown(self):
        response = self.client.get(reverse('tracker:issue_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/issue_list.html')

    def test_open_issues_only_by_default(self):
        response = self.client.get(reverse('tracker:issue_list'))
        self.assertContains(response, 'ログイン画面を作る')
        self.assertNotContains(response, '古いリンクを直す')

    def test_closed_state_shows_closed_issues(self):
        response = self.client.get(reverse('tracker:issue_list'), {'state': 'closed'})
        self.assertContains(response, '古いリンクを直す')
        self.assertNotContains(response, 'ログイン画面を作る')

    def test_all_state_shows_everything(self):
        response = self.client.get(reverse('tracker:issue_list'), {'state': 'all'})
        self.assertContains(response, 'ログイン画面を作る')
        self.assertContains(response, '古いリンクを直す')

    def test_filter_by_project(self):
        response = self.client.get(
            reverse('tracker:issue_list'),
            {'state': 'all', 'project': self.other.pk},
        )
        self.assertContains(response, '古いリンクを直す')
        self.assertNotContains(response, 'ログイン画面を作る')

    def test_filter_by_assignee_is_partial(self):
        response = self.client.get(
            reverse('tracker:issue_list'), {'state': 'all', 'assignee': 'tana'})
        self.assertContains(response, 'ログイン画面を作る')
        self.assertNotContains(response, '古いリンクを直す')

    def test_sorting_by_subject(self):
        response = self.client.get(
            reverse('tracker:issue_list'), {'state': 'all', 'sort': 'subject'})
        subjects = [issue.subject for issue in response.context['issues']]
        self.assertEqual(subjects, sorted(subjects))

    def test_unknown_sort_key_falls_back(self):
        response = self.client.get(
            reverse('tracker:issue_list'), {'sort': 'drop table'})
        self.assertEqual(response.status_code, 200)


class IssueDetailTests(TrackerTestCase):
    def test_detail_is_shown(self):
        response = self.client.get(self.open_issue.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ログイン画面を作る')
        self.assertContains(response, '進行中')
        self.assertContains(response, 'tanaka')


class IssueEditingTests(TrackerTestCase):
    def test_create_issue(self):
        response = self.client.post(reverse('tracker:issue_create'), {
            'project': self.project.pk,
            'tracker': Issue.Tracker.BUG,
            'subject': '一覧の並び順がおかしい',
            'description': '日付の新しい順にならない。',
            'status': Issue.Status.NEW,
            'priority': Issue.Priority.URGENT,
            'assignee': 'yamada',
            'done_ratio': 0,
        })
        self.assertEqual(response.status_code, 302)
        issue = Issue.objects.get(subject='一覧の並び順がおかしい')
        self.assertEqual(issue.project, self.project)

    def test_update_issue(self):
        response = self.client.post(
            reverse('tracker:issue_update', args=[self.open_issue.pk]), {
                'project': self.project.pk,
                'tracker': self.open_issue.tracker,
                'subject': self.open_issue.subject,
                'description': '',
                'status': Issue.Status.RESOLVED,
                'priority': self.open_issue.priority,
                'assignee': 'tanaka',
                'done_ratio': 100,
            })
        self.assertEqual(response.status_code, 302)
        self.open_issue.refresh_from_db()
        self.assertEqual(self.open_issue.status, Issue.Status.RESOLVED)
        self.assertFalse(self.open_issue.is_open)

    def test_due_date_before_start_date_is_rejected(self):
        response = self.client.post(reverse('tracker:issue_create'), {
            'project': self.project.pk,
            'tracker': Issue.Tracker.FEATURE,
            'subject': '順番のおかしい日付',
            'description': '',
            'status': Issue.Status.NEW,
            'priority': Issue.Priority.NORMAL,
            'assignee': 'yamada',
            'start_date': '2026-10-20',
            'due_date': '2026-10-10',
            'done_ratio': 0,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'], 'due_date', '期日は開始日より後にしてください。')

    def test_assignee_is_required(self):
        response = self.client.post(reverse('tracker:issue_create'), {
            'project': self.project.pk,
            'tracker': Issue.Tracker.FEATURE,
            'subject': '担当者のないチケット',
            'description': '',
            'status': Issue.Status.NEW,
            'priority': Issue.Priority.NORMAL,
            'assignee': '',
            'done_ratio': 0,
        })
        self.assertEqual(response.status_code, 200)
        # 文言は LANGUAGE_CODE で変わるので、エラーが付いたことだけを見る
        self.assertIn('assignee', response.context['form'].errors)
        self.assertFalse(Issue.objects.filter(subject='担当者のないチケット').exists())

    def test_assignee_is_free_text(self):
        """選択式ではなく、好きな文字列を入れられる。"""
        response = self.client.post(reverse('tracker:issue_create'), {
            'project': self.project.pk,
            'tracker': Issue.Tracker.FEATURE,
            'subject': '自由入力の担当者',
            'description': '',
            'status': Issue.Status.NEW,
            'priority': Issue.Priority.NORMAL,
            'assignee': '生成チーム（当番制）',
            'done_ratio': 0,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Issue.objects.get(subject='自由入力の担当者').assignee, '生成チーム（当番制）')

    def test_filtering_by_assignee_stays_optional(self):
        """一覧の絞り込みでは担当者は任意。"""
        response = self.client.get(reverse('tracker:issue_list'), {'state': 'all'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['filter_form'].fields['assignee'].required)

    def test_delete_issue(self):
        response = self.client.post(
            reverse('tracker:issue_delete', args=[self.closed_issue.pk]))
        self.assertRedirects(response, reverse('tracker:issue_list'))
        self.assertFalse(Issue.objects.filter(pk=self.closed_issue.pk).exists())


class ProjectViewTests(TrackerTestCase):
    def test_project_list_counts_issues(self):
        response = self.client.get(reverse('tracker:project_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'サンプルサイト')
        projects = {p.identifier: p for p in response.context['projects']}
        self.assertEqual(projects['sample'].open_count, 1)
        self.assertEqual(projects['tools'].open_count, 0)
        self.assertEqual(projects['tools'].total_count, 1)

    def test_project_detail_lists_its_issues(self):
        response = self.client.get(self.project.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ログイン画面を作る')
        self.assertNotContains(response, '古いリンクを直す')

    def test_create_project(self):
        response = self.client.post(reverse('tracker:project_create'), {
            'name': '手順書', 'identifier': 'docs', 'description': '',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Project.objects.filter(identifier='docs').exists())


class ProjectDeleteTests(TrackerTestCase):
    def test_confirm_page_warns_about_the_issues(self):
        response = self.client.get(
            reverse('tracker:project_delete', args=[self.project.identifier]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'まとめて削除されます')
        self.assertContains(response, self.open_issue.subject)

    def test_delete_project_takes_its_issues_with_it(self):
        response = self.client.post(
            reverse('tracker:project_delete', args=[self.project.identifier]))
        self.assertRedirects(response, reverse('tracker:project_list'))
        self.assertFalse(
            Project.objects.filter(identifier=self.project.identifier).exists())
        self.assertFalse(Issue.objects.filter(pk=self.open_issue.pk).exists())
        # 別プロジェクトのチケットは残る
        self.assertTrue(Issue.objects.filter(pk=self.closed_issue.pk).exists())

    def test_empty_project_says_so(self):
        empty = Project.objects.create(name='空っぽ', identifier='empty')
        response = self.client.get(
            reverse('tracker:project_delete', args=[empty.identifier]))
        self.assertContains(response, 'チケットはありません')


class ListOperationLinkTests(TrackerTestCase):
    """一覧からそのまま編集・削除へ行ける。"""

    def test_issue_list_has_edit_and_delete_links(self):
        html = self.client.get(reverse('tracker:issue_list')).content.decode()
        self.assertIn(reverse('tracker:issue_update', args=[self.open_issue.pk]), html)
        self.assertIn(reverse('tracker:issue_delete', args=[self.open_issue.pk]), html)

    def test_project_list_has_edit_and_delete_links(self):
        html = self.client.get(reverse('tracker:project_list')).content.decode()
        self.assertIn(
            reverse('tracker:project_update', args=[self.project.identifier]), html)
        self.assertIn(
            reverse('tracker:project_delete', args=[self.project.identifier]), html)

    def test_project_detail_has_edit_and_delete_links(self):
        html = self.client.get(self.project.get_absolute_url()).content.decode()
        self.assertIn(
            reverse('tracker:project_update', args=[self.project.identifier]), html)
        self.assertIn(
            reverse('tracker:project_delete', args=[self.project.identifier]), html)

    def test_issue_detail_has_edit_and_delete_links(self):
        html = self.client.get(self.open_issue.get_absolute_url()).content.decode()
        self.assertIn(reverse('tracker:issue_update', args=[self.open_issue.pk]), html)
        self.assertIn(reverse('tracker:issue_delete', args=[self.open_issue.pk]), html)
