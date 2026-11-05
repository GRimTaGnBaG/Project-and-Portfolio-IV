"""Generate formal-looking but unmistakably fictional research paperwork.

Use the bundled document-authoring runtime with ReportLab and pypdfium2.
All wording and identifiers below are invented. The layout approximates generic
multi-section paperwork; it does not reproduce anyone's family document.
The scanned variant intentionally lacks text to verify the current OCR boundary.
"""
# Bring in Path from pathlib.
from pathlib import Path
# Load json for use in this module.
import json
# Load io for use in this module.
import io
# Bring in SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak from
# reportlab.platypus.
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
# Bring in getSampleStyleSheet, ParagraphStyle from reportlab.lib.styles.
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# Bring in colors from reportlab.lib.
from reportlab.lib import colors
# Bring in canvas from reportlab.pdfgen.
from reportlab.pdfgen import canvas
# Bring in ImageReader from reportlab.lib.utils.
from reportlab.lib.utils import ImageReader
# Load pypdfium2 for use in this module.
import pypdfium2 as pdfium

# Keep 1 field as root.
ROOT=Path(__file__).resolve().parents[1]
# Build the file or folder path for fixtures.
FIXTURES=ROOT/'fixtures'
# Set styles from get sample style sheet.
STYLES=getSampleStyleSheet()
# Use add on styles.
STYLES.add(ParagraphStyle(name='Clause',fontName='Times-Roman',fontSize=11,leading=16,spaceAfter=12))
# Use add on styles.
STYLES.add(ParagraphStyle(name='FormalTitle',fontName='Times-Bold',fontSize=16,leading=21,spaceAfter=18,alignment=1))
# Use add on styles.
STYLES.add(ParagraphStyle(name='FormalHeading',fontName='Times-Bold',fontSize=12,leading=17,spaceAfter=14))

# Set rule to 'Beginning 2026-11-02, Parent A has seven consecutive ov'.
RULE='Beginning 2026-11-02, Parent A has seven consecutive overnights, followed by seven consecutive overnights with Parent B. This 14-day cycle repeats.'


def page_header(c, doc):
    """Label every page, not just the cover, to prevent mistaken real-world use."""
    # Select the font used to draw the next text.
    c.setFont('Helvetica-Bold',9)
    # Use draw centred string on c.
    c.drawCentredString(306,760,'FICTIONAL TEST DOCUMENT — NOT A COURT ORDER')
    # Use set stroke color on c.
    c.setStrokeColor(colors.grey); c.line(54,749,558,749)
    # Select the font used to draw the next text.
    c.setFont('Helvetica',9)
    # Use draw string on c.
    c.drawString(54,31,'ParentVault AI | Synthetic research fixture | TEST-2026-001')
    # Use draw right string on c.
    c.drawRightString(558,31,f'Page {doc.page}')


def clause(number, title, body):
    # Return paragraph, paragraph to the caller.
    return [Paragraph(f'{number}. {title}',STYLES['FormalHeading']),Paragraph(body,STYLES['Clause'])]


def form(rows):
    # Set table from table.
    table=Table(rows,colWidths=[170,334])
    # Use set style on table.
    table.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,-1),'Times-Roman'),('FONTSIZE',(0,0),(-1,-1),10),
        ('GRID',(0,0),(-1,-1),.5,colors.HexColor('#bdbdbd')),
        ('BACKGROUND',(0,0),(0,-1),colors.HexColor('#eeeeee')),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),10),
        ('BOTTOMPADDING',(0,0),(-1,-1),10)]))
    # Return table to the caller.
    return table


def build(path, complex_case=False):
    # Initialize story as an empty list.
    story=[]
    def title(text): story.append(Paragraph(text,STYLES['FormalTitle']))
    def section(n,t,b): story.extend(clause(n,t,b))
    # Run title with the supplied input.
    title('Fictional Family Agreement Packet')
    # Add this item to the accumulating list.
    story.append(form([['Research identifier','TEST-2026-001'],['Parties','Parent A and Parent B'],
                       ['Child label','Child One — invented research label'],['Effective date','November 2, 2026'],
                       ['Purpose','Document-to-calendar software verification']]))
    # Add this item to the accumulating list.
    story.append(Spacer(1,24))
    # Run section with the supplied input.
    section('1','Status and purpose','This packet is invented solely for software testing. It has not been filed with a court, signed by a family, or prepared to provide legal advice. All labels and circumstances are fictional.')
    # Run section with the supplied input.
    section('2','Packet organization','Part I contains settlement-style administrative clauses. Part II contains the recurring overnight plan. Part III contains communication and acknowledgment forms. No address, birth date, or personal identifier is required for this research.')
    # Add this item to the accumulating list.
    story.append(PageBreak())
    # Run title with the supplied input.
    title('Part I Settlement Style Provisions')
    # Run section with the supplied input.
    section('3','Separate records','Each fictional party maintains a separate copy of routine household records. This administrative section does not allocate overnight ownership or change the recurring calendar.')
    # Run section with the supplied input.
    section('4','Personal property','Items labeled A are assigned to Parent A. Items labeled B are assigned to Parent B. These labels describe household property only and must not be interpreted as parenting-time rules.')
    # Run section with the supplied input.
    section('5','Administrative communication','Routine messages are documented in writing. The application is being evaluated on whether it can distinguish administrative language from the operative scheduling passage.')
    # Run section with the supplied input.
    section('6','Financial illustration','A hypothetical shared-cost ledger may contain illustrative amounts. No real financial figures are present, and no financial calculation is required by the document-to-calendar task.')
    # Add this item to the accumulating list.
    story.append(PageBreak())
    # Run title with the supplied input.
    title('Part II Recurring Parenting Plan')
    # Run section with the supplied input.
    section('7','Definitions','Parent A and Parent B are neutral ownership labels. An overnight is assigned to one label for each date. The anchor date identifies the first overnight in the repeating cycle.')
    # Run section with the supplied input.
    section('8','Regular residential rotation',RULE)
    # Run section with the supplied input.
    section('9','Exchange metadata','The regular exchange weekday is Monday. The regular exchange time is 18:00. These are reviewable metadata; the generated ownership table lists overnights and does not provide transportation instructions.')
    # Run section with the supplied input.
    section('10','Schedule interpretation','Read the operative rotation together with its anchor date. An isolated number or party label in another section is not a replacement for the complete schedule statement.')
    # Add this item to the accumulating list.
    story.append(PageBreak())
    # Run title with the supplied input.
    title('Part III Communication and Review')
    # Run section with the supplied input.
    section('11','Contact procedure','Parents use their agreed written communication method for routine updates. Contact addresses and telephone numbers are intentionally absent from this invented packet.')
    # Run section with the supplied input.
    section('12','Decision records','Major non-calendar decisions are recorded separately. Decision authority does not determine overnight ownership in the recurring schedule.')
    # Run section with the supplied input.
    section('13','Source verification','A reviewer should identify the specific page and passage used for the anchor date and rotation. Software must not treat an unrelated administrative paragraph as evidence for those values.')
    # Run section with the supplied input.
    section('14','Application approval','The research operator must verify extracted fields before generating a calendar. A later edit requires a new review. This describes application operation, not court approval.')
    # Handle the case where complex case is present or true.
    if complex_case:
        # Add this item to the accumulating list.
        story.append(PageBreak())
        # Run title with the supplied input.
        title('Supplement A Special Dates')
        # Run section with the supplied input.
        section('15','Holiday override','Holiday provisions override the regular residential rotation. Parent B has the fictional winter holiday on December 24 and December 25 in even-numbered years. This is an exception to the regular cycle and requires separate handling.')
        # Run section with the supplied input.
        section('16','School break ambiguity','Spring break follows the school calendar. No school calendar or break dates are attached. The application must flag missing dates instead of inventing them.')
        # Run section with the supplied input.
        section('17','Priority review','The recurring cycle alone is not a complete representation of this packet. The expected software behavior is to identify unresolved provisions and block approval until the scope is resolved.')
        # Add this item to the accumulating list.
        story.append(PageBreak())
        # Run title with the supplied input.
        title('Supplement B Illustrative Worksheet')
        # Add this item to the accumulating list.
        story.append(form([['Worksheet status','Invented supporting form — not a calculation'],['Parent A ledger label','A-LEDGER'],['Parent B ledger label','B-LEDGER'],['Income fields','Intentionally blank'],['Support result','Not calculated; not relevant to calendar generation']]))
        # Add this item to the accumulating list.
        story.append(Spacer(1,24))
        # Run section with the supplied input.
        section('18','Nonoperative numbers','Identifiers and worksheet labels in this supplement do not alter the anchor date or recurring rotation. No numeric financial fields should become dates or ownership assignments.')
    # Add this item to the accumulating list.
    story.append(PageBreak())
    # Run title with the supplied input.
    title('Acknowledgment and Test Checklist')
    # Add this item to the accumulating list.
    story.append(form([['Parent A signature','UNSIGNED — FICTIONAL'],['Parent B signature','UNSIGNED — FICTIONAL'],['Witness','NOT APPLICABLE — TEST MATERIAL'],['Court filing','NONE'],['Research review','Check the independently written fixture answer key']]))
    # Add this item to the accumulating list.
    story.append(Spacer(1,24))
    # Run section with the supplied input.
    section('19','Final notice','This document intentionally resembles formal multipart paperwork while remaining visibly fictional. It is unsuitable for filing, advice, identity verification, or real custody administration.')
    # Use build on simple doc template.
    SimpleDocTemplate(str(path),pagesize=(612,792),leftMargin=54,rightMargin=54,topMargin=65,bottomMargin=60).build(story,onFirstPage=page_header,onLaterPages=page_header)


def main():
    # Create the output directory before writing files into it.
    FIXTURES.mkdir(exist_ok=True)
    # Build the file or folder path for clean.
    clean=FIXTURES/'formal_recurring_plan.pdf'
    # Build the file or folder path for complex path.
    complex_path=FIXTURES/'formal_plan_with_exceptions.pdf'
    # Run build with the supplied input.
    build(clean); build(complex_path,True)
    # Rasterize only our invented fixture, never the user's reference. Embedding
    # full-page images creates a realistic no-text case without using private data.
    scanned=FIXTURES/'formal_recurring_plan_scanned.pdf'
    # Set c from canvas.
    c=canvas.Canvas(str(scanned),pagesize=(612,792))
    # Set source from pdf document.
    source=pdfium.PdfDocument(str(clean))
    # Process each page from source.
    for page in source:
        # Set image from to pil.
        image=page.render(scale=1.5).to_pil()
        # Set buffer from bytes io.
        buffer=io.BytesIO(); image.save(buffer,format='PNG'); buffer.seek(0)
        # Use draw image on c.
        c.drawImage(ImageReader(buffer),0,0,width=612,height=792)
        # Use show page on c.
        c.showPage()
    # Preserve the current state or write the record through its storage interface.
    c.save()
    # These answers encode the authored scenario; they are not extracted from
    # the generated PDF or copied from a model response.
    answer={'formal_recurring_plan.pdf':{'anchor_date':'2026-11-02','cycle':['A']*7+['B']*7,
              'rule_page':3,'exchange_weekday':'Monday','exchange_time':'18:00','expected':'reviewable_recurring_plan'},
            'formal_plan_with_exceptions.pdf':{'expected':'block_for_unsupported_or_missing_provisions',
              'reasons':['holiday override','school break dates missing']},
            'formal_recurring_plan_scanned.pdf':{'expected':'reject_no_readable_text','ocr_required':True}}
    # Save the text or JSON output using the requested encoding.
    (FIXTURES/'formal_fixture_answers.json').write_text(json.dumps(answer,indent=2),encoding='utf-8')
    # Print this result or output location for the research operator.
    print('Created fictional formal-layout fixtures and independent scenario answers.')


# Run the entry point only when the file is launched directly.
if __name__=='__main__': main()
