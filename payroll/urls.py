from django.urls import path
from .views import (
    EmployeeListView,
    EmployeeDetailView,
    MonthlySalaryDetailView,
    generate_monthly_salary,
)

urlpatterns = [
    path("employees/", EmployeeListView.as_view(), name="employee_list"),
    path("employees/<int:pk>/", EmployeeDetailView.as_view(), name="employee_detail"),
    path(
        "monthly-salary/<int:pk>/",
        MonthlySalaryDetailView.as_view(),
        name="monthly_salary_detail",
    ),
    path(
        "employees/<int:employee_id>/generate-salary/",
        generate_monthly_salary,
        name="generate_monthly_salary",
    ),
]
