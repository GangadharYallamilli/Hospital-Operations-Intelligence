import os
import PyPDF2

PDF_FOLDER = "member2/documents/original"

SEARCH_TERMS = [
    "admissions",
    "beds",
    "occupancy",
    "waiting",
    "patients",
    "emergency",
    "outpatient",
    "quality",
    "staff",
    "performance"
]

for filename in os.listdir(PDF_FOLDER):

    if not filename.lower().endswith(".pdf"):
        continue

    filepath = os.path.join(PDF_FOLDER, filename)

    print("\n" + "=" * 80)
    print(filename)
    print("=" * 80)

    try:
        with open(filepath, "rb") as file:

            reader = PyPDF2.PdfReader(file)

            full_text = ""

            for page in reader.pages:
                full_text += (page.extract_text() or "").lower()

            for term in SEARCH_TERMS:

                count = full_text.count(term)

                print(f"{term:15} : {count}")

    except Exception as e:
        print("ERROR:", e)