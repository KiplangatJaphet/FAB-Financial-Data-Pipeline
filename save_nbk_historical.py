import pandas as pd
from pathlib import Path

data = [
    [2010, 12898.9, 7853.3, 6385.2, 498.6, 301.7],
    [2011, 13626.8, 8182.2, 6799.2, 540.2, 302.4],
    [2012, 16424.5, 9874.4, 9507.8, 649.9, 305.1],
]

columns = [
    "year",
    "total_assets",
    "loans_and_advances",
    "customer_deposits",
    "total_operating_income",
    "profit_attributable_to_parent"
]

df = pd.DataFrame(data, columns=columns)

df.insert(0, "bank", "NBK")
df["currency"] = "KWD"
df["unit"] = "millions"
df["source_file"] = "NBK_2012_Financial_Statements.pdf"
df["source_page"] = 2
df["source_section"] = "Important Financial Indicators"
df["source_type"] = "historical_summary"

output = Path("output/NBK_historical_financial_indicators.csv")
output.parent.mkdir(parents=True, exist_ok=True)

if output.exists():
    raise FileExistsError(f"File already exists: {output}")

df.to_csv(output, index=False)

print(f"Saved: {output}")
print(df.to_string(index=False))
