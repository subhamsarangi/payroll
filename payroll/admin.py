from django.contrib import admin
from .models import (
    Employee,
    BankAccount,
    SalaryComponent,
    SalaryStructure,
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
    list_display = ("name", "code", "component_type", "mode")
    search_fields = ("name", "code")


admin.site.register(SalaryStructure)
