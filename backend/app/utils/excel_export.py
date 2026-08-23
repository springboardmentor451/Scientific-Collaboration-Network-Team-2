import io

from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.models.publication import Publication


def publications_to_excel(db: Session) -> io.BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Publications"

    headers = ["ID", "Title", "Type", "Status", "Year", "Venue", "DOI", "Authors"]
    ws.append(headers)

    publications = db.query(Publication).all()
    for pub in publications:
        authors = ", ".join(a.name for a in pub.authors)
        ws.append(
            [
                pub.id,
                pub.title,
                pub.publication_type.value if pub.publication_type else "",
                pub.status.value if pub.status else "",
                pub.year,
                pub.venue,
                pub.doi,
                authors,
            ]
        )

    for col in ws.columns:
        max_len = max((len(str(c.value)) for c in col if c.value is not None), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 60)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
