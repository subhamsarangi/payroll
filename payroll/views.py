from datetime import datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView

from .models import Employee, SalaryStructure, SalaryStructureLine, SalaryComponent


class EmployeeListView(ListView):
    model = Employee
    template_name = "payroll/employee_list.html"
    context_object_name = "employees"


def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    active_salary_structure = employee.salary_structures.filter(is_active=True).first()
    old_salary_structures = employee.salary_structures.filter(is_active=False)
    gross_salary = None
    net_salary = None
    if active_salary_structure:
        gross_salary = active_salary_structure.gross_salary()
        net_salary = active_salary_structure.net_salary()
    return render(
        request,
        "payroll/employee_detail.html",
        {
            "employee": employee,
            "active_salary_structure": active_salary_structure,
            "old_salary_structures": old_salary_structures,
            "gross_salary": gross_salary,
            "net_salary": net_salary,
        },
    )


def add_salary_structure(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    active_salary_structure = employee.salary_structures.filter(is_active=True).first()
    if active_salary_structure:
        active_gross_salary = active_salary_structure.gross_salary()
        active_net_salary = active_salary_structure.net_salary()
    else:
        active_gross_salary = None
        active_net_salary = None

    components = SalaryComponent.objects.all()

    if request.method == "POST":
        effective_date = request.POST.get("effective_date")
        end_date = request.POST.get("end_date")
        basic_pay = request.POST.get("basic_pay")
        description = request.POST.get("description", "")
        errors = {}
        try:
            basic_pay_val = float(basic_pay)
            if basic_pay_val < 0:
                errors["basic_pay"] = "Must be positive."
        except:
            errors["basic_pay"] = "Invalid number."
        try:
            effective_date_val = datetime.strptime(effective_date, "%Y-%m-%d").date()
        except:
            errors["effective_date"] = "Invalid date."
        if end_date:
            try:
                end_date_val = datetime.strptime(end_date, "%Y-%m-%d").date()
                if end_date_val < effective_date_val:
                    errors["end_date"] = "End date must be after effective date."
            except:
                errors["end_date"] = "Invalid date."
        if errors:
            return render(
                request,
                "payroll/add_salary_structure.html",
                {
                    "employee": employee,
                    "components": components,
                    "errors": errors,
                    "data": request.POST,
                    "active_salary_structure": active_salary_structure,
                },
            )
        existing_structures = employee.salary_structures.filter(is_active=True)
        for structure in existing_structures:
            if not structure.end_date or structure.end_date > effective_date_val:
                structure.end_date = effective_date_val - timedelta(days=1)
                structure.is_active = False
                structure.save()
        salary_structure = SalaryStructure.objects.create(
            employee=employee,
            effective_date=effective_date_val,
            end_date=end_date if end_date else None,
            basic_pay=basic_pay_val,
            description=description,
            is_active=True,
        )
        for comp in components:
            comp_amount = request.POST.get(f"component_{comp.id}")
            if comp_amount:
                try:
                    amount_val = float(comp_amount)
                except:
                    amount_val = 0
                SalaryStructureLine.objects.create(
                    salary_structure=salary_structure,
                    salary_component=comp,
                    amount=amount_val,
                )
        return redirect("employee_detail", employee_id=employee.employee_id)
    return render(
        request,
        "payroll/add_salary_structure.html",
        {
            "employee": employee,
            "components": components,
            "active_salary_structure": active_salary_structure,
            "active_gross_salary": active_gross_salary,
            "active_net_salary": active_net_salary,
        },
    )


def old_salary_structures(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    old_salary_structures = employee.salary_structures.filter(is_active=False)
    return render(
        request,
        "payroll/old_salary_structures.html",
        {"employee": employee, "old_salary_structures": old_salary_structures},
    )
