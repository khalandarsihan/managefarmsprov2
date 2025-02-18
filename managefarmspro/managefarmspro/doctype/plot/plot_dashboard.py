def get_data():
	return {
		"fieldname": "plot",  # The linking field in the Work Doctype
		"non_standard_fieldnames": {
			"Work": "plot",  # Ensures that the 'plot' link field is defined in Work Doctype
		},
		"transactions": [
			{
				"items": ["Work"],  # Include all linked Doctypes here
			}
		],
	}
