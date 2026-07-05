# Power BI Workspace

Connect Power BI Desktop to the PostgreSQL database using the views in `sql/powerbi_views.sql`.

Start with `POWER_BI_GUIDE.md`. It documents:

- Connection steps for PostgreSQL/Neon
- Required SQL views
- Recommended data model and relationships
- DAX measures
- Dashboard pages and visuals
- Slicers and refresh strategy
- Troubleshooting

Do not generate the `SmartBI_Dashboard.pbix` file automatically. Build it manually in Power BI Desktop from the documented reporting views.
