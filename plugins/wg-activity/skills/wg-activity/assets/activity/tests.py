import datetime
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.views import View

from . import content
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
        response = self.client.get(reverse('WGNAME_activity:issue_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'WGNAME_activity/issue_list.html')

    def test_open_issues_only_by_default(self):
        response = self.client.get(reverse('WGNAME_activity:issue_list'))
        self.assertContains(response, 'ログイン画面を作る')
        self.assertNotContains(response, '古いリンクを直す')

    def test_closed_state_shows_closed_issues(self):
        response = self.client.get(reverse('WGNAME_activity:issue_list'), {'state': 'closed'})
        self.assertContains(response, '古いリンクを直す')
        self.assertNotContains(response, 'ログイン画面を作る')

    def test_all_state_shows_everything(self):
        response = self.client.get(reverse('WGNAME_activity:issue_list'), {'state': 'all'})
        self.assertContains(response, 'ログイン画面を作る')
        self.assertContains(response, '古いリンクを直す')

    def test_filter_by_project(self):
        response = self.client.get(
            reverse('WGNAME_activity:issue_list'),
            {'state': 'all', 'project': self.other.pk},
        )
        self.assertContains(response, '古いリンクを直す')
        self.assertNotContains(response, 'ログイン画面を作る')

    def test_filter_by_assignee_is_partial(self):
        response = self.client.get(
            reverse('WGNAME_activity:issue_list'), {'state': 'all', 'assignee': 'tana'})
        self.assertContains(response, 'ログイン画面を作る')
        self.assertNotContains(response, '古いリンクを直す')

    def test_sorting_by_subject(self):
        response = self.client.get(
            reverse('WGNAME_activity:issue_list'), {'state': 'all', 'sort': 'subject'})
        subjects = [issue.subject for issue in response.context['issues']]
        self.assertEqual(subjects, sorted(subjects))

    def test_sorting_by_priority_follows_the_choices(self):
        """優先度は文字列の順ではなく、低め→通常→高め→急いでの順に並ぶ。"""
        for priority in (Issue.Priority.URGENT, Issue.Priority.LOW):
            Issue.objects.create(project=self.project, subject=priority.label,
                                 priority=priority, assignee='sato')
        response = self.client.get(
            reverse('WGNAME_activity:issue_list'), {'state': 'all', 'sort': 'priority'})
        order = [issue.priority for issue in response.context['issues']]
        self.assertEqual(order, sorted(order, key=list(Issue.Priority.values).index))
        response = self.client.get(
            reverse('WGNAME_activity:issue_list'), {'state': 'all', 'sort': '-priority'})
        self.assertEqual(response.context['issues'][0].priority, Issue.Priority.URGENT)

    def test_sorting_by_status_follows_the_choices(self):
        response = self.client.get(
            reverse('WGNAME_activity:issue_list'), {'state': 'all', 'sort': 'status'})
        order = [issue.status for issue in response.context['issues']]
        self.assertEqual(order, sorted(order, key=list(Issue.Status.values).index))

    def test_unknown_sort_key_falls_back(self):
        response = self.client.get(
            reverse('WGNAME_activity:issue_list'), {'sort': 'drop table'})
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
        response = self.client.post(reverse('WGNAME_activity:issue_create'), {
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
            reverse('WGNAME_activity:issue_update', args=[self.open_issue.pk]), {
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
        response = self.client.post(reverse('WGNAME_activity:issue_create'), {
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
        response = self.client.post(reverse('WGNAME_activity:issue_create'), {
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
        response = self.client.post(reverse('WGNAME_activity:issue_create'), {
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
        response = self.client.get(reverse('WGNAME_activity:issue_list'), {'state': 'all'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['filter_form'].fields['assignee'].required)

    def test_delete_issue(self):
        response = self.client.post(
            reverse('WGNAME_activity:issue_delete', args=[self.closed_issue.pk]))
        self.assertRedirects(response, reverse('WGNAME_activity:issue_list'))
        self.assertFalse(Issue.objects.filter(pk=self.closed_issue.pk).exists())


class ProjectViewTests(TrackerTestCase):
    def test_project_list_counts_issues(self):
        response = self.client.get(reverse('WGNAME_activity:project_list'))
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
        response = self.client.post(reverse('WGNAME_activity:project_create'), {
            'name': '手順書', 'identifier': 'docs', 'description': '',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Project.objects.filter(identifier='docs').exists())


class ProjectDeleteTests(TrackerTestCase):
    def test_confirm_page_warns_about_the_issues(self):
        response = self.client.get(
            reverse('WGNAME_activity:project_delete', args=[self.project.identifier]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'まとめて削除されます')
        self.assertContains(response, self.open_issue.subject)

    def test_delete_project_takes_its_issues_with_it(self):
        response = self.client.post(
            reverse('WGNAME_activity:project_delete', args=[self.project.identifier]))
        self.assertRedirects(response, reverse('WGNAME_activity:project_list'))
        self.assertFalse(
            Project.objects.filter(identifier=self.project.identifier).exists())
        self.assertFalse(Issue.objects.filter(pk=self.open_issue.pk).exists())
        # 別プロジェクトのチケットは残る
        self.assertTrue(Issue.objects.filter(pk=self.closed_issue.pk).exists())

    def test_empty_project_says_so(self):
        empty = Project.objects.create(name='空っぽ', identifier='empty')
        response = self.client.get(
            reverse('WGNAME_activity:project_delete', args=[empty.identifier]))
        self.assertContains(response, 'チケットはありません')


class ListOperationLinkTests(TrackerTestCase):
    """一覧からそのまま編集・削除へ行ける。"""

    def test_issue_list_has_edit_and_delete_links(self):
        html = self.client.get(reverse('WGNAME_activity:issue_list')).content.decode()
        self.assertIn(reverse('WGNAME_activity:issue_update', args=[self.open_issue.pk]), html)
        self.assertIn(reverse('WGNAME_activity:issue_delete', args=[self.open_issue.pk]), html)

    def test_project_list_has_edit_and_delete_links(self):
        html = self.client.get(reverse('WGNAME_activity:project_list')).content.decode()
        self.assertIn(
            reverse('WGNAME_activity:project_update', args=[self.project.identifier]), html)
        self.assertIn(
            reverse('WGNAME_activity:project_delete', args=[self.project.identifier]), html)

    def test_project_detail_has_edit_and_delete_links(self):
        html = self.client.get(self.project.get_absolute_url()).content.decode()
        self.assertIn(
            reverse('WGNAME_activity:project_update', args=[self.project.identifier]), html)
        self.assertIn(
            reverse('WGNAME_activity:project_delete', args=[self.project.identifier]), html)

    def test_issue_detail_has_edit_and_delete_links(self):
        html = self.client.get(self.open_issue.get_absolute_url()).content.decode()
        self.assertIn(reverse('WGNAME_activity:issue_update', args=[self.open_issue.pk]), html)
        self.assertIn(reverse('WGNAME_activity:issue_delete', args=[self.open_issue.pk]), html)


class PublicAccessTests(TestCase):
    """本番は既定で全画面ログイン必須なので、すべてのビューを明示的に外してある。"""

    def test_every_view_is_public(self):
        from WGNAME_activity import views
        found = [
            obj for obj in vars(views).values()
            if isinstance(obj, type) and issubclass(obj, View)
            and obj.__module__ == views.__name__
        ]
        self.assertGreaterEqual(len(found), 12)
        for view in found:
            self.assertIs(
                view.dispatch.login_required, False,
                '{} に login_not_required が付いていない'.format(view.__name__))


class HomeTests(TrackerTestCase):
    """活動ページのトップ。"""

    def get(self):
        return self.client.get(reverse('WGNAME_activity:home'))

    def test_home_is_the_root_of_the_app(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'WGNAME_activity/home.html')

    def test_shows_the_wg_from_content(self):
        response = self.get()
        self.assertContains(response, escape(content.NAME))
        self.assertContains(response, escape(content.CODE))
        self.assertContains(response, escape(content.LEAD))

    def test_intro_is_split_into_paragraphs(self):
        with mock.patch.object(content, 'INTRO', '一段落目。\n\n二段落目。'):
            response = self.get()
        self.assertContains(response, '<p>一段落目。</p>', html=True)
        self.assertContains(response, '<p>二段落目。</p>', html=True)

    def test_counts_the_tickets(self):
        response = self.get()
        self.assertEqual(response.context['open_count'], 1)
        self.assertEqual(response.context['closed_count'], 1)
        self.assertEqual(response.context['total_count'], 2)

    def test_links_to_the_tracker(self):
        response = self.get()
        self.assertContains(response, reverse('WGNAME_activity:issue_list'))
        self.assertContains(response, reverse('WGNAME_activity:issue_create'))

    def test_due_soon_lists_open_issues_by_due_date(self):
        today = timezone.localdate()
        overdue = Issue.objects.create(
            project=self.project, subject='期日を過ぎたもの', assignee='sato',
            due_date=today - datetime.timedelta(days=1))
        soon = Issue.objects.create(
            project=self.project, subject='来週が期日', assignee='sato',
            due_date=today + datetime.timedelta(days=7))
        Issue.objects.create(
            project=self.project, subject='まだ先', assignee='sato',
            due_date=today + datetime.timedelta(days=60))
        Issue.objects.create(
            project=self.project, subject='終わったもの', assignee='sato',
            status=Issue.Status.CLOSED, due_date=today)
        response = self.get()
        self.assertEqual(list(response.context['due_soon']), [overdue, soon])
        self.assertContains(response, '（過ぎています）', count=1)

    def test_recent_issues_are_newest_first(self):
        response = self.get()
        recent = list(response.context['recent_issues'])
        self.assertEqual(recent, sorted(recent, key=lambda i: i.updated_at, reverse=True))

    def test_project_progress(self):
        response = self.get()
        projects = {p.identifier: p for p in response.context['projects']}
        self.assertEqual(projects['sample'].open_count, 1)
        self.assertEqual(projects['tools'].closed_count, 1)
        self.assertContains(response, '100%')

    def test_empty_tracker_still_shows(self):
        Issue.objects.all().delete()
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'チケットがまだありません')

    def test_join_link(self):
        self.assertContains(self.get(), 'href="{}"'.format(content.JOIN_URL))

    def test_links_from_content(self):
        with mock.patch.object(content, 'LINKS', [('Webアプリ', 'https://example.com/app/')]):
            response = self.get()
        self.assertContains(response, '関連リンク')
        self.assertContains(response, 'href="https://example.com/app/"')

    def test_every_page_carries_the_wg_name(self):
        response = self.client.get(reverse('WGNAME_activity:issue_list'))
        self.assertContains(response, '<title>チケット | {}</title>'.format(content.NAME), html=True)
        self.assertContains(response, reverse('WGNAME_activity:home'))


class SlidesTests(TestCase):
    """構想資料。content.SLIDES_TITLE が空のうちは出さない。"""

    def test_hidden_until_titled(self):
        with mock.patch.object(content, 'SLIDES_TITLE', None):
            self.assertEqual(
                self.client.get(reverse('WGNAME_activity:slides')).status_code, 404)
            home = self.client.get(reverse('WGNAME_activity:home'))
        self.assertNotContains(home, reverse('WGNAME_activity:slides'))

    def test_shown_and_linked_once_titled(self):
        with mock.patch.object(content, 'SLIDES_TITLE', '構想の資料'):
            response = self.client.get(reverse('WGNAME_activity:slides'))
            home = self.client.get(reverse('WGNAME_activity:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'WGNAME_activity/slides.html')
        self.assertContains(home, reverse('WGNAME_activity:slides'))
        self.assertContains(home, '構想の資料')

    def test_slides_have_navigation_and_a_way_back(self):
        with mock.patch.object(content, 'SLIDES_TITLE', '構想の資料'):
            response = self.client.get(reverse('WGNAME_activity:slides'))
        for marker in ('id="prev"', 'id="next"', 'id="counter"', 'id="dots"', 'name="viewport"'):
            self.assertContains(response, marker)
        self.assertContains(
            response, 'href="{}"'.format(reverse('WGNAME_activity:home')))
