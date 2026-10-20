from django.urls import path

from . import views

app_name = 'WGNAME_activity'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('slides/', views.SlidesView.as_view(), name='slides'),
    path('tracker/issues/', views.IssueListView.as_view(), name='issue_list'),
    path('tracker/issues/new/', views.IssueCreateView.as_view(), name='issue_create'),
    path('tracker/issues/<int:pk>/', views.IssueDetailView.as_view(), name='issue_detail'),
    path('tracker/issues/<int:pk>/edit/', views.IssueUpdateView.as_view(), name='issue_update'),
    path('tracker/issues/<int:pk>/delete/', views.IssueDeleteView.as_view(), name='issue_delete'),
    path('tracker/projects/', views.ProjectListView.as_view(), name='project_list'),
    path('tracker/projects/new/', views.ProjectCreateView.as_view(), name='project_create'),
    path('tracker/projects/<slug:identifier>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('tracker/projects/<slug:identifier>/edit/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('tracker/projects/<slug:identifier>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
]
