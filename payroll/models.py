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

    FIXED = "fixed"
    PERCENTAGE = "percentage"
    MODE_TYPES = [
        (FIXED, "Fixed"),
        (PERCENTAGE, "Percentage"),
    ]

    COMPULSORY = "compulsory"
    OPTIONAL = "optional"
    ACTION_TYPES = [
        (COMPULSORY, "Compulsory"),
        (OPTIONAL, "Optional"),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    component_type = models.CharField(max_length=10, choices=COMPONENT_TYPES)
    mode = models.CharField(max_length=10, choices=MODE_TYPES, default=FIXED)
    action = models.CharField(max_length=10, choices=ACTION_TYPES, default=COMPULSORY)
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    business_unit = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class SalaryStructure(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="salary_structures"
    )
    effective_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    basic_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    incentive_eligibility = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-effective_date"]

    def __str__(self):
        return (
            f"Salary Structure for {self.employee.name} effective {self.effective_date}"
        )

    def save(self, *args, **kwargs):
        if not self.pk:
            # Only set created_at for new objects
            self.created_at = timezone.now()
        # Always update updated_at
        self.updated_at = timezone.now()

        if self.is_active:
            SalaryStructure.objects.filter(
                employee=self.employee, is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def calculate_component_amounts(self):
        calculated = {}
        for line in self.lines.all():
            if line.salary_component.mode == SalaryComponent.PERCENTAGE:
                calculated_amount = self.basic_pay * line.amount / 100
            else:
                calculated_amount = line.amount
            calculated[line.salary_component.code] = calculated_amount
        return calculated

    def gross_salary(self):
        """Calculate the gross salary by summing up the basic pay and all positive components."""
        total_components = sum(self.calculate_component_amounts().values())
        return self.basic_pay + total_components

    def net_salary(self):
        """Calculate the net salary by subtracting any deductions from the gross salary."""
        total_deductions = sum(
            line.amount
            for line in self.lines.all()
            if line.salary_component.mode == SalaryComponent.DEDUCTION
        )
        return self.gross_salary() - total_deductions


class SalaryStructureLine(models.Model):
    salary_structure = models.ForeignKey(
        SalaryStructure, on_delete=models.CASCADE, related_name="lines"
    )
    salary_component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("salary_structure", "salary_component")

    def __str__(self):
        return f"{self.salary_component.name}: {self.amount}"

    def save(self, *args, **kwargs):
        if not self.pk:
            # Only set created_at for new objects
            self.created_at = timezone.now()
        # Always update updated_at
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)


class PayrollRun(models.Model):
    COMPLETED = "completed"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"

    STATUS_CHOICES = [
        (COMPLETED, "Completed"),
        (FAILED, "Failed"),
        (IN_PROGRESS, "In Progress"),
        (PENDING, "Pending"),
    ]

    run_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    run_version = models.CharField(max_length=50)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payroll Run {self.run_version} ({self.run_date.strftime('%Y-%m-%d')})"

    def save(self, *args, **kwargs):
        if not self.pk:
            # Only set created_at for new objects
            self.created_at = timezone.now()
        # Always update updated_at
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)


class MonthlySalary(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="monthly_salaries"
    )
    salary_structure = models.ForeignKey(
        SalaryStructure, on_delete=models.SET_NULL, null=True, blank=True
    )
    payroll_run = models.ForeignKey(
        PayrollRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="monthly_salaries",
    )
    month = models.PositiveSmallIntegerField()  # e.g. 1 for January, 12 for December
    year = models.PositiveSmallIntegerField()
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("employee", "month", "year")
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"Monthly Salary for {self.employee.name} - {self.month}/{self.year}"

    def save(self, *args, **kwargs):
        if not self.pk:
            # Only set created_at for new objects
            self.created_at = timezone.now()
        # Always update updated_at
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)


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


class PayrollAdjustment(models.Model):
    monthly_salary = models.ForeignKey(
        MonthlySalary, on_delete=models.CASCADE, related_name="adjustments"
    )
    adjustment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Adjustment for {self.monthly_salary} ({self.adjustment_amount})"
