from django.urls import path

from . import views

app_name = 'WGNAME_activity'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('slides/', views.SlidesView.as_view(), name='slides'),
    path('tracker/issues/', views.IssueListView.as_view(), name='issue_list'),
    path('tracker/issues/<int:number>/', views.IssueDetailView.as_view(), name='issue_detail'),
    path('tracker/projects/', views.ProjectListView.as_view(), name='project_list'),
    path('tracker/projects/<str:group_id>/', views.ProjectDetailView.as_view(), name='project_detail'),
]
