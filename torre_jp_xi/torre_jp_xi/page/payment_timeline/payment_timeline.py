import frappe
from frappe import _


@frappe.whitelist()
def get_timeline(customer):
	if not customer:
		return _empty_response()

	page = frappe.get_doc("Page", "payment-timeline")
	if not page.is_permitted():
		frappe.throw(
			_("No tiene permiso para acceder a esta página"),
			frappe.PermissionError,
		)

	if not frappe.db.exists("Customer", customer):
		frappe.throw(_("Cliente no encontrado: {0}").format(customer))

	gl_rows = frappe.get_all(
		"GL Entry",
		filters={
			"party_type": "Customer",
			"party": customer,
			"is_cancelled": 0,
		},
		fields=[
			"voucher_type",
			"voucher_no",
			"posting_date",
			"debit",
			"credit",
			"remarks",
		],
		order_by="posting_date asc, creation asc",
		limit_page_length=0,
	)

	events_map = {}
	for g in gl_rows:
		key = (g.voucher_type, g.voucher_no)
		if key not in events_map:
			events_map[key] = {
				"voucher_type": g.voucher_type,
				"voucher_no": g.voucher_no,
				"posting_date": str(g.posting_date) if g.posting_date else "",
				"debit": 0.0,
				"credit": 0.0,
				"remarks": g.remarks or "",
			}
		events_map[key]["debit"] += g.debit or 0
		events_map[key]["credit"] += g.credit or 0

	events = []
	for v in events_map.values():
		net = v["debit"] - v["credit"]
		if abs(net) < 0.005:
			continue
		v["net"] = net
		v["amount"] = abs(net)
		v["kind"] = "charge" if net > 0 else "payment"
		events.append(v)

	events.sort(
		key=lambda e: (e["posting_date"], 0 if e["kind"] == "charge" else 1)
	)

	si_names = [e["voucher_no"] for e in events if e["voucher_type"] == "Sales Invoice"]
	pe_names = [e["voucher_no"] for e in events if e["voucher_type"] == "Payment Entry"]
	je_names = [e["voucher_no"] for e in events if e["voucher_type"] == "Journal Entry"]

	si_map = {}
	if si_names:
		for s in frappe.get_all(
			"Sales Invoice",
			filters={"name": ["in", si_names]},
			fields=["name", "status", "outstanding_amount", "grand_total", "remarks"],
			limit_page_length=0,
		):
			si_map[s.name] = s

	pe_map = {}
	if pe_names:
		for p in frappe.get_all(
			"Payment Entry",
			filters={"name": ["in", pe_names]},
			fields=["name", "reference_no", "mode_of_payment"],
			limit_page_length=0,
		):
			pe_map[p.name] = p

	je_map = {}
	if je_names:
		for j in frappe.get_all(
			"Journal Entry",
			filters={"name": ["in", je_names]},
			fields=["name", "user_remark"],
			limit_page_length=0,
		):
			je_map[j.name] = j

	allocations = []
	if pe_names:
		for r in frappe.get_all(
			"Payment Entry Reference",
			filters={
				"parent": ["in", pe_names],
				"reference_doctype": "Sales Invoice",
			},
			fields=["parent", "reference_name", "allocated_amount"],
			limit_page_length=0,
		):
			allocations.append(
				{
					"payment_voucher": r.parent,
					"payment_voucher_type": "Payment Entry",
					"invoice_voucher": r.reference_name,
					"invoice_voucher_type": "Sales Invoice",
					"amount": r.allocated_amount,
				}
			)

	if je_names:
		for r in frappe.get_all(
			"Journal Entry Account",
			filters={
				"parent": ["in", je_names],
				"party_type": "Customer",
				"party": customer,
				"reference_type": "Sales Invoice",
			},
			fields=[
				"parent",
				"reference_name",
				"credit_in_account_currency",
				"debit_in_account_currency",
			],
			limit_page_length=0,
		):
			amt = (r.credit_in_account_currency or 0) - (r.debit_in_account_currency or 0)
			if abs(amt) > 0.005:
				allocations.append(
					{
						"payment_voucher": r.parent,
						"payment_voucher_type": "Journal Entry",
						"invoice_voucher": r.reference_name,
						"invoice_voucher_type": "Sales Invoice",
						"amount": abs(amt),
					}
				)

	attachments = {}
	voucher_names = pe_names + je_names
	if voucher_names:
		for f in frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": ["in", ["Payment Entry", "Journal Entry"]],
				"attached_to_name": ["in", voucher_names],
			},
			fields=[
				"name",
				"file_name",
				"file_url",
				"file_type",
				"is_private",
				"attached_to_name",
			],
			limit_page_length=0,
		):
			attachments.setdefault(f.attached_to_name, []).append(
				{
					"name": f.name,
					"file_name": f.file_name,
					"file_url": f.file_url,
					"file_type": f.file_type,
					"is_private": f.is_private,
				}
			)

	return {
		"events": events,
		"allocations": allocations,
		"si_map": si_map,
		"pe_map": pe_map,
		"je_map": je_map,
		"attachments": attachments,
	}


def _empty_response():
	return {
		"events": [],
		"allocations": [],
		"si_map": {},
		"pe_map": {},
		"je_map": {},
		"attachments": {},
	}
