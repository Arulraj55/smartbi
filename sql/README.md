# SQL Assets

Run `schema.sql` first, then `powerbi_views.sql`.

`schema.sql` creates the SmartBI upload/clean-row tables and reporting indexes.

`powerbi_views.sql` creates Power BI-ready views for:

- Upload metadata and domain KPIs
- Row-level facts
- Placement reporting
- HR reporting
- Sales reporting
- Inventory reporting
- Attendance reporting
- Generic dataset reporting
- Backward-compatible monthly summary views

Use `powerbi/POWER_BI_GUIDE.md` for the recommended Power BI model, relationships, DAX measures, visuals, slicers, and refresh strategy.
