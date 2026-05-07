// Copyright (c) 2025, Lewin Villar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Extra Payment Tool', {
	refresh(frm) {
		frm.trigger("add_custom_buttons");
		frm.trigger("set_queries");
	},
	add_custom_buttons(frm) {
		if (!frm.doc.customers){
			frm.add_custom_button(__('Get Customers'), function() {
				frm.call("get_customers");
			}).addClass('btn-primary');
		}
		else {
			frm.add_custom_button(__('Create Invoices'), function() {
				frappe.dom.freeze(__("Creating Invoices..."));
				frm.call("create_invoices").then(() => {
					frappe.utils.play_sound("submit");
					frappe.show_alert({message: __('Invoices Created Successfully'), indicator: 'green'});
				}).finally(() => {
					frappe.dom.unfreeze();
				});
			}).addClass('btn-primary');
		}
	},
	set_queries(frm) {
		frm.set_query("income_account", function() {
			return {
				filters: {
					account_type: "Income Account",
					is_group: 0,
					company: frm.doc.company
				}
			};
		});
	}
});
