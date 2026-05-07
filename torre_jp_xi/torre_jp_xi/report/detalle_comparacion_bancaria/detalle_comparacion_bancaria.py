# Copyright (c) 2025, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder import Criterion, functions as fn
def execute(filters=None):
	return get_columns(), get_data(filters)

def get_columns():
	return []

def get_data(filters):
	pass

def get_payment_entries(filters):
	PE = frappe.qb.DocType("Payment Entry")
	conditions = [
		PE.posting_date >= filters.from_date,
		PE.posting_date <= filters.to_date,
		PE.company == filters.company,
		PE.bank_account == filters.bank_account,
		PE.docstatus == 1
	]
	return frappe.qb.from_(PE).select(
		PE.name,
		PE.posting_date,
		PE.paid_amount
	).where(
		Criterion.all(conditions)
	).run(as_dict=True)