// Copyright (c) 2024, Lewin Villar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Gas Entry', {
	refresh(frm) {
		const events = ['add_custom_buttons', 'set_defaults'];
		$.map(events, event => frm.trigger(event));
	},
	add_custom_buttons(frm) {
		if (frm.doc.docstatus > 0)
			return;
		frm.add_custom_button(__('Get Customers'), () => {
			frm.call("get_customers");
		}).addClass('btn-primary');
	},
	set_defaults(frm) {
		if(!frm.is_new())
			return;

		frm.set_value('responsible', frappe.session.user);
	}
});
