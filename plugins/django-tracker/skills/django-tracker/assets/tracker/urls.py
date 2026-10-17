from django.urls import path

from . import views

app_name = 'tracker'

urlpatterns = [
    path('issues/', views.IssueListView.as_view(), name='issue_list'),
    path('issues/new/', views.IssueCreateView.as_view(), name='issue_create'),
    path('issues/<int:pk>/', views.IssueDetailView.as_view(), name='issue_detail'),
    path('issues/<int:pk>/edit/', views.IssueUpdateView.as_view(), name='issue_update'),
    path('issues/<int:pk>/delete/', views.IssueDeleteView.as_view(), name='issue_delete'),
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/new/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<slug:identifier>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projects/<slug:identifier>/edit/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('projects/<slug:identifier>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
]
