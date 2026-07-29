# C1 Technical Architecture - Inventory Sync System
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
