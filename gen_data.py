import csv
import json
import os

# Output directory for data files
DATA_DIR = "./data/synthetic_docs"
os.makedirs(DATA_DIR, exist_ok=True)

print(f"Generating synthetic dataset in '{DATA_DIR}'...")

# ==========================================
# 1. ORDERS & REFUNDS (CSV Files)
# ==========================================

orders_data = [
    ["order_id", "customer_id", "product_name", "order_date", "amount_usd", "status", "department"],
    ["ORD-2026-8801", "CUST-101", "Apex Pro Laptop 15", "2026-03-01", "1299.00", "Refunded", "Sales"],
    ["ORD-2026-8802", "CUST-102", "Apex Pro Laptop 15", "2026-03-02", "1299.00", "Refunded", "Sales"],
    ["ORD-2026-8803", "CUST-103", "ErgoDesk Chair", "2026-03-02", "349.50", "Delivered", "Sales"],
    ["ORD-2026-8804", "CUST-104", "Apex Pro Laptop 15", "2026-03-05", "1299.00", "Refunded", "Sales"],
    ["ORD-2026-8805", "CUST-105", "UltraWide Monitor 34", "2026-03-06", "699.00", "Delivered", "Sales"],
    ["ORD-2026-8806", "CUST-106", "Apex Pro Laptop 15", "2026-03-08", "1299.00", "Completed", "Sales"],
]

with open(f"{DATA_DIR}/orders_march_2026.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(orders_data)

refunds_data = [
    ["refund_id", "order_id", "refund_date", "refund_amount", "reason_code", "department"],
    ["RF-9901", "ORD-2026-8801", "2026-03-10", "1299.00", "DEFECT_OVERHEATING", "Finance"],
    ["RF-9902", "ORD-2026-8802", "2026-03-11", "1299.00", "DEFECT_POWER_FAULT", "Finance"],  # Inconsistency: Ticket says $1350 compensation
    ["RF-9904", "ORD-2026-8804", "2026-03-14", "1299.00", "DEFECT_OVERHEATING", "Finance"],
]

with open(f"{DATA_DIR}/refunds_march_2026.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(refunds_data)

# ==========================================
# 2. CUSTOMER SUPPORT TICKETS (JSON Files)
# ==========================================

tickets = [
    {
        "ticket_id": "TICK-401",
        "order_id": "ORD-2026-8801",
        "customer_id": "CUST-101",
        "date_created": "2026-03-09",
        "department": "Customer Support",
        "issue_type": "Hardware Defect",
        "subject": "Laptop shut down spontaneously and won't turn back on",
        "description": "My Apex Pro Laptop started smoking near the charging port and shut down. Requesting immediate full refund.",
        "status": "Resolved",
        "flagged_component": "NovaCart Power Module Model-V2",
        "resolution": "Full refund issued via RF-9901."
    },
    {
        "ticket_id": "TICK-402",
        "order_id": "ORD-2026-8802",
        "customer_id": "CUST-102",
        "date_created": "2026-03-10",
        "department": "Customer Support",
        "issue_type": "Hardware Defect",
        "subject": "Power supply overheating on Apex Pro",
        "description": "Laptop gets dangerously hot. Demanding refund and store voucher.",
        "status": "Resolved",
        "flagged_component": "NovaCart Power Module Model-V2",
        "compensation_issued_usd": 1350.00,  # Inconsistency with CSV refund amount ($1299)
        "resolution": "Refunded $1299 plus $51 goodwill store credit."
    },
    {
        "ticket_id": "TICK-403",
        "order_id": None,  # Inconsistency: Missing Field
        "customer_id": "CUST-104",
        "date_created": "2026-03-12",
        "department": "Customer Support",
        "issue_type": "Hardware Defect",
        "subject": "Apex Pro Laptop total power failure",
        "description": "Unit completely dead after 3 days of use.",
        "status": "In Progress",
        "flagged_component": "NovaCart Power Module Model-V2",
        "resolution": "Escalated to Quality Engineering."
    }
]

for ticket in tickets:
    with open(f"{DATA_DIR}/ticket_{ticket['ticket_id'].lower()}.json", "w", encoding="utf-8") as f:
        json.dump(ticket, f, indent=2)

# ==========================================
# 3. SUPPLIER QUALITY & LOGISTICS (Markdown & CSV)
# ==========================================

qc_report = """# Supplier Incident & Quality Control Audit
**Document ID:** QC-2026-Q1-08  
**Department:** Quality Engineering / Supply Chain  
**Date:** February 24, 2026  
**Supplier Name:** NovaCart Global (Supplier ID: SUP-VOLT-88)  
**Component:** Power Module Model-V2 (Used in Apex Pro Laptop line)  

## Executive Summary
During regular batch testing on Lot #VT-2026-02B, Quality Control identified a 14.2% failure rate in thermal management capacitors supplied by NovaCart. 

## Key Findings
1. Substandard dielectric material used in capacitor production led to rapid thermal degradation under load.
2. Affected units were shipped to assembly plants between February 1, 2026, and February 18, 2026.
3. Recommended Action: Issue a quarantine on all uninstalled Model-V2 modules and alert Procurement.
"""

with open(f"{DATA_DIR}/supplier_qc_NovaCart.md", "w", encoding="utf-8") as f:
    f.write(qc_report)

shipment_logs = [
    ["shipment_id", "supplier_id", "carrier", "origin_warehouse", "dispatch_date", "status", "notes", "department"],
    ["SH-771", "SUP-VOLT-88", "GlobalExpress", "Shenzhen", "2026-02-05", "Delivered", "Batch Lot #VT-2026-02B", "Logistics"],
    ["SH-772", "SUP-VOLT-88", "GlobalExpress", "Shenzhen", "2026-02-20", "Delayed", "Held at customs due to missing compliance declaration", "Logistics"],
    ["SH-801", "SUP-LOGI-12", "SwiftFreight", "Frankfurt", "2026-03-01", "Delivered", "ErgoDesk frames", "Logistics"],
]

with open(f"{DATA_DIR}/shipment_logs_feb_mar_2026.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(shipment_logs)

warehouse_log = """# Internal Warehouse Incident Log
**Warehouse:** Central Fulfillment Center (Hub East)
**Date:** March 3, 2026
**Logged By:** Marcus Vance (Operations Lead)
**Department:** Operations

**Incident Summary:**
Quarantined 450 units of NovaCart Power Module Model-V2 (Lot #VT-2026-02B) following QC Notice QC-2026-Q1-08. Replacement stock requested from secondary supplier (PowerGrid Systems), but lead time is estimated at 3 weeks. Expected bottleneck in Apex Pro Laptop assembly throughout March 2026.
"""

with open(f"{DATA_DIR}/warehouse_quarantine_log.txt", "w", encoding="utf-8") as f:
    f.write(warehouse_log)

# ==========================================
# 4. POLICIES & INTERNAL EMAILS (Markdown & TXT)
# ==========================================

outdated_policy = """# Standard Customer Refund and Return Policy
**Policy ID:** POL-CUST-2024-V1  
**Effective Date:** January 1, 2024  
**Status:** ARCHIVED / OUTDATED  
**Department:** Operations / Customer Support  

## Standard Terms
1. Customers may return unused products within **14 days** of delivery for a full refund.
2. Returns past 14 days will only be issued store credit.
3. Proof of purchase is required for all claims.
"""

with open(f"{DATA_DIR}/refund_policy_2024_v1.md", "w", encoding="utf-8") as f:
    f.write(outdated_policy)

active_policy_email = """From: executive-office@c1.com
To: support-all@c1.com, finance-leads@c1.com
Date: March 8, 2026
Subject: URGENT: Extended Refund Window for Apex Pro Laptop Hardware Issues
Department: Executive / Customer Support

Team,

Due to ongoing hardware issues identified with power components in the Apex Pro Laptop 15 line, we are temporarily expanding our standard refund window.

Effective immediately:
- Any customer experiencing power failure or overheating on the Apex Pro Laptop is eligible for a FULL cash refund within 45 days of purchase (overriding the legacy 14-day policy POL-CUST-2024-V1).
- Support agents are authorized to add up to $75 in store credit for high-friction customer disputes.

Please override standard auto-rejections for these cases.

Best,
Elena Rostova
VP of Customer Experience
"""

with open(f"{DATA_DIR}/email_exec_policy_override.txt", "w", encoding="utf-8") as f:
    f.write(active_policy_email)

# ==========================================
# 5. MARKETING & OTHER DEPARTMENTS
# ==========================================

marketing_doc = """# Q1 Marketing Campaign Summary: Apex Pro Launch
**Department:** Marketing
**Date:** January 15, 2026
**Campaign ID:** MKT-2026-APEX

## Objectives & Spend
- Total Ad Spend: $120,000 across LinkedIn, Google Search, and Tech Media.
- Core Value Proposition: "Unmatched performance, ultra-cool thermal engineering."
- Projected Q1 Units Sold: 5,000 units.

## Performance Note (Added March 15, 2026)
Campaign paused mid-March due to high product return rates stemming from component overheating.
"""

with open(f"{DATA_DIR}/marketing_campaign_q1_2026.md", "w", encoding="utf-8") as f:
    f.write(marketing_doc)

confluence_doc = """# C1 Technical Architecture - Inventory Sync System
**Space:** Engineering / Integration
**Last Updated:** February 10, 2026
**Author:** Tech Stack Migration Team

## Systems Overview
- ERP: SAP S/4HANA (Source of truth for purchase orders)
- CRM: Salesforce Service Cloud (Customer support records)
- E-Commerce: Custom Storefront integrated with Dynamics 365

## Known Data Gaps
- Support tickets in Salesforce currently do not mandate a valid `order_id` link if submitted via the guest portal (resulting in null order fields in downstream analytics).
- Supplier codes in SAP use prefix `SUP-`, while legacy Dynamics records omit the prefix.
"""

with open(f"{DATA_DIR}/confluence_data_dictionary.md", "w", encoding="utf-8") as f:
    f.write(confluence_doc)

print(" Successfully created 15 synthetic files in ./data/synthetic_docs/")