# Copyright (c) 2024, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, add_days
from frappe.model.document import Document
from frappe.query_builder import Criterion, Query, Order, functions as fn

class GasEntry(Document):
	def validate(self):
		self.validate_multiple_customers()
		self.calculate_totals()
	
	
	def on_submit(self):
		self.create_invoices()
	
	def on_cancel(self):
		self.cancel_invoices()

	
	def validate_multiple_customers(self):
		# Let's check if there are multiple customers in the readings table
		readings = set()
		for row in self.readings:
			if row.customer in readings:
				frappe.throw(f"Customer {row.customer} appears more than once in the table")
			readings.add(row.customer)

	
	def calculate_totals(self):
		if not self.conversion_factor:
			frappe.throw("Please set the conversion factor")
		
		if not self.price_gallon:
			frappe.throw("Please set the price per gallon")

		self.total_gal =  self.total_amount = .00
		
		for row in self.readings:
			row.used_m3 = flt(row.actual_m3) - flt(row.before_m3)
			row.used_gal = flt(row.used_m3) * flt(self.conversion_factor)
			row.used_amount = flt(row.used_gal) * flt(self.price_gallon)
			self.total_gal += row.used_gal
			self.total_amount += row.used_amount
		
			
	@frappe.whitelist()
	def get_customers(self):
		CS = frappe.qb.DocType("Customer")
		GE = frappe.qb.DocType("Gas Entry")
		GI = frappe.qb.DocType("Gas Entry Item")
		
		conditions = [
			(CS.customer_type == "Proprietorship"),
			(CS.disabled == 0)
		]
		
		last_reading = Query.from_(GE).join(GI).on(
			GE.name == GI.parent
		).select( GI.actual_m3 ).where(
			(GI.customer == CS.name)&
			(GI.docstatus == 1)&
			(GI.parent != self.name)
		).orderby(GE.date, Order.desc).limit(1)
		

		# Let's get the last reading for each customer
		customer_readings =  frappe.qb.from_(CS).select(
			CS.name,
			last_reading.as_("last_reading")
		).where(Criterion.all(conditions)).run(as_dict=True)

		self.set("readings", [])

		for reading in customer_readings:
			self.append("readings", {
				"customer": reading.name,
				"before_m3": flt(reading.last_reading)
			})
		
		self.calculate_totals()
		

	def create_invoices(self):
		# Let's get the default company
		for row in self.readings:
			doc = frappe.get_doc({
				"doctype": "Sales Invoice",
				"company": self.company,
				"customer": row.customer,
				"posting_date": str(self.date).split(" ")[0],
				"posting_time": str(self.date).split(" ")[1],
				"set_posting_time": 1,
				# "due_date": self.date,
			})
			
			doc.append("items", {
				"item_code": "Gas Mensual",
				"qty": row.used_gal,
				"rate": self.price_gallon,
				"amount": row.used_amount
			})

			doc.set_missing_values()
			doc.save()
			doc.submit()
			row.invoice = doc.name
		
		self.save()
		
		frappe.msgprint("Invoices created successfully")
	
	def cancel_invoices(self):
		for row in self.readings:
			if not row.invoice or not frappe.db.exists("Sales Invoice", row.invoice):
				continue
			doc = frappe.get_doc("Sales Invoice", row.invoice)
			doc.cancel()
			row.invoice = None
		self.save()
		