from django.urls import path
from .views import *

urlpatterns = [
    path("employees/", EmployeeListView.as_view(), name="employee_list"),
    path(
        "employees/<int:employee_id>/",
        employee_detail,
        name="employee_detail",
    ),
    path(
        "employees/<int:employee_id>/add_salary_structure/",
        add_salary_structure,
        name="add_salary_structure",
    ),
    path(
        "employees/<int:employee_id>/old_salary_structures/",
        old_salary_structures,
        name="old_salary_structures",
    ),
]
