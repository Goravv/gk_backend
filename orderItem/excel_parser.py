import pandas as pd

# Map expected columns with possible variants
COLUMN_MAP = {
    'part_no': ['Part No.', 'Part No', 'PartNo', 'part_no'],
    'description': ['Description', 'desc', 'description'],
    'qty': ['Qty', 'Quantity', 'qty'],
    'mrp': ['MRP', 'Mrp', 'mrp'],
    'total_amt_mrp': ['Total Amt. MRP', 'Total Amount MRP', 'total_amt_mrp'],
    'tax_percent': ['Tax %', 'Tax Percent', 'Tax%', 'tax_percent'],
    'hsn': ['HSN', 'hsn'],
    'billed_qty': ['Billed Qty', 'Billed Quantity', 'billed_qty'],
    'total_amt_billed_qty': ['Total Amt. Billed Qty', 'Total Amount Billed Qty', 'total_amt_billed_qty'],
}

def find_column(df, possible_names):
    for name in possible_names:
        if name in df.columns:
            return name
    return None

def parse_excel_file(file):
    df = pd.read_excel(file)

    # Normalize columns by mapping to model fields
    data = []
    for idx, row in df.iterrows():
        item = {}

        # Required fields
        for key in ['part_no', 'description', 'qty']:
            col_name = find_column(df, COLUMN_MAP[key])
            if not col_name:
                raise ValueError(f"Required column '{key}' is missing in the Excel file.")
            item[key] = row[col_name]

        # Optional fields
        for key in ['mrp', 'total_amt_mrp', 'tax_percent', 'hsn', 'billed_qty', 'total_amt_billed_qty']:
            col_name = find_column(df, COLUMN_MAP[key])
            item[key] = row[col_name] if col_name in df.columns else None

        # Skip rows without part_no
        if pd.isna(item['part_no']):
            continue

        data.append(item)

    return data
