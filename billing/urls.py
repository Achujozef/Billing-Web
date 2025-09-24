from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("generate-bill/", views.generate_bill, name="generate_bill"),


    path("poojas/", views.pooja_list, name="pooja_list"),
    path("poojas/save/", views.save_pooja, name="save_pooja"),  # Add/Edit via AJAX
    path("poojas/delete/<int:pk>/", views.delete_pooja, name="delete_pooja"),

    path("subscriptions/", views.subscription_list, name="subscription_list"),
    path("subscriptions/toggle/", views.toggle_subscription, name="toggle_subscription"),
    path("subscriptions/save/", views.subscription_save, name="subscription_save"),  # for AJAX save
    path('subscriptions/delete/', views.delete_subscription, name='delete_subscription'),
    path('subscriptions/bill/<int:subscription_id>/', views.view_subscription_bill, name='view_subscription_bill'),
    path('subscription/<int:subscription_id>/history/', views.subscription_history, name='subscription_history'),
    path('subscription/mark_cycle_done/', views.mark_cycle_done, name='mark_cycle_done'),


    path("report/", views.report_view, name="report_view"),

    path("api/transliterate/", views.transliterate, name="transliterate"),
    
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),



# ---------------- Festival Billing ----------------
    path("festival/", views.festival_dashboard, name="festival_dashboard"),

    # Event CRUD
    path("festival/event/add/", views.add_event, name="add_event"),
    path("festival/event/<int:pk>/edit/", views.edit_event, name="edit_event"),
    path("festival/event/<int:pk>/delete/", views.delete_event, name="delete_event"),

    # Festival Pooja CRUD
    path("festival/pooja/add/", views.add_festival_pooja, name="add_festival_pooja"),
    path("festival/pooja/<int:pk>/edit/", views.edit_festival_pooja, name="edit_festival_pooja"),
    path("festival/pooja/<int:pk>/delete/", views.delete_festival_pooja, name="delete_festival_pooja"),

    # Festival Bill
    path("festival/bill/create/", views.create_festival_bill, name="create_festival_bill"),
    path("festival/bill/<int:bill_id>/print/", views.print_festival_bill, name="print_festival_bill"),

    path("bill/<int:bill_id>/toggle-payment/", views.toggle_payment_status, name="toggle_payment_status"),

]
