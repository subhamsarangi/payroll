from django.db import models
from django.utils import timezone


class Employee(models.Model):
    employee_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.employee_id})"

    @property
    def current_salary_structure(self):
        """Returns the current active salary structure for this employee"""
        return self.salary_structures.filter(is_active=True).first()


class BankAccount(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="bank_accounts"
    )
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)
    branch_name = models.CharField(max_length=100)
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ("employee", "account_number")

    def __str__(self):
        return f"{self.employee.name} - {self.bank_name} ({self.account_number})"

    def save(self, *args, **kwargs):
        if self.is_primary:
            BankAccount.objects.filter(employee=self.employee, is_primary=True).update(
                is_primary=False
            )
        super().save(*args, **kwargs)


class SalaryComponent(models.Model):
    EARNING = "earning"
    DEDUCTION = "deduction"
    COMPONENT_TYPES = [
        (EARNING, "Earning"),
        (DEDUCTION, "Deduction"),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    component_type = models.CharField(max_length=10, choices=COMPONENT_TYPES)
    is_percentage = models.BooleanField(
        default=False,
        help_text="If true, the value represents a percentage (e.g. of basic salary).",
    )
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class SalaryStructure(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="salary_structures"
    )
    effective_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-effective_date"]

    def __str__(self):
        return (
            f"Salary Structure for {self.employee.name} effective {self.effective_date}"
        )

    def save(self, *args, **kwargs):
        if self.is_active:
            SalaryStructure.objects.filter(
                employee=self.employee, is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def total_fixed_amount(self):
        total = sum(
            [
                line.amount
                for line in self.lines.all()
                if not line.salary_component.is_percentage
            ]
        )
        return total

    def calculate_component_amounts(self, basic_salary):
        calculated = {}
        for line in self.lines.all():
            if line.salary_component.is_percentage:
                calculated_amount = basic_salary * line.amount / 100
            else:
                calculated_amount = line.amount
            calculated[line.salary_component.code] = calculated_amount
        return calculated


class SalaryStructureLine(models.Model):
    salary_structure = models.ForeignKey(
        SalaryStructure, on_delete=models.CASCADE, related_name="lines"
    )
    salary_component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ("salary_structure", "salary_component")

    def __str__(self):
        return f"{self.salary_component.name}: {self.amount}"


class MonthlySalary(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="monthly_salaries"
    )
    salary_structure = models.ForeignKey(
        SalaryStructure, on_delete=models.SET_NULL, null=True, blank=True
    )
    month = models.PositiveSmallIntegerField()  # e.g. 1 for January, 12 for December
    year = models.PositiveSmallIntegerField()
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("employee", "month", "year")
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"Monthly Salary for {self.employee.name} - {self.month}/{self.year}"


class MonthlySalaryLine(models.Model):
    monthly_salary = models.ForeignKey(
        MonthlySalary, on_delete=models.CASCADE, related_name="salary_lines"
    )
    salary_component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ("monthly_salary", "salary_component")

    def __str__(self):
        return f"{self.salary_component.name}: {self.amount}"
