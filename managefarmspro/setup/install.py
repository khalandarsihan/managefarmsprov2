import frappe

def after_install():
    """Customize workspace permissions after installation"""
    # List of standard workspaces to restrict to Administrator only
    admin_only_workspaces = [
        # Frappe workspaces
        "Tools", "Build", "Users", "Welcome", "Integrations", "Website",
        # ERPNext workspaces
        "Accounting", "Financial Reports", "Payables", "Receivables", 
        "Assets", "Buying", "CRM", "ERPNext Integrations", "Manufacturing",
        "Projects", "Quality", "Selling", "ERPNext Settings", "Home",
        "Stock", "Support"
        # Add any others that need to be admin-only
    ]
    
    # Restrict standard workspaces to Administrator
    for workspace_name in admin_only_workspaces:
        try:
            workspace = frappe.get_doc("Workspace", workspace_name)
            # Clear existing roles
            workspace.roles = []
            # Add Administrator role only
            workspace.append("roles", {"role": "Administrator"})
            workspace.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Failed to update workspace {workspace_name}: {str(e)}")
    
    # Your custom workspace setup (if needed)
    try:
        # Make sure your custom workspace exists
        if frappe.db.exists("Workspace", "ManageFarmsPro"):
            workspace = frappe.get_doc("Workspace", "ManageFarmsPro")
            # Set required roles
            workspace.roles = []
            workspace.append("roles", {"role": "System Manager"})
            # Add other roles as needed
            workspace.append("roles", {"role": "Farm Manager"})
            workspace.save(ignore_permissions=True)
            frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Failed to update ManageFarmsPro workspace: {str(e)}")