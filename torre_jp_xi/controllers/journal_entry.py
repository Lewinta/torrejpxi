import frappe
from erpnext.accounts.doctype.journal_entry.journal_entry import JournalEntry as CustomJournalEntry

class JournalEntry(CustomJournalEntry):

    def on_update(self):
        self.set_bank_accounts()

    def set_bank_accounts(self):
        # This function will set the bank account for the journal entry accounts
        # that are missing it. It will use the account and company to find the bank account
        # and set it to the journal entry account
        
        BA = frappe.qb.DocType("Bank Account")
        JA = frappe.qb.DocType("Journal Entry Account")

        frappe.qb.update(JA).join(BA).on(
            (JA.account == BA.account)&
            (BA.is_company_account == 1)
        ).set(
            JA.bank_account, BA.name
        ).where(
            JA.parent == self.name
        ).run()