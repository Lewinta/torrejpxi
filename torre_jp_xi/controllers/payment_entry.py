import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry as CustomPaymentEntry

class PaymentEntry(CustomPaymentEntry):
    def validate(self):
        super(PaymentEntry, self).validate()
        self.validate_bank_account()

    def validate_bank_account(self):
        if self.payment_type == "Pay":
            return
        
        mode_of_payment =  frappe.get_doc("Mode of Payment", {"name": self.mode_of_payment})
        if mode_of_payment.type != "Bank":
            return 
        if not mode_of_payment.accounts:
            return

        # Let's find the matching row with the corresponding company
        row = list(filter(lambda x: x.company == self.company, mode_of_payment.accounts))
        if not row:
            frappe.errprint(f"No Bank Account for company {self.company}")
            return
        filters = {
            "company": self.company,
            "account": row[0].default_account,
            "is_company_account": 1
        }
        account = frappe.db.exists("Bank Account", filters, ["account"])
        if account:
            self.bank_account = account
