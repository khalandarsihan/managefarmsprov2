# managefarmspro/managefarmspro/overrides/customer.py

import frappe
from frappe import _

def get_dashboard_data(data):
    return {
        "fieldname": "customer",
        "non_standard_fieldnames": {
            "Payment Entry": "party",
            "Quotation": "party_name",
            "Plot": "customer_name"
        },
        "transactions": [
            {
                "label":"",
                "items": [
                    "Plot",
                    "Quotation",
                    "Project",
                    "Work",
                    "Sales Invoice",
                    "Payment Entry"
                ]
            }
        ]
    }