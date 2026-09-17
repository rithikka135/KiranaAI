from app.documents.invoice_generator import generate_invoice_pdf


pdf_path = generate_invoice_pdf(12)

print("Invoice generated successfully!")
print("PDF:", pdf_path)