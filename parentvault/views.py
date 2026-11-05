"""Build the screenshot-inspired desktop presentation without duplicating logic.

All widgets are real PySide6 controls. Page navigation and field edits connect
to MainWindow's existing document/review/storage operations. Styles change how
the application looks; they do not seed fabricated extraction or saved results.
"""
from .paths import ASSET_ROOT
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,QButtonGroup,QCalendarWidget,QCheckBox,QComboBox,QDateEdit,
    QFrame,QGridLayout,QGroupBox,QHBoxLayout,QLabel,QLineEdit,QListWidget,
    QPlainTextEdit,QPushButton,QScrollArea,QSplitter,QStackedWidget,QTableWidget,
    QVBoxLayout,QWidget,QTabWidget,
)
from PySide6.QtGui import QFont
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from .comparison import HEADERS
from .calendar_view import OwnershipCalendar

STYLE='''
QMainWindow,QWidget#workspace { background:#f3f7fb; color:#17263b; }
QWidget { font-family:"Segoe UI"; font-size:13px; color:#17263b; }
QFrame#sidebar { background:#eaf2fb; border-right:1px solid #d9e4f0; }
QLabel#brand { font-size:19px; font-weight:700; }
QLabel#heading { font-size:25px; font-weight:700; }
QLabel#subheading,QLabel#muted { color:#61738c; }
QLabel#cardTitle { font-size:15px; font-weight:650; }
QFrame#card { background:white; border:1px solid #dbe4ee; border-radius:10px; }
QPushButton { background:#fff; border:1px solid #cedbea; border-radius:6px; padding:9px 13px; }
QPushButton:hover { background:#e9f1fd; border-color:#a9c4ec; }
QPushButton:disabled { background:#edf1f6; color:#8b99ab; border-color:#e1e7ef; }
QPushButton#primary { background:#1261ed; color:white; border-color:#1261ed; font-weight:600; }
QPushButton#primary:hover { background:#0c4ecd; }
QPushButton#primary:disabled { background:#c6d5ed; color:#f7f9fc; border-color:#c6d5ed; }
QPushButton#nav { text-align:left; border:0; padding:13px 15px; background:transparent; color:#536783; }
QPushButton#nav:checked { background:#d5e7ff; color:#0754d9; font-weight:600; }
QPushButton#nav:hover { background:#dfeafa; }
QLineEdit,QComboBox,QDateEdit { background:#fff; border:1px solid #cedbea; border-radius:6px; padding:8px; }
QPlainTextEdit { background:#fff; border:1px solid #dbe4ee; border-radius:6px; padding:12px; selection-background-color:#cfe2ff; }
QLabel#notice { background:#fff7e7; color:#80561d; border:1px solid #f3d9a4; border-radius:6px; padding:12px; }
QLabel#status { background:#e9f2ff; color:#325580; border:1px solid #d4e4fa; border-radius:6px; padding:9px; }
QTableWidget { background:white; alternate-background-color:#f7faff; gridline-color:#e0e8f0; border:1px solid #dbe4ee; border-radius:5px; }
QHeaderView::section { background:#f1f6fc; border:0; border-bottom:1px solid #dbe4ee; padding:9px; color:#526b88; }
QCalendarWidget { background:white; border:1px solid #dbe4ee; border-radius:8px; }
QCalendarWidget QWidget#qt_calendar_navigationbar { background:#edf4ff; }
QCalendarWidget QToolButton { color:#244b7a; background:transparent; padding:8px; }
QGroupBox { border:1px solid #dbe4ee; border-radius:6px; margin-top:12px; padding-top:15px; }
QGroupBox::title { subcontrol-origin:margin; left:10px; }
QListWidget { border:1px solid #dbe4ee; border-radius:6px; background:white; padding:8px; }
'''


def label(text,style=None):
    widget=QLabel(text);widget.setWordWrap(True)
    if style:widget.setObjectName(style)
    return widget


def card(title):
    frame=QFrame();frame.setObjectName('card')
    layout=QVBoxLayout(frame);layout.setContentsMargins(18,16,18,18);layout.setSpacing(12)
    layout.addWidget(label(title,'cardTitle'))
    return frame,layout


def button(text,slot,primary=False):
    widget=QPushButton(text);widget.clicked.connect(slot)
    if primary:widget.setObjectName('primary')
    return widget


def page(title,subtitle):
    widget=QWidget();layout=QVBoxLayout(widget);layout.setContentsMargins(26,22,26,20);layout.setSpacing(14)
    layout.addWidget(label(title,'heading'));layout.addWidget(label(subtitle,'subheading'))
    return widget,layout


def source_view():
    widget=QPlainTextEdit();widget.setReadOnly(True)
    widget.setFont(QFont('Georgia',11));widget.setMinimumWidth(300)
    widget.setStyleSheet('font-family:Georgia; font-size:14px; padding:22px; background:white;')
    widget.setPlaceholderText('Select a text-based PDF to view its actual extracted text and page references.')
    return widget


# DEMO 02 | Connect the interface to the workflow
# The sidebar switches between five pages of the same window and session.
# Each action button calls a controller method. For example, Choose PDF opens
# a picker, while Open sample plan sends the bundled PDF to the same loader.
def build(window):
    """Attach view attributes used by the tested controller methods."""
    w=window
    w.setStyleSheet(STYLE);w.resize(1440,940);w.setMinimumSize(1100,760)
    central=QWidget();central.setObjectName('workspace');w.setCentralWidget(central)
    root=QHBoxLayout(central);root.setContentsMargins(0,0,0,0);root.setSpacing(0)
    side=QFrame();side.setObjectName('sidebar');side.setFixedWidth(215)
    sidebar=QVBoxLayout(side);sidebar.setContentsMargins(14,28,14,20);sidebar.setSpacing(7)
    sidebar.addWidget(label('ParentVault AI','brand'))
    sidebar.addWidget(label('Document to Calendar','muted'));sidebar.addSpacing(30)
    w.navigation=QButtonGroup(w);w.navigation.setExclusive(True)
    for i,name in enumerate(['Document','Review Rules','Calendar','Saved Records','Research Comparison']):
        item=QPushButton(name);item.setObjectName('nav');item.setCheckable(True)
        w.navigation.addButton(item,i);sidebar.addWidget(item)
    sidebar.addStretch()
    sidebar.addWidget(label('SAMPLE WORKSPACE\n\nUse fictional test documents. Review every rule before saving.','muted'))
    root.addWidget(side)
    workspace=QWidget();outer=QVBoxLayout(workspace);outer.setContentsMargins(0,0,0,12)
    w.tabs=QStackedWidget();outer.addWidget(w.tabs,1)
    w.status=label('Select a fictional PDF to begin.','status');outer.addWidget(w.status)
    root.addWidget(workspace,1)
    w.navigation.idClicked.connect(w.show_page)
    w.tabs.currentChanged.connect(w.page_changed)

    document,layout=page('Start with your document','Select a parenting plan, extract its schedule, then review the evidence.')
    split=QSplitter();layout.addWidget(split,1)
    frame,left=card('Document preview');w.document_source=source_view()
    w.pdf_document=QPdfDocument(w)
    w.document_pdf_view=QPdfView();w.document_pdf_view.setDocument(w.pdf_document)
    w.document_pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
    w.document_pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
    w.document_preview_tabs=QTabWidget();w.document_preview_tabs.addTab(w.document_pdf_view,'PDF preview')
    w.document_preview_tabs.addTab(w.document_source,'Extracted text')
    left.addWidget(w.document_preview_tabs,1);split.addWidget(frame)
    panel=QWidget();right=QVBoxLayout(panel);right.setContentsMargins(0,0,0,0);right.setSpacing(16)
    frame,content=card('Select a PDF');w.file_label=label('No document selected','muted');content.addWidget(w.file_label)
    w.open_button=button('Choose PDF',w.open_pdf);content.addWidget(w.open_button)
    w.sample_button=button('Open sample plan',lambda:w.load_pdf(ASSET_ROOT/'fixtures'/'formal_recurring_plan.pdf'));content.addWidget(w.sample_button)
    content.addWidget(label('Text-based PDF • Up to 10 MB • Scanned pages require OCR','muted'));right.addWidget(frame)
    frame,content=card('Extract scheduling rules')
    content.addWidget(label('Choose a method. Results are proposals until you review and approve them.','muted'))
    w.model=QLineEdit('parentvault-research');w.model.setAccessibleName('Loaded local model identifier')
    content.addWidget(label('Loaded local model'));content.addWidget(w.model)
    w.model_check_button=button('Check local model connection',w.check_model);content.addWidget(w.model_check_button)
    w.model_status=label('Connection not checked. Baseline works without LM Studio.','muted');content.addWidget(w.model_status)
    actions=QHBoxLayout();w.baseline_button=button('Baseline extraction',w.run_baseline)
    w.ai_button=button('Local model extraction',w.run_ai,True)
    actions.addWidget(w.baseline_button);actions.addWidget(w.ai_button);content.addLayout(actions)
    right.addWidget(frame)
    right.addWidget(label('The source stays local. Unsupported, incomplete, or conflicting information must be resolved before a calendar is approved.','notice'))
    right.addStretch();split.addWidget(panel);split.setSizes([560,480]);w.tabs.addWidget(document)

    review,layout=page('Review scheduling rules','Compare the proposed rules with your document before approving.')
    split=QSplitter();layout.addWidget(split,1)
    frame,left=card('Source document');w.source=source_view()
    w.review_pdf_view=QPdfView();w.review_pdf_view.setDocument(w.pdf_document)
    w.review_pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
    w.review_pdf_view.setPageMode(QPdfView.PageMode.SinglePage)
    w.review_preview_tabs=QTabWidget();w.review_preview_tabs.addTab(w.review_pdf_view,'PDF preview')
    w.review_preview_tabs.addTab(w.source,'Extracted text')
    left.addWidget(w.review_preview_tabs,1);split.addWidget(frame)
    scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.Shape.NoFrame)
    frame,right=card('Proposed rules');scroll.setWidget(frame);split.addWidget(scroll);split.setSizes([520,520])
    w.approval_badge=label('Not yet approved','muted');right.addWidget(w.approval_badge)
    form=QGridLayout();right.addLayout(form)
    w.anchor_edit=QDateEdit();w.anchor_edit.setCalendarPopup(True);w.anchor_edit.setDisplayFormat('MMM d, yyyy')
    w.anchor_edit.setDate(w.month_default_date());w.anchor_edit.setAccessibleName('Anchor date')
    form.addWidget(label('Anchor date'),0,0);form.addWidget(label('Cycle length'),0,1)
    form.addWidget(w.anchor_edit,1,0);form.addWidget(label('14 days'),1,1)
    right.addWidget(label('Overnight rotation','cardTitle'))
    grid=QGridLayout();w.cycle_edits=[]
    for i in range(14):
        owner=QComboBox();owner.addItem('A','A');owner.addItem('B','B')
        owner.setAccessibleName(f'Overnight owner for cycle day {i+1}')
        grid.addWidget(label(f'Day {i+1}'),(i//7)*2,i%7)
        grid.addWidget(owner,(i//7)*2+1,i%7);w.cycle_edits.append(owner)
        owner.currentIndexChanged.connect(w.form_edited)
    right.addLayout(grid)
    exchange=QGridLayout();right.addLayout(exchange)
    w.exchange_day=QLineEdit();w.exchange_day.setPlaceholderText('Not stated')
    w.exchange_time=QLineEdit();w.exchange_time.setPlaceholderText('Not stated')
    exchange.addWidget(label('Exchange weekday'),0,0);exchange.addWidget(label('Exchange time'),0,1)
    exchange.addWidget(w.exchange_day,1,0);exchange.addWidget(w.exchange_time,1,1)
    w.evidence_label=label('Source references appear after extraction.','muted');right.addWidget(w.evidence_label)
    w.warning_label=label('Review required: verify the anchor and rotation against the source.','notice');right.addWidget(w.warning_label)
    w.review_checkbox=QCheckBox('I have reviewed these rules and their source.');right.addWidget(w.review_checkbox)
    w.review_checkbox.toggled.connect(w.update_controls)
    w.approve_button=button('Approve reviewed rules',w.approve,True);right.addWidget(w.approve_button)
    right.addWidget(button('Back to document',lambda:w.show_page(0)))
    right.addWidget(button('Continue to calendar',lambda:w.show_page(2)))
    right.addWidget(label('Overnight assignments are not precise handoff instructions.','muted'))
    advanced=QGroupBox('Advanced structured rules');advanced.setCheckable(True);advanced.setChecked(False)
    advanced_layout=QVBoxLayout(advanced);w.rules=QPlainTextEdit();w.rules.setMinimumHeight(200)
    w.rules.setAccessibleName('Proposed scheduling rules JSON');advanced_layout.addWidget(w.rules)
    w.rules.setVisible(False);advanced.toggled.connect(w.rules.setVisible);right.addWidget(advanced)
    w.rules.textChanged.connect(w.rules_edited)
    w.anchor_edit.dateChanged.connect(w.form_edited)
    w.exchange_day.textEdited.connect(w.form_edited);w.exchange_time.textEdited.connect(w.form_edited)
    right.addStretch();w.tabs.addWidget(review)

    result,layout=page('Your parenting calendar','A monthly view generated from the reviewed 14-day rotation.')
    actions=QHBoxLayout();w.generate_button=button('Generate approved month',w.generate,True)
    w.export_button=button('Export CSV',w.export);actions.addWidget(w.generate_button);actions.addStretch();actions.addWidget(w.export_button)
    actions.addWidget(button('Save plan',lambda:w.show_page(3)));layout.addLayout(actions)
    split=QSplitter();layout.addWidget(split,1)
    frame,left=card('Monthly calendar');w.month=OwnershipCalendar();w.month.setGridVisible(True)
    w.month.currentPageChanged.connect(w.month_changed);left.addWidget(w.month,1)
    left.addWidget(label('Parent A — blue     Parent B — gold\nThe table includes text labels for every overnight.','muted'));split.addWidget(frame)
    frame,right=card('Overnight ownership');w.table=QTableWidget(0,2)
    w.table.setHorizontalHeaderLabels(['Date','Assigned to']);w.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    w.table.horizontalHeader().setStretchLastSection(True);right.addWidget(w.table,1);split.addWidget(frame)
    split.setSizes([680,350]);w.tabs.addWidget(result)

    records,layout=page('Saved records','Return to a saved plan and its source, or remove a local record.')
    frame,content=card('Save the current approved plan');row=QHBoxLayout()
    w.record_name=QLineEdit();w.record_name.setPlaceholderText('Name this fictional configuration')
    w.save_button=button('Save approved plan',w.save,True);row.addWidget(w.record_name,1);row.addWidget(w.save_button)
    content.addLayout(row);layout.addWidget(frame)
    frame,content=card('Your plans');w.record_list=QComboBox();content.addWidget(w.record_list)
    # Keep the legacy ID-backed selection internally, but use one visible table
    # as the action target so a second selector cannot bypass the search filter.
    w.record_list.hide()
    w.record_search=QLineEdit();w.record_search.setPlaceholderText('Search by plan name or filename')
    w.record_search.textChanged.connect(w.filter_records);content.insertWidget(1,w.record_search)
    w.record_table=QTableWidget(0,3);w.record_table.setHorizontalHeaderLabels(['Plan and source','Review status','Saved'])
    w.record_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    w.record_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    w.record_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    w.record_table.horizontalHeader().setStretchLastSection(True)
    w.record_table.itemSelectionChanged.connect(w.record_selected)
    content.addWidget(w.record_table)
    row=QHBoxLayout();w.load_button=button('Load for review',w.load);w.delete_button=button('Delete selected record…',w.delete)
    row.addWidget(w.load_button);row.addWidget(w.delete_button);row.addStretch();content.addLayout(row)
    content.addWidget(label('Loading a record always requires review and approval again.','notice'));layout.addWidget(frame)
    layout.addStretch();w.tabs.addWidget(records)

    comparison,layout=page('Research comparison','Run a measured extraction comparison, or review recorded experiment results.')
    frame,content=card('Recorded experiment results')
    w.comparison_label=label('No experiment results loaded.','muted');content.addWidget(w.comparison_label)
    w.compare_run_button=button('Run comparison on current document',w.run_comparison,True);content.addWidget(w.compare_run_button)
    w.compare_export_button=button('Export latest comparison',w.export_comparison);content.addWidget(w.compare_export_button)
    w.comparison_button=button('Open saved experiment results',w.choose_comparison);content.addWidget(w.comparison_button)
    w.comparison_table=QTableWidget(0,len(HEADERS));w.comparison_table.setHorizontalHeaderLabels(HEADERS)
    w.comparison_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    w.comparison_table.setWordWrap(True);w.comparison_table.horizontalHeader().setStretchLastSection(True)
    content.addWidget(w.comparison_table,1);layout.addWidget(frame,1)
    layout.addWidget(label('Run both methods on the current document, or open historical evidence. Accuracy is scored only against explicitly reviewed rules; comparison never grants approval.','notice'))
    w.tabs.addWidget(comparison);w.show_page(0)

