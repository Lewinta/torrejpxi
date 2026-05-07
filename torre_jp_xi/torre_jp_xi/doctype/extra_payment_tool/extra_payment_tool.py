# Copyright (c) 2025, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder import Criterion, Order
from frappe.model.document import Document
from frappe.utils import add_days

class ExtraPaymentTool(Document):
	def on_submit(self):
		self.create_invoices()

	@frappe.whitelist()
	def create_invoices(self):
		cost_center = frappe.get_value("Company", self.company, "cost_center")
		default_uom = frappe.get_value("Stock Settings", None, "default_uom")
		for row in self.customers:
			sinv = frappe.new_doc("Sales Invoice")
			sinv.update({
				"customer": row.customer,
				"posting_date": self.posting_date,
				"due_date": add_days(self.posting_date, 30),
				"company": self.company,
				"cost_center": cost_center,
				"remarks": self.remarks,
				"items": [{
					"item_name": "Cuota Extraordinaria",
					"description": "Cuota Extraordinaria",
					"qty": 1,
					"rate": row.amount,
					"remarks": row.remarks,
					"uom": default_uom,
					"conversion_factor": 1,
					"income_account": self.income_account
				}]
			})
			sinv.set_missing_values()
			sinv.calculate_taxes_and_totals()
			sinv.save()
			sinv.submit()
	
	@frappe.whitelist()
	def get_customers(self):
		CS = frappe.qb.DocType("Customer")

		conditions = [
			(CS.customer_type == "Proprietorship"),
			(CS.disabled == 0)
		]

		self.set("customers", [])
		
		customers = frappe.qb.from_(CS).select(
			CS.name
		).where(
			Criterion.all(conditions)
		).orderby(
			CS.name, Order.asc
		).run(as_dict=True)
		
		
		for customer in customers:
			self.append("customers", {
				"customer": customer.name,
				"amount": self.amount,
				"remarks": self.remarks,
			})
		
		self.total_amount = len(customers) * self.amount
		self.save()
		
