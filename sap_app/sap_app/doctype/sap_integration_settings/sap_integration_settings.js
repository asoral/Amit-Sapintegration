// Copyright (c) 2026, kanchan and contributors
// For license information, please see license.txt

frappe.ui.form.on("SAP Integration Settings", {
    refresh(frm) {
        // Fetch Sales Register Preview
        frm.add_custom_button(__("Fetch Data"), () => {
            frm.call({
                method: "get_sap_data",
                doc: frm.doc,
                callback: (r) => {
                    if (r.message && r.message.length > 0) {
                        show_preview_dialog(r.message, "SAP Sales Register Data Preview (JSON)");
                    } else {
                        frappe.msgprint(__("No data found or error fetching data."));
                    }
                }
            });
        }, __("Actions"));

        // Insert Sales Register Data
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

        // Fetch Payments Preview
        frm.add_custom_button(__("Fetch Payments"), () => {
            frm.call({
                method: "get_sap_payment_data",
                doc: frm.doc,
                callback: (r) => {
                    if (r.message && r.message.length > 0) {
                        show_preview_dialog(r.message, "SAP Payment Data Preview (JSON)");
                    } else {
                        frappe.msgprint(__("No payment data found or error fetching data."));
                    }
                }
            });
        }, __("Actions"));

        // Sync Payments Data
        frm.add_custom_button(__("Sync Payments"), () => {
            frappe.confirm(__("Are you sure you want to sync payments from SAP?"), () => {
                frm.call({
                    method: "process_sap_payment_data_manual",
                    doc: frm.doc,
                    freeze: true,
                    callback: (r) => {
                        if (r.message && r.message.status === "success") {
                            frappe.msgprint({
                                title: __("SAP Payments Processed"),
                                indicator: "green",
                                message: `
                                    <p>${r.message.message}</p>
                                    <ul>
                                        <li><b>${__("Created")}:</b> ${r.message.created}</li>
                                        <li><b>${__("Updated")}:</b> ${r.message.updated}</li>
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

function show_preview_dialog(data, title) {
    let json_html = `<pre style="max-height: 400px; overflow-y: auto; background-color: #f4f4f4; padding: 10px; border-radius: 4px; font-size: 12px;">${JSON.stringify(data, null, 2)}</pre>`;

    let d = new frappe.ui.Dialog({
        title: __(title || "SAP Data Preview (JSON)"),
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
