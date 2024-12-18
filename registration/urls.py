from django.urls import path
from . import views
from .views import GerenteTicketListView, UserListView, ReportDetailView, ReportListView, ReportCreateView, ReportDetailView

urlpatterns = [
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('logout_time/', views.logout_time, name='logout_time'),
    path('gerente/users/', UserListView.as_view(), name='user_list'),
    path('gerente/users/create/', views.create_user, name='create_user'),
    path('gerente/users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('gerente/users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('gerente/tickets_list', GerenteTicketListView.as_view(), name='gerente_ticket_list'),
    path('gerente/report_list', ReportListView.as_view(), name='reports_list'),
    path('gerente/report_create', ReportCreateView.as_view(), name='reports_create'),
    path('gerente/report_detail/<int:pk>', ReportDetailView.as_view(), name='reports_detail')
]