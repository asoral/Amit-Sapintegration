// Copyright (c) 2026, kanchan and contributors
// For license information, please see license.txt

frappe.ui.form.on("SAP Integration Settings", {
    refresh(frm) {
        
        frm.add_custom_button(__("Fetch Data"), () => {
            frm.call({
                method: "get_sap_data",
                doc: frm.doc,
                callback: (r) => {
                    if (r.message && r.message.length > 0) {
                        show_preview_dialog(r.message);
                    } else {
                        frappe.msgprint(__("No data found or error fetching data."));
                    }
                }
            });
        }, __("Actions"));

        // Insert Data Button
        frm.add_custom_button(__("Execute"), () => {
            frappe.confirm(__("Are you sure you want to insert/update data from SAP?"), () => {
                frm.call({
                    method: "insert_process_sap_data",
                    doc: frm.doc,
                    freeze: true,
                    callback: (r) => {
                        if (r.message && r.message.status === "success") {
                            frappe.msgprint({
                                title: __("SAP Data Processed"),
                                indicator: "green",
                                message: `
                                    <p>${r.message.message}</p>
                                    <ul>
                                        <li><b>${__("Created")}:</b> ${r.message.created}</li>                                        
                                    </ul>
                                `
                            });
                        }
                    }
                });
            });
        }, __("Actions"));
    },
});

function show_preview_dialog(data) {
    let json_html = `<pre style="max-height: 400px; overflow-y: auto; background-color: #f4f4f4; padding: 10px; border-radius: 4px; font-size: 12px;">${JSON.stringify(data, null, 2)}</pre>`;

    let d = new frappe.ui.Dialog({
        title: __("SAP Data Preview (JSON)"),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'preview_html',
                options: json_html
            }
        ],
        primary_action_label: __("Close"),
        primary_action() {
            d.hide();
        }
    });

    d.show();
}
