from django.views.generic import ListView, DetailView
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from decimal import Decimal

from .models import Employee, MonthlySalary, MonthlySalaryLine, SalaryComponent


class EmployeeListView(ListView):
    model = Employee
    template_name = "payroll/employee_list.html"
    context_object_name = "employees"


class EmployeeDetailView(DetailView):
    model = Employee
    template_name = "payroll/employee_detail.html"
    context_object_name = "employee"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["salary_structures"] = self.object.salary_structures.all()
        context["monthly_salaries"] = self.object.monthly_salaries.all()
        return context


class MonthlySalaryDetailView(DetailView):
    model = MonthlySalary
    template_name = "payroll/monthly_salary_detail.html"
    context_object_name = "monthly_salary"


def generate_monthly_salary(request, employee_id):
    """
    Generates the monthly salary record for a given employee.
    Only the month and year are provided by the user.
    The salary is calculated using the employee's current salary structure.
    Assumes that the basic salary is stored in a SalaryStructureLine
    with a SalaryComponent code "BASIC".
    """
    employee = get_object_or_404(Employee, pk=employee_id)
    error = None

    if request.method == "POST":
        try:
            month = int(request.POST.get("month"))
            year = int(request.POST.get("year"))
        except (TypeError, ValueError):
            error = "Invalid input provided."

        # Retrieve the current active salary structure for the employee
        salary_structure = employee.current_salary_structure
        if not salary_structure:
            error = "No active salary structure found for this employee."

        if not error:
            # Assume that the basic salary is stored in a line where the component code is "BASIC"
            basic_line = salary_structure.lines.filter(
                salary_component__name__iexact="basic"
            ).first()
            if basic_line:
                basic_salary = basic_line.amount
            else:
                # If no basic salary is defined, assume 0
                basic_salary = Decimal("0")

            gross = Decimal("0")
            deductions = Decimal("0")

            # Calculate gross and deductions based on each component
            for line in salary_structure.lines.all():
                if line.salary_component.is_percentage:
                    # Percentage-based components are computed as a percentage of basic_salary
                    computed = (basic_salary * line.amount) / Decimal("100")
                else:
                    computed = line.amount

                if line.salary_component.component_type == SalaryComponent.EARNING:
                    gross += computed
                elif line.salary_component.component_type == SalaryComponent.DEDUCTION:
                    deductions += computed

            net = gross - deductions

            # Create the MonthlySalary record
            monthly_salary = MonthlySalary.objects.create(
                employee=employee,
                salary_structure=salary_structure,
                month=month,
                year=year,
                gross_amount=gross,
                net_amount=net,
            )

            # Create the detailed breakdown for each salary component
            for line in salary_structure.lines.all():
                if line.salary_component.is_percentage:
                    computed = (basic_salary * line.amount) / Decimal("100")
                else:
                    computed = line.amount

                MonthlySalaryLine.objects.create(
                    monthly_salary=monthly_salary,
                    salary_component=line.salary_component,
                    amount=computed,
                )

            return redirect("monthly_salary_detail", pk=monthly_salary.pk)
    else:
        month = timezone.now().month
        year = timezone.now().year

    context = {
        "employee": employee,
        "error": error,
        "current_year": year,
        "current_month": month,
    }
    return render(request, "payroll/generate_monthly_salary.html", context)
