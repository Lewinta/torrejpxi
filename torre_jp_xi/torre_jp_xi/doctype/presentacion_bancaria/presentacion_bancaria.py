# Copyright (c) 2025, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days
from frappe.model.document import Document
from erpnext.accounts.utils import get_balance_on
from frappe.query_builder import Query, Criterion, functions as fn
GL = frappe.qb.DocType("GL Entry")
BA = frappe.qb.DocType("Bank Account")
BT = frappe.qb.DocType("Bank Transaction")
JV = frappe.qb.DocType("Journal Entry")
PE = frappe.qb.DocType("Payment Entry")

class PresentacionBancaria(Document):
    def before_print(self, settings):
        self.html = self.fetch_records()

    def get_opening_balance(self):
        return get_balance_on(
            account = frappe.get_value("Bank Account", self.bank_account, "account"),
            date = add_days(self.from_date, -1),
            company = self.company,
            ignore_account_permission=True
        )
    
    def get_system_data(self):
        conditions = [
            GL.posting_date >= self.from_date,
            GL.posting_date <= self.to_date,
            GL.company <= self.company,
            BA.name == self.bank_account,
            GL.is_cancelled == 0
        ]
        result =  {
            'system_deposit': .00,
            'system_withdrawal': .00
        }
        data = frappe.qb.from_(GL).join(BA).on(
            GL.account ==  BA.account
        ).select(
            fn.Sum(GL.debit).as_('system_deposit'),
            fn.Sum(GL.credit).as_('system_withdrawal')
        ).where(
            Criterion.all(conditions)
        ).groupby(GL.account).run(as_dict=True, debug=True)

        if data:
            result.update(data[0])
        
        return result

    def get_bank_data(self):
        conditions = [
            BT.date >= self.from_date,
            BT.date <= self.to_date,
            BT.company == self.company,
            BT.bank_account == self.bank_account,
            BT.status == "Reconciled"
        ]
        result =  {
            'bank_deposit': .00,
            'bank_withdrawal': .00
        }
        data = frappe.qb.from_(BT).select(
            fn.Sum(BT.deposit).as_("bank_deposit"),
            fn.Sum(BT.withdrawal).as_("bank_withdrawal"),
        ).where(
            Criterion.all(conditions)
        ).groupby(BT.bank_account).run(as_dict=True, debug=True)

        if data:
            result.update(data[0])
        
        return result

    def get_deposits_in_transit(self):
        conditions = [
            PE.docstatus == 1,
            PE.posting_date >= self.from_date,
            PE.posting_date <= self.to_date,
            PE.payment_type == 'Receive',
            PE.clearance_date.isnull(),
            PE.company == self.company,
            PE.bank_account == self.bank_account
        ]
        data = frappe.qb.from_(PE).select(
            fn.Sum(PE.paid_amount).as_("deposit_in_transit")
        ).where(
            Criterion.all(conditions)
        ).groupby(PE.bank_account).run(as_dict=True)

        return data[0] if data else { "deposit_in_transit": .00 }

    def get_pending_checks(self):
        pe_conditions = [
            PE.docstatus == 1,
            PE.posting_date >= self.from_date,
            PE.posting_date <= self.to_date,
            PE.payment_type == 'Pay',
            PE.clearance_date.isnull(),
            PE.company == self.company,
            PE.bank_account == self.bank_account
        ]
        jv_conditions = [
            JV.docstatus == 1,
            JV.posting_date >= self.from_date,
            JV.posting_date <= self.to_date,
            JV.clearance_date.isnull(),
            JV.company == self.company,
            JV.mode_of_payment == 'Cheque'
        ]
        payment_entries = Query.from_(PE).select(
            PE.paid_amount.as_("pending_checks")
        ).where(
            Criterion.all(pe_conditions)
        )

        journal_entries = Query.from_(JV).select(
            JV.total_debit.as_("pending_checks")
        ).where(
            Criterion.all(jv_conditions)
        )

        query = payment_entries + journal_entries

        data = frappe.qb.from_(query).select(
            fn.Coalesce(
                fn.Sum(query.pending_checks),
                .00
            ).as_("pending_checks")
        ).run(as_dict=True)

        return data[0] if data else {"pending_checks": .00}

    @frappe.whitelist()
    def fetch_records(self):
        data = {
            "doc": self,
            "opening_balance": self.get_opening_balance()
        }
        url = 'torre_jp_xi/doctype/presentacion_bancaria/presentacion_bancaria.html'
        system_data = self.get_system_data()
        bank_data = self.get_bank_data()
        deposit_in_transit = self.get_deposits_in_transit()
        pending_checks = self.get_pending_checks()
        data.update(system_data)
        data.update(bank_data)
        data.update(deposit_in_transit)
        data.update(pending_checks)
        return frappe.render_template(url, data)
