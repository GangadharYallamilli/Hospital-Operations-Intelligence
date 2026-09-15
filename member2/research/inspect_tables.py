import os
import pdfplumber

PDF_FOLDER = "member2/documents/original"

for filename in os.listdir(PDF_FOLDER):

    if filename.lower().endswith(".pdf"):

        filepath = os.path.join(PDF_FOLDER, filename)

        print("\n" + "=" * 80)
        print("FILE:", filename)
        print("=" * 80)

        try:
            with pdfplumber.open(filepath) as pdf:

                total_tables = 0
                pages_with_tables = 0

                for page_number, page in enumerate(pdf.pages, start=1):

                    tables = page.extract_tables()

                    if tables:
                        pages_with_tables += 1
                        total_tables += len(tables)

                        # Show only the first detected table
                        if total_tables == len(tables):

                            print("\nFirst table found on page:", page_number)

                            table = tables[0]

                            for row in table[:10]:
                                print(row)

                print("\nPages:", len(pdf.pages))
                print("Pages containing tables:", pages_with_tables)
                print("Total tables detected:", total_tables)

        except Exception as e:
            print("ERROR:", e)
            