# File: managefarmspro/managefarmspro/utils/migrate_fields.py

import frappe
from frappe.utils import now

def migrate_all_fields():
    """
    Master migration function that calls all individual migration functions
    """
    frappe.log_error("Starting field migration process", "Migration")
    
    # Start a migration log
    migration_log = []
    migration_stats = {
        "customers_updated": 0,
        "plots_updated": 0,
        "clusters_updated": 0,
        "works_updated": 0,
        "errors": 0
    }
    
    try:
        # 1. Migrate Customer fields
        customer_results = migrate_customer_fields()
        migration_log.extend(customer_results["log"])
        migration_stats["customers_updated"] = customer_results["count"]
        
        # 2. Migrate Plot fields if needed
        plot_results = migrate_plot_fields()
        migration_log.extend(plot_results["log"])
        migration_stats["plots_updated"] = plot_results["count"]
        
        # 3. Migrate Cluster fields if needed
        cluster_results = migrate_cluster_fields()
        migration_log.extend(cluster_results["log"])
        migration_stats["clusters_updated"] = cluster_results["count"]
        
        # 4. Migrate Work fields
        work_results = migrate_work_fields()
        migration_log.extend(work_results["log"])
        migration_stats["works_updated"] = work_results["count"]
        
        # Create migration summary
        summary = f"""
        Migration Completed at {now()}
        
        Summary:
        - Customers updated: {migration_stats['customers_updated']}
        - Plots updated: {migration_stats['plots_updated']}
        - Clusters updated: {migration_stats['clusters_updated']}
        - Works updated: {migration_stats['works_updated']}
        - Errors encountered: {migration_stats['errors']}
        """
        
        migration_log.append(summary)
        
        # Save migration log to a file or database
        frappe.log_error("\n".join(migration_log), "Migration Complete")
        
        frappe.db.commit()
        return {"success": True, "stats": migration_stats, "log": migration_log}
        
    except Exception as e:
        error_msg = f"Error during migration: {str(e)}"
        migration_log.append(error_msg)
        frappe.log_error(error_msg, "Migration Error")
        migration_stats["errors"] += 1
        return {"success": False, "stats": migration_stats, "log": migration_log}


def migrate_customer_fields():
    """
    Migrate old field names to new field names in Customer DocType
    
    Old fields:
    - customer_phone -> custom_customer_phone
    - customer_email -> custom_customer_email
    - customer_since -> custom_customer_since
    - is_active_ -> custom_is_active
    - partners_tab (tab name) -> custom_partners (tab name)
    - partners_information -> custom_partners_information
    - plots_tab (tab name) -> custom_plots (tab name)
    - plot_list -> custom_plot_details
    """
    log_messages = []
    updated_count = 0
    
    log_messages.append("Starting Customer fields migration...")
    
    try:
        # Get all customers
        customers = frappe.get_all("Customer", fields=["name"])
        log_messages.append(f"Found {len(customers)} customers to process")
        
        for customer in customers:
            try:
                doc = frappe.get_doc("Customer", customer.name)
                modified = False
                
                # Map old field names to new field names
                field_mapping = {
                    "customer_phone": "custom_customer_phone",
                    "customer_email": "custom_customer_email",
                    "customer_since": "custom_customer_since",
                    "is_active_": "custom_is_active"
                }
                
                # Migrate simple fields
                for old_field, new_field in field_mapping.items():
                    if hasattr(doc, old_field) and getattr(doc, old_field):
                        if not hasattr(doc, new_field) or not getattr(doc, new_field):
                            setattr(doc, new_field, getattr(doc, old_field))
                            log_messages.append(f"Customer {customer.name}: Migrated {old_field} to {new_field}")
                            modified = True
                
                # Migrate partners child table
                if hasattr(doc, "partners_information") and doc.partners_information:
                    if not hasattr(doc, "custom_partners_information") or not doc.custom_partners_information:
                        for partner in doc.partners_information:
                            doc.append("custom_partners_information", {
                                "partner": partner.partner if hasattr(partner, "partner") else None,
                                "partner_name": partner.partner_name if hasattr(partner, "partner_name") else None,
                                "phone_number": partner.phone_number if hasattr(partner, "phone_number") else None,
                                "email": partner.email if hasattr(partner, "email") else None
                            })
                        log_messages.append(f"Customer {customer.name}: Migrated partners_information to custom_partners_information")
                        modified = True
                
                # Migrate plot child table
                if hasattr(doc, "plot_list") and doc.plot_list:
                    if not hasattr(doc, "custom_plot_details") or not doc.custom_plot_details:
                        for plot in doc.plot_list:
                            plot_data = {
                                "plot": plot.plot if hasattr(plot, "plot") else None,
                                "plot_name": plot.plot_name if hasattr(plot, "plot_name") else None,
                                "plot_area": plot.plot_area if hasattr(plot, "plot_area") else None
                            }
                            
                            # Check if "cluster" field is available
                            if hasattr(plot, "cluster"):
                                plot_data["cluster"] = plot.cluster
                                
                            doc.append("custom_plot_details", plot_data)
                        log_messages.append(f"Customer {customer.name}: Migrated plot_list to custom_plot_details")
                        modified = True
                
                # Save if modified
                if modified:
                    doc.save()
                    updated_count += 1
                    log_messages.append(f"Customer {customer.name}: Successfully saved changes")
                
            except Exception as e:
                error_msg = f"Error processing Customer {customer.name}: {str(e)}"
                log_messages.append(error_msg)
                frappe.log_error(error_msg, "Customer Migration Error")
        
        frappe.db.commit()
        log_messages.append(f"Customer migration completed. Updated {updated_count} out of {len(customers)} customers.")
        
    except Exception as e:
        error_msg = f"Error during Customer migration: {str(e)}"
        log_messages.append(error_msg)
        frappe.log_error(error_msg, "Customer Migration Error")
    
    return {"count": updated_count, "log": log_messages}


def migrate_plot_fields():
    """
    Migrate old field names to new field names in Plot DocType
    
    The main changes are from old fields like supervision_charge to supervision_charges
    """
    log_messages = []
    updated_count = 0
    
    log_messages.append("Starting Plot fields migration...")
    
    try:
        # Get all plots
        plots = frappe.get_all("Plot", fields=["name"])
        log_messages.append(f"Found {len(plots)} plots to process")
        
        for plot in plots:
            try:
                doc = frappe.get_doc("Plot", plot.name)
                modified = False
                
                # Map old field names to new field names
                field_mapping = {
                    "supervision_charge": "supervision_charges"
                }
                
                # Migrate simple fields
                for old_field, new_field in field_mapping.items():
                    if hasattr(doc, old_field) and getattr(doc, old_field):
                        if not hasattr(doc, new_field) or not getattr(doc, new_field):
                            setattr(doc, new_field, getattr(doc, old_field))
                            log_messages.append(f"Plot {plot.name}: Migrated {old_field} to {new_field}")
                            modified = True
                
                # Save if modified
                if modified:
                    doc.save()
                    updated_count += 1
                    log_messages.append(f"Plot {plot.name}: Successfully saved changes")
                
            except Exception as e:
                error_msg = f"Error processing Plot {plot.name}: {str(e)}"
                log_messages.append(error_msg)
                frappe.log_error(error_msg, "Plot Migration Error")
        
        frappe.db.commit()
        log_messages.append(f"Plot migration completed. Updated {updated_count} out of {len(plots)} plots.")
        
    except Exception as e:
        error_msg = f"Error during Plot migration: {str(e)}"
        log_messages.append(error_msg)
        frappe.log_error(error_msg, "Plot Migration Error")
    
    return {"count": updated_count, "log": log_messages}


def migrate_cluster_fields():
    """
    Migrate old field names to new field names in Cluster DocType
    
    The key changes are:
    - plots (child table) -> plot_details (child table)
    - table_bcjd (child table) -> work_details (child table)
    """
    log_messages = []
    updated_count = 0
    
    log_messages.append("Starting Cluster fields migration...")
    
    try:
        # Get all clusters
        clusters = frappe.get_all("Cluster", fields=["name"])
        log_messages.append(f"Found {len(clusters)} clusters to process")
        
        for cluster in clusters:
            try:
                doc = frappe.get_doc("Cluster", cluster.name)
                modified = False
                
                # Migrate plots child table
                if hasattr(doc, "plots") and doc.plots:
                    if not hasattr(doc, "plot_details") or not doc.plot_details:
                        for plot in doc.plots:
                            plot_data = {
                                "plot": plot.plot if hasattr(plot, "plot") else None,
                                "plot_name": plot.plot_name if hasattr(plot, "plot_name") else None,
                                "plot_area": plot.plot_area if hasattr(plot, "plot_area") else None,
                                "units": plot.units if hasattr(plot, "units") else None
                            }
                            doc.append("plot_details", plot_data)
                        log_messages.append(f"Cluster {cluster.name}: Migrated plots to plot_details")
                        modified = True
                
                # Migrate work child table
                if hasattr(doc, "table_bcjd") and doc.table_bcjd:
                    if not hasattr(doc, "work_details") or not doc.work_details:
                        for work in doc.table_bcjd:
                            work_data = {
                                "work_id": work.work_id if hasattr(work, "work_id") else None,
                                "work_name": work.work_name if hasattr(work, "work_name") else None,
                                "work_date": work.work_date if hasattr(work, "work_date") else None,
                                "status": work.status if hasattr(work, "status") else None,
                                "total_cost": work.total_cost if hasattr(work, "total_cost") else None
                            }
                            doc.append("work_details", work_data)
                        log_messages.append(f"Cluster {cluster.name}: Migrated table_bcjd to work_details")
                        modified = True
                
                # Save if modified
                if modified:
                    doc.save()
                    updated_count += 1
                    log_messages.append(f"Cluster {cluster.name}: Successfully saved changes")
                
            except Exception as e:
                error_msg = f"Error processing Cluster {cluster.name}: {str(e)}"
                log_messages.append(error_msg)
                frappe.log_error(error_msg, "Cluster Migration Error")
        
        frappe.db.commit()
        log_messages.append(f"Cluster migration completed. Updated {updated_count} out of {len(clusters)} clusters.")
        
    except Exception as e:
        error_msg = f"Error during Cluster migration: {str(e)}"
        log_messages.append(error_msg)
        frappe.log_error(error_msg, "Cluster Migration Error")
    
    return {"count": updated_count, "log": log_messages}


def migrate_work_fields():
    """
    Migrate old field names to new field names in Work DocType
    
    The key changes are:
    - work_type_name -> work_name
    - supervision_charges -> supervision_charges (format change)
    """
    log_messages = []
    updated_count = 0
    
    log_messages.append("Starting Work fields migration...")
    
    try:
        # Get all works
        works = frappe.get_all("Work", fields=["name"])
        log_messages.append(f"Found {len(works)} works to process")
        
        for work in works:
            try:
                doc = frappe.get_doc("Work", work.name)
                modified = False
                
                # Map old field names to new field names
                field_mapping = {
                    "work_type_name": "work_name",
                    "supervision_charges": "supervision_charges"  # Same name but format might be different
                }
                
                # Migrate simple fields
                for old_field, new_field in field_mapping.items():
                    if hasattr(doc, old_field) and getattr(doc, old_field):
                        if not hasattr(doc, new_field) or not getattr(doc, new_field):
                            setattr(doc, new_field, getattr(doc, old_field))
                            log_messages.append(f"Work {work.name}: Migrated {old_field} to {new_field}")
                            modified = True
                
                # Save if modified
                if modified:
                    # For submitted documents, use db_set to avoid workflow issues
                    if doc.docstatus == 1:
                        for old_field, new_field in field_mapping.items():
                            if hasattr(doc, old_field) and getattr(doc, old_field):
                                frappe.db.set_value("Work", work.name, new_field, getattr(doc, old_field))
                        log_messages.append(f"Work {work.name}: Updated submitted document using db_set")
                    else:
                        doc.save()
                        log_messages.append(f"Work {work.name}: Successfully saved changes")
                    
                    updated_count += 1
                
            except Exception as e:
                error_msg = f"Error processing Work {work.name}: {str(e)}"
                log_messages.append(error_msg)
                frappe.log_error(error_msg, "Work Migration Error")
        
        frappe.db.commit()
        log_messages.append(f"Work migration completed. Updated {updated_count} out of {len(works)} works.")
        
        # Now handle fixing any remaining work_name fields in database
        log_messages.append("Running direct SQL fix for work_name field...")
        try:
            # This ensures that any references in database directly are updated
            frappe.db.sql("""
                UPDATE `tabWork` 
                SET work_name = work_type_name 
                WHERE work_name IS NULL AND work_type_name IS NOT NULL
            """)
            frappe.db.commit()
            log_messages.append("SQL fix for work_name completed successfully")
        except Exception as e:
            error_msg = f"Error during SQL fix for work_name: {str(e)}"
            log_messages.append(error_msg)
            frappe.log_error(error_msg, "Work SQL Migration Error")
        
    except Exception as e:
        error_msg = f"Error during Work migration: {str(e)}"
        log_messages.append(error_msg)
        frappe.log_error(error_msg, "Work Migration Error")
    
    return {"count": updated_count, "log": log_messages}


# Console-friendly version of the customer migration function
def migrate_customer_console():
    """
    Version of migrate_customer_fields() that can be run directly in Frappe Console
    """
    print("Starting Customer migration...")
    
    # Find all customer records
    customers = frappe.get_all("Customer", fields=["name"])
    print(f"Found {len(customers)} customers to process")
    
    # Migration counter
    updated_count = 0
    
    for customer in customers:
        try:
            doc = frappe.get_doc("Customer", customer.name)
            modified = False
            
            # Migrate simple fields
            field_mapping = {
                "customer_phone": "custom_customer_phone",
                "customer_email": "custom_customer_email",
                "customer_since": "custom_customer_since",
                "is_active_": "custom_is_active"
            }
            
            for old_field, new_field in field_mapping.items():
                if hasattr(doc, old_field) and getattr(doc, old_field):
                    if not hasattr(doc, new_field) or not getattr(doc, new_field):
                        setattr(doc, new_field, getattr(doc, old_field))
                        modified = True
                        print(f"Updated {old_field} to {new_field} for {customer.name}")
            
            # Migrate partners child table
            if hasattr(doc, "partners_information") and doc.partners_information:
                if not hasattr(doc, "custom_partners_information") or not doc.custom_partners_information:
                    for partner in doc.partners_information:
                        doc.append("custom_partners_information", {
                            "partner": partner.partner if hasattr(partner, "partner") else None,
                            "partner_name": partner.partner_name if hasattr(partner, "partner_name") else None,
                            "phone_number": partner.phone_number if hasattr(partner, "phone_number") else None,
                            "email": partner.email if hasattr(partner, "email") else None
                        })
                    modified = True
                    print(f"Migrated partners information for {customer.name}")
            
            # Migrate plot child table
            if hasattr(doc, "plot_list") and doc.plot_list:
                if not hasattr(doc, "custom_plot_details") or not doc.custom_plot_details:
                    for plot in doc.plot_list:
                        plot_data = {
                            "plot": plot.plot if hasattr(plot, "plot") else None,
                            "plot_name": plot.plot_name if hasattr(plot, "plot_name") else None,
                            "plot_area": plot.plot_area if hasattr(plot, "plot_area") else None
                        }
                        
                        # Check if "cluster" field is available
                        if hasattr(plot, "cluster"):
                            plot_data["cluster"] = plot.cluster
                            
                        doc.append("custom_plot_details", plot_data)
                    modified = True
                    print(f"Migrated plot list for {customer.name}")
            
            # Save if modified
            if modified:
                doc.save()
                updated_count += 1
                print(f"Saved changes for {customer.name}")
        
        except Exception as e:
            print(f"Error processing {customer.name}: {str(e)}")
    
    print(f"Migration completed. Updated {updated_count} out of {len(customers)} customers.")
    frappe.db.commit()


def migrate_plot_console():
    """
    Version of migrate_plot_fields() that can be run directly in Frappe Console
    """
    print("Starting Plot migration...")
    
    # Find all plots
    plots = frappe.get_all("Plot", fields=["name"])
    print(f"Found {len(plots)} plots to process")
    
    # Migration counter
    updated_count = 0
    
    for plot in plots:
        try:
            doc = frappe.get_doc("Plot", plot.name)
            modified = False
            
            # Migrate simple fields
            field_mapping = {
                "supervision_charge": "supervision_charges"
            }
            
            for old_field, new_field in field_mapping.items():
                if hasattr(doc, old_field) and getattr(doc, old_field):
                    if not hasattr(doc, new_field) or not getattr(doc, new_field):
                        setattr(doc, new_field, getattr(doc, old_field))
                        modified = True
                        print(f"Updated {old_field} to {new_field} for {plot.name}")
            
            # Save if modified
            if modified:
                doc.save()
                updated_count += 1
                print(f"Saved changes for {plot.name}")
        
        except Exception as e:
            print(f"Error processing {plot.name}: {str(e)}")
    
    print(f"Migration completed. Updated {updated_count} out of {len(plots)} plots.")
    frappe.db.commit()


def migrate_cluster_console():
    """
    Version of migrate_cluster_fields() that can be run directly in Frappe Console
    """
    print("Starting Cluster migration...")
    
    # Find all clusters
    clusters = frappe.get_all("Cluster", fields=["name"])
    print(f"Found {len(clusters)} clusters to process")
    
    # Migration counter
    updated_count = 0
    
    for cluster in clusters:
        try:
            doc = frappe.get_doc("Cluster", cluster.name)
            modified = False
            
            # Migrate plots child table
            if hasattr(doc, "plots") and doc.plots:
                if not hasattr(doc, "plot_details") or not doc.plot_details:
                    for plot in doc.plots:
                        plot_data = {
                            "plot": plot.plot if hasattr(plot, "plot") else None,
                            "plot_name": plot.plot_name if hasattr(plot, "plot_name") else None,
                            "plot_area": plot.plot_area if hasattr(plot, "plot_area") else None,
                            "units": plot.units if hasattr(plot, "units") else None
                        }
                        doc.append("plot_details", plot_data)
                    modified = True
                    print(f"Migrated plots to plot_details for {cluster.name}")
            
            # Migrate work child table
            if hasattr(doc, "table_bcjd") and doc.table_bcjd:
                if not hasattr(doc, "work_details") or not doc.work_details:
                    for work in doc.table_bcjd:
                        work_data = {
                            "work_id": work.work_id if hasattr(work, "work_id") else None,
                            "work_name": work.work_name if hasattr(work, "work_name") else None,
                            "work_date": work.work_date if hasattr(work, "work_date") else None,
                            "status": work.status if hasattr(work, "status") else None,
                            "total_cost": work.total_cost if hasattr(work, "total_cost") else None
                        }
                        doc.append("work_details", work_data)
                    modified = True
                    print(f"Migrated table_bcjd to work_details for {cluster.name}")
            
            # Save if modified
            if modified:
                doc.save()
                updated_count += 1
                print(f"Saved changes for {cluster.name}")
        
        except Exception as e:
            print(f"Error processing {cluster.name}: {str(e)}")
    
    print(f"Migration completed. Updated {updated_count} out of {len(clusters)} clusters.")
    frappe.db.commit()


def migrate_work_console():
    """
    Version of migrate_work_fields() that can be run directly in Frappe Console
    """
    print("Starting Work migration...")
    
    # Find all works
    works = frappe.get_all("Work", fields=["name"])
    print(f"Found {len(works)} works to process")
    
    # Migration counter
    updated_count = 0
    
    for work in works:
        try:
            doc = frappe.get_doc("Work", work.name)
            modified = False
            
            # Migrate simple fields
            field_mapping = {
                "work_type_name": "work_name",
                "supervision_charges": "supervision_charges"  # Same name but format might be different
            }
            
            for old_field, new_field in field_mapping.items():
                if hasattr(doc, old_field) and getattr(doc, old_field):
                    if not hasattr(doc, new_field) or not getattr(doc, new_field):
                        setattr(doc, new_field, getattr(doc, old_field))
                        modified = True
                        print(f"Updated {old_field} to {new_field} for {work.name}")
            
            # Save if modified
            if modified:
                # For submitted documents, use db_set to avoid workflow issues
                if doc.docstatus == 1:
                    for old_field, new_field in field_mapping.items():
                        if hasattr(doc, old_field) and getattr(doc, old_field):
                            frappe.db.set_value("Work", work.name, new_field, getattr(doc, old_field))
                    print(f"Updated submitted document {work.name} using db_set")
                else:
                    doc.save()
                    print(f"Saved changes for {work.name}")
                
                updated_count += 1
        
        except Exception as e:
            print(f"Error processing {work.name}: {str(e)}")
    
    print(f"Migration completed. Updated {updated_count} out of {len(works)} works.")
    
    # Now handle fixing any remaining work_name fields in database
    print("Running direct SQL fix for work_name field...")
    try:
        # This ensures that any references in database directly are updated
        frappe.db.sql("""
            UPDATE `tabWork` 
            SET work_name = work_type_name 
            WHERE work_name IS NULL AND work_type_name IS NOT NULL
        """)
        frappe.db.commit()
        print("SQL fix for work_name completed successfully")
    except Exception as e:
        print(f"Error during SQL fix for work_name: {str(e)}")
    
    frappe.db.commit()


if __name__ == "__main__":
    # This block allows the script to be run using bench execute
    migrate_all_fields()