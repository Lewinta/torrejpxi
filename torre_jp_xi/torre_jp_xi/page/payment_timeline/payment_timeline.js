frappe.pages["payment-timeline"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Historial de Pagos",
		single_column: true,
	});

	page.main.append(`<div id="payment-timeline-app"></div>`);
	new PaymentTimeline(page);
};

class PaymentTimeline {
	constructor(page) {
		this.page = page;
		this.customer = null;
		this.events = [];
		this.allocations = [];
		this.si_map = {};
		this.pe_map = {};
		this.je_map = {};
		this.attachments = {};

		this.setup_filters();
	}

	setup_filters() {
		this.customer_field = this.page.add_field({
			fieldname: "customer",
			label: __("Inquilino"),
			fieldtype: "Link",
			options: "Customer",
			change: () => {
				const val = this.customer_field.get_value();
				if (val && val !== this.customer) {
					this.customer = val;
					this.load_data();
				}
			},
		});
	}

	async load_data() {
		const $app = this.page.main.find("#payment-timeline-app");
		$app.html(
			`<div class="ptl-loading"><div class="ptl-spinner"></div><p>Cargando movimientos...</p></div>`
		);

		try {
			const res = await frappe.call({
				method:
					"torre_jp_xi.torre_jp_xi.page.payment_timeline.payment_timeline.get_timeline",
				args: { customer: this.customer },
			});
			const data = res.message || {};
			this.events = data.events || [];
			this.allocations = data.allocations || [];
			this.si_map = data.si_map || {};
			this.pe_map = data.pe_map || {};
			this.je_map = data.je_map || {};
			this.attachments = data.attachments || {};

			this.render();
		} catch (err) {
			console.error(err);
			$app.html(
				`<div class="ptl-loading"><p class="ptl-red">Error al cargar datos</p></div>`
			);
		}
	}

	get_invoice_type(remarks) {
		const r = (remarks || "").toLowerCase();
		if (r.includes("gas")) return "gas";
		if (
			r.includes("pintura") ||
			r.includes("doble sueldo") ||
			r.includes("daños") ||
			r.includes("apertura")
		) {
			return "extra";
		}
		return "maintenance";
	}

	format_currency(val) {
		return new Intl.NumberFormat("es-DO", {
			minimumFractionDigits: 2,
			maximumFractionDigits: 2,
		}).format(val || 0);
	}

	format_date(d) {
		if (!d) return "—";
		const dt = new Date(d + "T12:00:00");
		return dt.toLocaleDateString("es-DO", {
			day: "2-digit",
			month: "short",
			year: "numeric",
		});
	}

	escape(str) {
		return String(str == null ? "" : str).replace(
			/[&<>"']/g,
			(c) =>
				({
					"&": "&amp;",
					"<": "&lt;",
					">": "&gt;",
					'"': "&quot;",
					"'": "&#39;",
				})[c]
		);
	}

	render() {
		const charges = this.events.filter((e) => e.kind === "charge");
		const payments = this.events.filter((e) => e.kind === "payment");

		const total_charged = charges.reduce((s, e) => s + e.amount, 0);
		const total_paid = payments.reduce((s, e) => s + e.amount, 0);
		const balance = total_charged - total_paid;

		const open_si = charges.filter(
			(e) =>
				e.voucher_type === "Sales Invoice" &&
				this.si_map[e.voucher_no] &&
				this.si_map[e.voucher_no].status !== "Paid"
		).length;

		const alloc_by_charge = {};
		const alloc_by_payment = {};
		this.allocations.forEach((a) => {
			if (!alloc_by_charge[a.invoice_voucher])
				alloc_by_charge[a.invoice_voucher] = [];
			alloc_by_charge[a.invoice_voucher].push(a);
			if (!alloc_by_payment[a.payment_voucher])
				alloc_by_payment[a.payment_voucher] = [];
			alloc_by_payment[a.payment_voucher].push(a);
		});

		let html = `
		<div class="ptl-root">
			<div class="ptl-summary">
				<div class="ptl-summary-card">
					<span class="ptl-summary-label">Total Facturado</span>
					<span class="ptl-summary-value">${this.format_currency(total_charged)}</span>
					<span class="ptl-summary-sub">${charges.length} cargos</span>
				</div>
				<div class="ptl-summary-card">
					<span class="ptl-summary-label">Total Pagado</span>
					<span class="ptl-summary-value ptl-green">${this.format_currency(total_paid)}</span>
					<span class="ptl-summary-sub">${payments.length} pagos</span>
				</div>
				<div class="ptl-summary-card ptl-summary-highlight">
					<span class="ptl-summary-label">Balance Pendiente</span>
					<span class="ptl-summary-value ${balance > 0.005 ? "ptl-red" : "ptl-green"}">${this.format_currency(balance)}</span>
					<span class="ptl-summary-sub">${open_si} facturas abiertas</span>
				</div>
			</div>

			<div class="ptl-timeline-container">
				<div class="ptl-col-headers">
					<div class="ptl-col-header ptl-col-left">
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
						Cargos
					</div>
					<div class="ptl-col-header ptl-col-center">Fecha</div>
					<div class="ptl-col-header ptl-col-right">
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
						Pagos
					</div>
				</div>

				<div class="ptl-timeline" id="ptl-timeline">`;

		if (this.events.length === 0) {
			html += `<div class="ptl-empty">No hay movimientos para este inquilino.</div>`;
		}

		let running = 0;
		let current_month = "";

		this.events.forEach((ev) => {
			if (ev.kind === "charge") running += ev.amount;
			else running -= ev.amount;
			ev.running_balance = running;

			const d = new Date(ev.posting_date + "T12:00:00");
			const month_key = d.toLocaleDateString("es-DO", {
				month: "long",
				year: "numeric",
			});
			if (month_key !== current_month) {
				current_month = month_key;
				html += `<div class="ptl-month-divider"><span>${month_key}</span></div>`;
			}

			html +=
				ev.kind === "charge"
					? this.render_charge_row(ev, alloc_by_charge)
					: this.render_payment_row(ev, alloc_by_payment);
		});

		html += `
				</div>
			</div>
		</div>

		<div class="ptl-lightbox" id="ptl-lightbox" style="display:none">
			<div class="ptl-lightbox-backdrop"></div>
			<div class="ptl-lightbox-content">
				<button class="ptl-lightbox-close">&times;</button>
				<div class="ptl-lightbox-header">
					<span id="ptl-lb-title"></span>
				</div>
				<div class="ptl-lightbox-body" id="ptl-lb-body"></div>
			</div>
		</div>`;

		this.page.main.find("#payment-timeline-app").html(html);
		this.bind_events();
	}

	render_charge_row(ev, alloc_by_charge) {
		const is_si = ev.voucher_type === "Sales Invoice";
		const si = is_si ? this.si_map[ev.voucher_no] : null;
		const status = si ? si.status : "";

		let status_class;
		if (!is_si) {
			status_class = "ptl-status-jv";
		} else if (status === "Paid") {
			status_class = "ptl-status-paid";
		} else if (status === "Overdue") {
			status_class = "ptl-status-overdue";
		} else {
			status_class = "ptl-status-unpaid";
		}

		const remarks =
			(si && si.remarks) ||
			(this.je_map[ev.voucher_no] && this.je_map[ev.voucher_no].user_remark) ||
			ev.remarks ||
			"";

		let badge_html;
		let type_class;
		if (is_si) {
			const inv_type = this.get_invoice_type(remarks);
			type_class = `ptl-inv-${inv_type}`;
			const label =
				inv_type === "gas"
					? "⛽ Gas"
					: inv_type === "extra"
						? "⚡ Extra"
						: "🏠 Mant.";
			badge_html = `<span class="ptl-card-type-badge">${label}</span>`;
		} else {
			type_class = "ptl-inv-jv";
			badge_html = `<span class="ptl-card-type-badge ptl-badge-jv">📒 Asiento</span>`;
		}

		const allocs = alloc_by_charge[ev.voucher_no] || [];
		const outstanding = si ? si.outstanding_amount : 0;
		const status_label = is_si ? status || "—" : "Asiento";
		const date_node_class = is_si ? "ptl-date-invoice" : "ptl-date-jv";

		return `
		<div class="ptl-row" data-charge="${this.escape(ev.voucher_no)}">
			<div class="ptl-cell ptl-cell-left">
				<div class="ptl-card ptl-card-invoice ${status_class} ${type_class}" data-doctype="${this.escape(ev.voucher_type)}" data-name="${this.escape(ev.voucher_no)}">
					<div class="ptl-card-top">
						${badge_html}
						<span class="ptl-card-status">${this.escape(status_label)}</span>
					</div>
					<div class="ptl-card-id">${this.escape(ev.voucher_no)}</div>
					<div class="ptl-card-desc">${this.escape(remarks)}</div>
					<div class="ptl-card-amount">${this.format_currency(ev.amount)}</div>
					${
						is_si && outstanding > 0.005 && outstanding < ev.amount
							? `<div class="ptl-card-outstanding">Pendiente: ${this.format_currency(outstanding)}</div>`
							: ""
					}
					${
						allocs.length > 0
							? `<div class="ptl-card-allocs">${allocs
									.map(
										(a) =>
											`<div class="ptl-alloc-tag" data-pay="${this.escape(a.payment_voucher)}"><span class="ptl-alloc-arrow">←</span> ${this.escape(a.payment_voucher)} <span class="ptl-alloc-amt">${this.format_currency(a.amount)}</span></div>`
									)
									.join("")}</div>`
							: is_si && status === "Paid"
								? `<div class="ptl-card-allocs"><div class="ptl-alloc-tag ptl-alloc-unknown">Pago no vinculado directamente</div></div>`
								: ""
					}
				</div>
			</div>
			<div class="ptl-cell ptl-cell-center">
				<div class="ptl-date-node ${date_node_class}"></div>
				<div class="ptl-date-label">${this.format_date(ev.posting_date)}</div>
				<div class="ptl-balance-badge ${ev.running_balance > 0.005 ? "ptl-bal-negative" : "ptl-bal-ok"}">
					Bal: ${this.format_currency(ev.running_balance)}
				</div>
			</div>
			<div class="ptl-cell ptl-cell-right"></div>
		</div>`;
	}

	render_payment_row(ev, alloc_by_payment) {
		const is_pe = ev.voucher_type === "Payment Entry";
		const pe = is_pe ? this.pe_map[ev.voucher_no] : null;
		const je =
			ev.voucher_type === "Journal Entry"
				? this.je_map[ev.voucher_no]
				: null;

		const ref = pe
			? pe.reference_no || pe.mode_of_payment || "—"
			: je
				? je.user_remark || "—"
				: ev.remarks || "—";

		const allocs = alloc_by_payment[ev.voucher_no] || [];
		const has_attachment = !!this.attachments[ev.voucher_no];

		const badge_html = is_pe
			? `<span class="ptl-card-type-badge ptl-badge-pay">💳 Pago</span>`
			: `<span class="ptl-card-type-badge ptl-badge-jv">📒 Asiento</span>`;

		return `
		<div class="ptl-row" data-pay="${this.escape(ev.voucher_no)}">
			<div class="ptl-cell ptl-cell-left"></div>
			<div class="ptl-cell ptl-cell-center">
				<div class="ptl-date-node ${is_pe ? "ptl-date-payment" : "ptl-date-jv"}"></div>
				<div class="ptl-date-label">${this.format_date(ev.posting_date)}</div>
				<div class="ptl-balance-badge ${ev.running_balance > 0.005 ? "ptl-bal-negative" : "ptl-bal-ok"}">
					Bal: ${this.format_currency(ev.running_balance)}
				</div>
			</div>
			<div class="ptl-cell ptl-cell-right">
				<div class="ptl-card ptl-card-payment ${is_pe ? "" : "ptl-card-payment-jv"}" data-doctype="${this.escape(ev.voucher_type)}" data-name="${this.escape(ev.voucher_no)}">
					<div class="ptl-card-top">
						${badge_html}
						${has_attachment ? `<button class="ptl-btn-receipt" data-pe="${this.escape(ev.voucher_no)}" title="Ver comprobante">📎</button>` : ""}
					</div>
					<div class="ptl-card-id">${this.escape(ev.voucher_no)}</div>
					<div class="ptl-card-ref">${is_pe ? "Ref" : "Nota"}: ${this.escape(ref)}</div>
					<div class="ptl-card-amount ptl-green">-${this.format_currency(ev.amount)}</div>
					${
						allocs.length > 0
							? `<div class="ptl-card-allocs">${allocs
									.map(
										(a) =>
											`<div class="ptl-alloc-tag ptl-alloc-pay" data-inv="${this.escape(a.invoice_voucher)}"><span class="ptl-alloc-arrow">→</span> ${this.escape(a.invoice_voucher)} <span class="ptl-alloc-amt">${this.format_currency(a.amount)}</span></div>`
									)
									.join("")}</div>`
							: ""
					}
				</div>
			</div>
		</div>`;
	}

	bind_events() {
		const $app = this.page.main.find("#payment-timeline-app");

		$app.on("click", ".ptl-btn-receipt", (e) => {
			e.stopPropagation();
			const name = $(e.currentTarget).data("pe");
			this.show_receipt(name);
		});

		$app.on("click", ".ptl-lightbox-backdrop, .ptl-lightbox-close", () => {
			$app.find("#ptl-lightbox").hide();
		});

		$app.on("mouseenter", ".ptl-alloc-tag[data-pay]", (e) => {
			const pay = $(e.currentTarget).data("pay");
			$app
				.find(`.ptl-card-payment[data-name="${pay}"]`)
				.addClass("ptl-highlight");
		});
		$app.on("mouseleave", ".ptl-alloc-tag[data-pay]", (e) => {
			const pay = $(e.currentTarget).data("pay");
			$app
				.find(`.ptl-card-payment[data-name="${pay}"]`)
				.removeClass("ptl-highlight");
		});

		$app.on("mouseenter", ".ptl-alloc-tag[data-inv]", (e) => {
			const inv = $(e.currentTarget).data("inv");
			$app
				.find(`.ptl-card-invoice[data-name="${inv}"]`)
				.addClass("ptl-highlight");
		});
		$app.on("mouseleave", ".ptl-alloc-tag[data-inv]", (e) => {
			const inv = $(e.currentTarget).data("inv");
			$app
				.find(`.ptl-card-invoice[data-name="${inv}"]`)
				.removeClass("ptl-highlight");
		});

		$app.on("click", ".ptl-card", (e) => {
			if ($(e.target).closest(".ptl-btn-receipt, .ptl-alloc-tag").length) return;
			const $card = $(e.currentTarget);
			const doctype = $card.data("doctype");
			const name = $card.data("name");
			if (doctype && name) frappe.set_route("Form", doctype, name);
		});
	}

	show_receipt(voucher_name) {
		const files = this.attachments[voucher_name];
		if (!files || files.length === 0) return;

		const $app = this.page.main.find("#payment-timeline-app");
		const $lb = $app.find("#ptl-lightbox");
		$app.find("#ptl-lb-title").text(`Comprobante — ${voucher_name}`);

		let body_html = "";
		files.forEach((f) => {
			const url = f.file_url;
			const ext = (f.file_type || "").toUpperCase();
			if (["JPG", "JPEG", "PNG", "GIF", "WEBP"].includes(ext)) {
				body_html += `<div class="ptl-receipt-item"><img src="${url}" alt="${this.escape(f.file_name)}" /></div>`;
			} else if (ext === "PDF") {
				body_html += `<div class="ptl-receipt-item"><iframe src="${url}" frameborder="0"></iframe><a href="${url}" target="_blank" class="ptl-pdf-link">Abrir PDF en nueva pestaña ↗</a></div>`;
			} else {
				body_html += `<div class="ptl-receipt-item"><a href="${url}" target="_blank" class="ptl-file-link">${this.escape(f.file_name)} ↗</a></div>`;
			}
		});

		$app.find("#ptl-lb-body").html(body_html);
		$lb.show();
	}
}
