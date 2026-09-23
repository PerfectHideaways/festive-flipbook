Rates tables on phones
----------------------
The phone layout shows the "Rates and dates" pages as real tables. Their data lives in rates.js,
which is generated from the brochure PDF, so it always matches the PDF.

Each new edition:
  1. Put the new PDF in the site folder (same file name as PDF_URL in index.html).
  2. Run:  python tools/extract_rates.py Perfect_Hideaways_Festive_Availability_2026_27.pdf rates.js
     (needs PyMuPDF:  pip install pymupdf)
  3. Check the printed summary: table spreads, rows per page, and any "problems" line.
  4. Publish index.html, rates.js and the new page images together.

The desktop book still shows the page images, so both views need the new export.
Rates pages are found by the words "RATE PER NIGHT" in the PDF; a table that is redrawn as a picture
will be missed.
