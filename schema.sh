Table SalaryComponent { 
  id int [pk, increment]
  name varchar(100)
  type varchar(10) // e.g., "earning", "deduction"
  mode varchar(10) // e.g., "fixed", "percentage"
  action varchar(10) // compulsory, optional
  value decimal(10,2)
  business_unit int
  description text
}

Table SalaryStructure {
  id int [pk, increment]
  employee_id int
  effective_date date
  end_date date                     // New: defines the validity period of the structure (nullable if open-ended)
  basic_pay decimal(10,2)
  incentive_eligibility boolean [default: false]
  is_active boolean [default: true]
  description text
  created_at datetime               // New: audit field
  updated_at datetime               // New: audit field
  created_by int                    // New: audit field (could reference a user id)
  updated_by int                    // New: audit field (could reference a user id)
}

Table SalaryStructureLine {
  id int [pk, increment]
  salary_structure_id int [ref: > SalaryStructure.id]
  salary_component_id int [ref: > SalaryComponent.id]
  amount decimal(10,2)
  created_at datetime               // New: audit field (optional)
  updated_at datetime               // New: audit field (optional)

  indexes {
    (salary_structure_id, salary_component_id) [unique]
  }
}

Table PayrollRun {
  id int [pk, increment]
  run_date datetime                 // Date and time when the payroll run occurred
  status varchar(20)                // e.g., "completed", "failed"
  run_version varchar(50)           // Identifier or version of the payroll run
  notes text
  created_at datetime               // Audit field
  updated_at datetime               // Audit field
}

Table MonthlySalary {
  id int [pk, increment]
  employee_id int
  salary_structure_id int [ref: > SalaryStructure.id, note: "nullable"]
  payroll_run_id int [ref: > PayrollRun.id, note: "nullable"]  // New: links monthly salary to a specific payroll run
  month int
  year int
  gross_amount decimal(10,2)
  net_amount decimal(10,2)
  created_at datetime
  updated_at datetime

  indexes {
    (employee_id, month, year) [unique]
  }
}

Table MonthlySalaryLine {
  id int [pk, increment]
  monthly_salary_id int [ref: > MonthlySalary.id]
  salary_component_id int [ref: > SalaryComponent.id]
  amount decimal(10,2)

  indexes {
    (monthly_salary_id, salary_component_id) [unique]
  }
}

Table PayrollAdjustment {
  id int [pk, increment]
  monthly_salary_id int [ref: > MonthlySalary.id]
  adjustment_amount decimal(10,2)
  reason text
  created_at datetime
  created_by int                    // Could reference a user id who made the adjustment
}
