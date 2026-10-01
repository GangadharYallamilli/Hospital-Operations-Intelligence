from backend.nexa_priority_service import get_equipment_priority


result = get_equipment_priority(
    top_n=10
)


print("STATUS:")
print(result.get("status"))

print("\nMESSAGE:")
print(result.get("message"))


print("\nRECORDS:")
print(result.get("records_processed"))


print("\nPRIORITY LIST:")

for item in result.get("priority_list", []):

    print(
        item["equipment_id"],
        "|",
        item["equipment_type"],
        "| Score:",
        item["priority_score"],
        "|",
        item["priority_level"]
    )