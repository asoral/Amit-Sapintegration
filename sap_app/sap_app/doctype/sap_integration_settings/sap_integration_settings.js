// Copyright (c) 2026, kanchan and contributors
// For license information, please see license.txt

frappe.ui.form.on("SAP Integration Settings", {
    refresh(frm) {

        frm.add_custom_button(__("Fetch SAP Data"), () => {
            frm.call({
                method: "fetch_data_from_sap",
                doc: frm.doc,
                callback: (r) => {
                    if (r.message) {
                        if (r.message.status === "error") {
                            frappe.msgprint({
                                title: __("Error Fetching Data"),
                                indicator: "red",
                                message: r.message.message
                            });
                        } else {
                            frappe.msgprint({
                                title: __("SAP Data"),
                                indicator: "green",
                                message: `<pre style="max-height: 400px; overflow: auto; background-color: #f4f4f4; padding: 10px; border-radius: 4px;">${JSON.stringify(r.message, null, 2)}</pre>`,
                                wide: true
                            });
                        }
                    }
                }
            });
        }, __("Actions"));
    },
});
