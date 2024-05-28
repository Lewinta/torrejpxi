import frappe

from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice as SalesInvoiceERPNext

class SalesInvoice(SalesInvoiceERPNext):
    def validate(self):
        super(SalesInvoice, self).validate()
        self.set_remarks()
    
    def set_remarks(self):
        # If auto_repeat is set, set remarks to the next Month
        month_map = {
            1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr',
            5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago',
            9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
        }

        if self.auto_repeat:
            year, month, day = str(self.posting_date).split('-')
            self.remarks = f"{month_map[int(month)]} {year[-2:]}"