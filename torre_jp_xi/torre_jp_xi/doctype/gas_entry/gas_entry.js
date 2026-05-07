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
	},
	calculate_totals(frm){
		if (!frm.doc.conversion_factor)
			frappe.throw("Please set the conversion factor")
		
		if (!frm.doc.price_gallon)
			frappe.throw("Please set the price per gallon")

		frm.doc.total_gal =  0.00;
		frm.doc.total_amount = 0.00;
		
		$.map(frm.doc.readings, row => {
			let used_m3 = flt(row.actual_m3) - flt(row.before_m3)
			let used_gal = flt(used_m3) * flt(frm.doc.conversion_factor)
			let used_amount = flt(used_gal) * flt(frm.doc.price_gallon)
			
			frappe.model.set_value(row.doctype, row.name, 'used_m3', used_m3)
			frappe.model.set_value(row.doctype, row.name, 'used_gal', used_gal)
			frappe.model.set_value(row.doctype, row.name, 'used_amount', used_amount)
			
			frm.doc.total_gal += row.used_gal
			frm.doc.total_amount += row.used_amount
		});
	}
});

frappe.ui.form.on('Gas Entry Item', {
	actual_m3(frm, cdt, cn){
		frm.trigger("calculate_totals");
	}
});