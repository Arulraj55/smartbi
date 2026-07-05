const SmartBiTables = (() => {
  const pageSize = 10;

  function sortRows(rows, column, direction = 'asc') {
    const multiplier = direction === 'asc' ? 1 : -1;
    return [...rows].sort((left, right) => String(left[column] ?? '').localeCompare(String(right[column] ?? ''), undefined, { numeric: true }) * multiplier);
  }

  function paginateRows(rows, page = 1) {
    const startIndex = (page - 1) * pageSize;
    return rows.slice(startIndex, startIndex + pageSize);
  }

  function filterRows(rows, searchTerm) {
    const normalizedSearch = String(searchTerm || '').toLowerCase();
    if (!normalizedSearch) {
      return rows;
    }
    return rows.filter((row) => Object.values(row).some((value) => String(value ?? '').toLowerCase().includes(normalizedSearch)));
  }

  function exportCsv(rows, fileName = 'smartbi_export.csv') {
    if (!rows.length) {
      return;
    }
    const headers = Object.keys(rows[0]);
    const csvContent = [headers.join(','), ...rows.map((row) => headers.map((header) => JSON.stringify(row[header] ?? '')).join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    downloadBlob(blob, fileName);
  }

  function exportExcel(rows, fileName = 'smartbi_export.xlsx') {
    if (!rows.length || typeof XLSX === 'undefined') {
      return;
    }
    const workbook = XLSX.utils.book_new();
    const worksheet = XLSX.utils.json_to_sheet(rows);
    XLSX.utils.book_append_sheet(workbook, worksheet, 'SmartBI');
    XLSX.writeFile(workbook, fileName);
  }

  function downloadBlob(blob, fileName) {
    const link = document.createElement('a');
    const objectUrl = URL.createObjectURL(blob);
    link.href = objectUrl;
    link.download = fileName;
    link.click();
    URL.revokeObjectURL(objectUrl);
  }

  return { sortRows, paginateRows, filterRows, exportCsv, exportExcel };
})();