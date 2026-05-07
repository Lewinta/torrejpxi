import frappe
from frappe.utils import today
from frappe import qb

@frappe.whitelist()
def get_bank_account(company, mop=None, account=None):
    if not mop and not account:
        frappe.throw("Please provide either a Mode of Payment or an Account")

    BA = qb.DocType('Bank Account')
    MP = qb.DocType('Mode of Payment')
    MA = qb.DocType('Mode of Payment Account')

    data = None

    if account:
        data = frappe.qb.from_(BA).where(
            (BA.account == account)&
            (BA.is_company_account == 1)
        ).select(
            BA.name
        ).limit(1).run(as_dict=True)

    elif mop:
        data = frappe.qb.from_(MP).join(MA).on(
            MP.name == MA.parent
        ).join(BA).on(
            MA.default_account == BA.account
        ).where(
            (MP.name == mop)&
            (BA.is_company_account == 1)&
            (MA.company == company)
        ).select(
            BA.name
        ).limit(1).run(as_dict=True)

    return data[0].name if data else None

def validate_comment_on_cancel(doc, method=None):
    C = qb.DocType('Comment')

    comment = frappe.qb.from_(C).where(
        (C.reference_doctype == doc.doctype) &
        (C.reference_name == doc.name) &
        (C.comment_type == 'Comment') &
        (C.comment_email == frappe.session.user)&
        (C.creation[today() + " 00:00:00": today() + " 23:59:59"])
    ).select(
        C.name
    ).limit(1).run(as_dict=True)

    if not comment:
        frappe.throw("""
            Favor agregar un comentario al final de la página 
            con la razón de la anulación del documento antes de proceder.
        """)
