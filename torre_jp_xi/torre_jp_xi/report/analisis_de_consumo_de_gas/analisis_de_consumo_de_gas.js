// Copyright (c) 2025, Lewin Villar and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Analisis de Consumo de Gas"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("Desde"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.year_start(), -24),
		},
		{
			"fieldname": "to_date",
			"label": __("Hasta"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_days(frappe.datetime.get_today(), 1),
		},
		{
			"fieldname": "based_on",
			"label": __("Basado en"),
			"fieldtype": "Select",
			"options": "\nConsumo\nMonto"	
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		let formatted = default_formatter(value, row, column, data);
		let color = null;
		// const based_on = frappe.query_report.get_filter_value("based_on");

		if (frappe.query_report.get_filter_value("based_on") === "Monto") {
			if (column.fieldname === "last_consumption" ) {
				if (flt(data.last_consumption) > flt(data.average_consumption)) {
					color = "red";
				} else if (flt(data.last_consumption) === flt(data.average_consumption)) {
					color = "orange";
				} else {
					color = "green";
				}
			}
		}
		
		if (frappe.query_report.get_filter_value("based_on") === "Consumo") {
			if (column.fieldname === "last_amount" && data.average_amount !== undefined) {
				if (data.last_amount > data.average_amount) {
					color = "red";
				} else if (data.last_amount === data.average_amount) {
					color = "orange";
				} else {
					color = "green";
				}
			}
		}

		if (color) {
			formatted = `<span style="color: ${color}; font-weight: bold;">${formatted}</span>`;
		}

		return formatted;
	}
};