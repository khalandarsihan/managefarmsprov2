from frappe import _

def get_dashboard_data(data):
    return {
        "fieldname": "sales_invoice",
        "non_standard_fieldnames": {
            "Payment Entry": "reference_name",
        },
        "transactions": [
            {
                "items": ["Payment Entry"],
            }
        ],
    }