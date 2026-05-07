frappe.ui.form.on("Journal Entry", {
    refresh(frm){

    }
});

frappe.ui.form.on("Journal Entry Account", {
    account(frm, cdt, cdn){
        const row = locals[cdt][cdn];
        if (!row.account) return;
        const method = "torre_jp_xi.utils.get_bank_account"
        const args = {"company": frm.doc.company, "account": row.account}
        frappe.call({method, args, callback: ({message}) => {
            if (message) {
                frappe.model.set_value(cdt, cdn, "bank_account", message);
            }
        }});
    }
});