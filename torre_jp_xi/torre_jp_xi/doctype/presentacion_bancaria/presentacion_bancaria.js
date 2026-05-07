// Copyright (c) 2025, Lewin Villar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Presentacion Bancaria', {
	refresh(frm) {
		frm.trigger("set_queries");
		frm.trigger("fetch_records");
	},
	set_queries(frm){
		frm.set_query("company", function(){
			return {
				filters: {
					is_group: 0
				}
			}
		})

		frm.set_query("bank_account", function (){
			return { 
				filters: {
					company: frm.doc.company,
					is_company_account: 1
				}
			}
		})
	},
	fetch_records(frm) {
		frm.call("fetch_records").then( ({message}) => {
		  frm.set_df_property("html", "options", message)
		});
	  },
});
