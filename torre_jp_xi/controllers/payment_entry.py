import frappe

def validate(doc, event):
    validate_bank_account(doc)

def on_submit(doc, event):
    filters = {
        "attached_to_name": doc.name,
        "attached_to_doctype": doc.doctype,
    }
    if not frappe.db.exists("File", filters):
        frappe.throw(f"Please attach the receipt before submitting the document")

def validate_bank_account(doc):
    if doc.payment_type == "Pay":
        return
    
    mode_of_payment =  frappe.get_doc("Mode of Payment", {"name": doc.mode_of_payment})
    if mode_of_payment.type != "Bank":
        return 
    if not mode_of_payment.accounts:
        return

    # Let's find the matching row with the corresponding company
    row = list(filter(lambda x: x.company == doc.company, mode_of_payment.accounts))
    if not row:
        frappe.errprint(f"No Bank Account for company {doc.company}")
        return
    filters = {
        "company": doc.company,
        "account": row[0].default_account,
        "is_company_account": 1
    }
    account = frappe.db.exists("Bank Account", filters, ["account"])
    if account:
        doc.bank_account = account
