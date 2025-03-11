from django.contrib import admin
from .models import (
    Employee,
    BankAccount,
    SalaryComponent,
    SalaryStructure,
    SalaryStructureLine,
    MonthlySalary,
    MonthlySalaryLine,
)


class BankAccountInline(admin.TabularInline):
    model = BankAccount
    extra = 0


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "name", "is_active")
    search_fields = ("employee_id", "name")
    inlines = [BankAccountInline]


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "bank_name",
        "account_number",
        "ifsc_code",
        "branch_name",
        "is_primary",
    )
    search_fields = ("employee__name", "bank_name", "account_number")


@admin.register(SalaryComponent)
class SalaryComponentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "component_type", "is_percentage")
    search_fields = ("name", "code")


class SalaryStructureLineInline(admin.TabularInline):
    model = SalaryStructureLine
    extra = 0


@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ("employee", "effective_date", "is_active")
    list_filter = ("is_active", "effective_date")
    search_fields = ("employee__name",)
    inlines = [SalaryStructureLineInline]


class MonthlySalaryLineInline(admin.TabularInline):
    model = MonthlySalaryLine
    extra = 0


@admin.register(MonthlySalary)
class MonthlySalaryAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "month",
        "year",
        "gross_amount",
        "net_amount",
        "created_at",
    )
    list_filter = ("year", "month")
    search_fields = ("employee__name",)
    inlines = [MonthlySalaryLineInline]
