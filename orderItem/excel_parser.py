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
    import pandas as pd

    try:
        df = pd.read_excel(file)
    except Exception as e:
        raise ValueError("Invalid Excel file")

    required_columns = ['part_no', 'description', 'qty']  # adjust if you have more columns

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    items_data = []
    for _, row in df.iterrows():
        part_no = row.get('part_no')
        description = row.get('description')
        qty = row.get('qty')

        # ✅ Skip only if part_no or qty is missing (not if qty == 0)
        if pd.isna(part_no) or pd.isna(qty):
            continue

        items_data.append({
            'part_no': str(part_no).strip(),
            'description': str(description).strip() if pd.notna(description) else '',
            'qty': int(qty),  # Allows 0
        })

    return items_data
