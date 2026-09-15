import os
import PyPDF2

PDF_FOLDER = "member2/documents/original"

for filename in os.listdir(PDF_FOLDER):

    if filename.lower().endswith(".pdf"):

        filepath = os.path.join(PDF_FOLDER, filename)

        print("\n" + "=" * 80)
        print("FILE:", filename)
        print("=" * 80)

        try:
            with open(filepath, "rb") as file:

                reader = PyPDF2.PdfReader(file)

                print("Pages:", len(reader.pages))

                # Extract first 5 pages
                text = ""

                for page in reader.pages[:5]:
                    page_text = page.extract_text() or ""
                    text += page_text

                print("\nFIRST 5 PAGES SAMPLE:")
                print("-" * 80)
                print(text[:5000])

        except Exception as e:
            print("ERROR:", e)