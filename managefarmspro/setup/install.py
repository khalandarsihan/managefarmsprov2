import frappe

def after_install():
    """Customize workspace permissions after installation"""
    try:
        # First, restrict standard workspaces to Administrator
        update_standard_workspaces()
        
        # Then handle your custom workspace
        setup_custom_workspace()
    except Exception as e:
        frappe.log_error(f"Install error: {str(e)[:200]}")  # Limit error message length

def update_standard_workspaces():
    """Restrict standard workspaces to Administrator only"""
    # List of standard workspaces to restrict
    admin_only_workspaces = [
        # Frappe workspaces
        "Tools", "Build", "Users", "Welcome", "Integrations", "Website",
        # ERPNext workspaces
        "Accounting", "Financial Reports", "Payables", "Receivables", 
        "Assets", "Buying", "CRM", "ERPNext Integrations", "Manufacturing",
        "Projects", "Quality", "Selling", "ERPNext Settings", "Home",
        "Stock", "Support"
    ]
    
    for workspace_name in admin_only_workspaces:
        try:
            if frappe.db.exists("Workspace", workspace_name):
                workspace = frappe.get_doc("Workspace", workspace_name)
                # Clear existing roles
                workspace.roles = []
                # Add Administrator role only
                workspace.append("roles", {"role": "Administrator"})
                workspace.save(ignore_permissions=True)
        except Exception as e:
            # Keep error message short
            frappe.log_error(f"Error updating {workspace_name}: {str(e)[:100]}")

def setup_custom_workspace():
    """Setup your custom workspace permissions"""
    try:
        # Check if your workspace exists before trying to modify it
        if frappe.db.exists("Workspace", "ManageFarmsPro"):
            workspace = frappe.get_doc("Workspace", "ManageFarmsPro")
            
            # Clear existing roles
            workspace.roles = []
            
            # Add roles
            workspace.append("roles", {"role": "System Manager"})
            
            # Only add Farm Manager if the role exists
            if frappe.db.exists("Role", "Farm Manager"):
                workspace.append("roles", {"role": "Farm Manager"})
                
            workspace.save(ignore_permissions=True)
            frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Error setting up custom workspace: {str(e)[:100]}")