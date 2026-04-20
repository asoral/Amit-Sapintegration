frappe.ui.form.on('Sales Contract', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.sap_sync_status !== 'Synced') {
			frm.add_custom_button(__('Sync to SAP'), () => {
				frappe.call({
					method: 'sap_app.sap_app.api_sync.sync_sales_contracts_to_sap',
					args: {
						docname: frm.doc.name
					},
					callback: function(r) {
						if (!r.exc) {
							frappe.msgprint(__('Sync process completed. Check SAP Response for details.'));
							frm.reload_doc();
						}
					}
				});
			});
		}
	}
});

frappe.ui.form.on('Sales Contract Item', {
	qty: function(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
	},
	rate: function(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
	}
});

function calculate_item_amount(frm, cdt, cdn) {
	var child = locals[cdt][cdn];
	frappe.model.set_value(cdt, cdn, 'amount', (child.qty || 0) * (child.rate || 0));
	
	var total = 0;
	frm.doc.items.forEach(function(item) {
		total += (item.amount || 0);
	});
	frm.set_value('total_net_amount', total);
}

frappe.ui.form.on('Sales Contract Item', {
	form_render: function(frm, cdt, cdn) {
		setTimeout(() => render_pricing_table(frm, cdt, cdn), 100);
	}
});

function render_pricing_table(frm, cdt, cdn) {
	let row = frappe.get_doc(cdt, cdn);
	if (!row) return;

	let grid_row = frm.fields_dict.to_item.grid.grid_rows_by_docname[cdn];
	if (!grid_row || !grid_row.grid_form) return;

	let wrapper = grid_row.grid_form.fields_dict.pricing_elements_html.wrapper;
	
	let data = [];
	try {
		data = JSON.parse(row.pricing_elements_json || "[]");
	} catch(e) {}
	
	if (!Array.isArray(data)) data = [data];
	if (data.length === 0) {
		data.push({"ConditionType": "ZCNQ", "ConditionRateValue": "0.00", "ConditionCurrency": "INR", "ConditionQuantity": "1", "ConditionQuantityUnit": "MT"});
	}

	let html = `
		<table class="table table-bordered">
			<thead>
				<tr>
					<th>Condition Type</th>
					<th>Rate Value</th>
					<th>Currency</th>
					<th>Quantity</th>
					<th>UOM</th>
					<th></th>
				</tr>
			</thead>
			<tbody>
	`;
	
	data.forEach((d, i) => {
		html += `
			<tr>
				<td><input class="form-control pe-input" data-field="ConditionType" value="${d.ConditionType || ''}"></td>
				<td><input class="form-control pe-input" data-field="ConditionRateValue" type="number" value="${d.ConditionRateValue || ''}"></td>
				<td><input class="form-control pe-input" data-field="ConditionCurrency" value="${d.ConditionCurrency || 'INR'}"></td>
				<td><input class="form-control pe-input" data-field="ConditionQuantity" type="number" value="${d.ConditionQuantity || '1'}"></td>
				<td><input class="form-control pe-input" data-field="ConditionQuantityUnit" value="${d.ConditionQuantityUnit || 'MT'}"></td>
				<td><button class="btn btn-sm btn-danger pe-remove">X</button></td>
			</tr>
		`;
	});
	
	html += `
			</tbody>
		</table>
		<button class="btn btn-sm btn-secondary pe-add mt-2">Add Element</button>
	`;
	
	$(wrapper).html(html);
	
	$(wrapper).find('.pe-input').on('change', function() {
		update_pe_json(frm, cdt, cdn, wrapper);
	});
	
	$(wrapper).find('.pe-remove').on('click', function(e) {
		e.preventDefault();
		$(this).closest('tr').remove();
		update_pe_json(frm, cdt, cdn, wrapper);
	});
	
	$(wrapper).find('.pe-add').on('click', function(e) {
		e.preventDefault();
		let new_json = [];
		try { new_json = JSON.parse(row.pricing_elements_json || "[]"); } catch(e) {}
		if (!Array.isArray(new_json)) new_json = [new_json];
		new_json.push({"ConditionType": "ZCNQ", "ConditionRateValue": "0.00", "ConditionCurrency": "INR", "ConditionQuantity": "1", "ConditionQuantityUnit": "MT"});
		frappe.model.set_value(cdt, cdn, "pricing_elements_json", JSON.stringify(new_json, null, 2));
		render_pricing_table(frm, cdt, cdn);
	});
}

function update_pe_json(frm, cdt, cdn, wrapper) {
	let new_data = [];
	$(wrapper).find('tbody tr').each(function() {
		let tr = $(this);
		new_data.push({
			"ConditionType": tr.find('[data-field="ConditionType"]').val(),
			"ConditionRateValue": tr.find('[data-field="ConditionRateValue"]').val(),
			"ConditionCurrency": tr.find('[data-field="ConditionCurrency"]').val(),
			"ConditionQuantity": tr.find('[data-field="ConditionQuantity"]').val(),
			"ConditionQuantityUnit": tr.find('[data-field="ConditionQuantityUnit"]').val()
		});
	});
	frappe.model.set_value(cdt, cdn, 'pricing_elements_json', JSON.stringify(new_data, null, 2));
}
