import pandas as pd
import json
import ast

# === File paths ===
main_input = "published_mv_synthetic_unitvariant_lessons_by_keystage_18_0_0.csv"
supplementary_input = "published_mv_synthetic_unitvariants_with_lesson_ids_by_keystage_18_0_0.csv"
extracted_output = "extracted_rows.csv"
supplementary_output = "extracted_rows_supplementary.csv"

# === Step 1: Read main CSV ===
df_main = pd.read_csv(main_input)

if "programme_fields" not in df_main.columns:
    raise ValueError("The main CSV does not contain a 'programme_fields' column.")

# === Step 2: Helper functions to parse fields ===
def parse_programme_fields(field_str):
    """Return dict from JSON or Python-literal string, or empty dict on failure."""
    if pd.isna(field_str):
        return {}
    try:
        return json.loads(field_str)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(field_str)
        except Exception:
            return {}

def matches_criteria(field_str):
    data = parse_programme_fields(field_str)
    return (
        data.get("year_slug") == "year-10"
        and data.get("subject_slug") == "biology"
        and data.get("examboard_slug") == "aqa"
        and data.get("tier_slug") == "foundation"
    )

def extract_field(field_str, key):
    return parse_programme_fields(field_str).get(key)

# === Step 3: Filter rows ===
filtered_df = df_main[df_main["programme_fields"].apply(matches_criteria)]

# === Step 4: Extract programme_fields values into new columns ===
filtered_df["year_slug"] = filtered_df["programme_fields"].apply(lambda x: extract_field(x, "year_slug"))
filtered_df["subject_slug"] = filtered_df["programme_fields"].apply(lambda x: extract_field(x, "subject_slug"))
filtered_df["examboard_slug"] = filtered_df["programme_fields"].apply(lambda x: extract_field(x, "examboard_slug"))
filtered_df["tier_slug"] = filtered_df["programme_fields"].apply(lambda x: extract_field(x, "tier_slug"))

# === Step 5: Deduplicate and save first CSV ===
before_dedup = len(filtered_df)
filtered_df = filtered_df.drop_duplicates()
after_dedup = len(filtered_df)

filtered_df.to_csv(extracted_output, index=False)
print(f"{before_dedup - after_dedup} duplicate rows removed from extracted data.")
print(f"{after_dedup} unique rows saved to '{extracted_output}'.")

# === Step 6: Read supplementary CSV and keep only relevant columns ===
df_supp = pd.read_csv(supplementary_input)

required_cols = ["unit_slug", "supplementary_data"]
for col in required_cols:
    if col not in df_supp.columns:
        raise ValueError(f"The supplementary CSV must contain '{col}' column.")

# Keep only needed columns and deduplicate by unit_slug
df_supp_reduced = df_supp[required_cols].drop_duplicates(subset=["unit_slug"])

# === Step 7: Merge supplementary_data with extracted CSV ===
df_extracted = pd.read_csv(extracted_output)
merged_df = df_extracted.merge(df_supp_reduced, on="unit_slug", how="left")

# === Step 8: Extract unit_order from supplementary_data ===
def extract_unit_order(field_str):
    if pd.isna(field_str):
        return None
    try:
        data = json.loads(field_str)
    except json.JSONDecodeError:
        try:
            data = ast.literal_eval(field_str)
        except Exception:
            return None
    return data.get("unit_order")

merged_df["unit_order"] = merged_df["supplementary_data"].apply(extract_unit_order)

# === Step 9: Deduplicate merged result and save final CSV ===
merged_before = len(merged_df)
merged_df = merged_df.drop_duplicates()
merged_after = len(merged_df)

merged_df.to_csv(supplementary_output, index=False)
print(f"{merged_before - merged_after} duplicate rows removed from merged data.")
print(f"{merged_after} unique rows saved to '{supplementary_output}'.")
