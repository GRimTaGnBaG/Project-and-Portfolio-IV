"""Build the screenshot-inspired desktop presentation without duplicating logic.

All widgets are real PySide6 controls. Page navigation and field edits connect
to MainWindow's existing document/review/storage operations. Styles change how
the application looks; they do not seed fabricated extraction or saved results.
"""
# Bring in ASSET_ROOT from paths.
from .paths import ASSET_ROOT
# Bring in Qt from PySide6.QtCore.
from PySide6.QtCore import Qt
# Bring in QAbstractItemView, QButtonGroup, QCalendarWidget, QCheckBox, QComboBox, QDateEdit,
# QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPlainTextEdit,
# QPushButton, QScrollArea, QSplitter, QStackedWidget, QTableWidget, QVBoxLayout, QWidget,
# QTabWidget from PySide6.QtWidgets.
from PySide6.QtWidgets import (
    QAbstractItemView,QButtonGroup,QCalendarWidget,QCheckBox,QComboBox,QDateEdit,
    QFrame,QGridLayout,QGroupBox,QHBoxLayout,QLabel,QLineEdit,QListWidget,
    QPlainTextEdit,QPushButton,QScrollArea,QSplitter,QStackedWidget,QTableWidget,
    QVBoxLayout,QWidget,QTabWidget,
)
# Bring in QFont from PySide6.QtGui.
from PySide6.QtGui import QFont
# Bring in QPdfDocument from PySide6.QtPdf.
from PySide6.QtPdf import QPdfDocument
# Bring in QPdfView from PySide6.QtPdfWidgets.
from PySide6.QtPdfWidgets import QPdfView
# Bring in HEADERS from comparison.
from .comparison import HEADERS
# Bring in OwnershipCalendar from calendar_view.
from .calendar_view import OwnershipCalendar

# Set style to '\nQMainWindow,QWidget#workspace { background:#f3f7fb; co'.
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
    # Create the Qt label used for widget.
    widget=QLabel(text);widget.setWordWrap(True)
    # Handle the case where style is present or true.
    if style:widget.setObjectName(style)
    # Return widget to the caller.
    return widget


def card(title):
    # Create the Qt frame used for frame.
    frame=QFrame();frame.setObjectName('card')
    # Create the Qt vbox layout used for layout.
    layout=QVBoxLayout(frame);layout.setContentsMargins(18,16,18,18);layout.setSpacing(12)
    # Place the widget in its layout or page stack.
    layout.addWidget(label(title,'cardTitle'))
    # Return frame, layout to the caller.
    return frame,layout


def button(text,slot,primary=False):
    # Create the Qt push button used for widget.
    widget=QPushButton(text);widget.clicked.connect(slot)
    # Handle the case where primary is present or true.
    if primary:widget.setObjectName('primary')
    # Return widget to the caller.
    return widget


def page(title,subtitle):
    # Create the Qt widget used for widget.
    widget=QWidget();layout=QVBoxLayout(widget);layout.setContentsMargins(26,22,26,20);layout.setSpacing(14)
    # Place the widget in its layout or page stack.
    layout.addWidget(label(title,'heading'));layout.addWidget(label(subtitle,'subheading'))
    # Return widget, layout to the caller.
    return widget,layout


def source_view():
    # Create the Qt plain text edit used for widget.
    widget=QPlainTextEdit();widget.setReadOnly(True)
    # Select the font used to draw the next text.
    widget.setFont(QFont('Georgia',11));widget.setMinimumWidth(300)
    # Apply the widget styling for this state.
    widget.setStyleSheet('font-family:Georgia; font-size:14px; padding:22px; background:white;')
    # Show a hint when the field is empty.
    widget.setPlaceholderText('Select a text-based PDF to view its actual extracted text and page references.')
    # Return widget to the caller.
    return widget


def build(window):
    """Attach view attributes used by the tested controller methods."""
    # Build widgets on the existing controller so the event handlers can update them.
    w=window
    # Apply the widget styling for this state.
    w.setStyleSheet(STYLE);w.resize(1440,940);w.setMinimumSize(1100,760)
    # Create the Qt widget used for central.
    central=QWidget();central.setObjectName('workspace');w.setCentralWidget(central)
    # Create the Qt hbox layout used for root.
    root=QHBoxLayout(central);root.setContentsMargins(0,0,0,0);root.setSpacing(0)
    # Create the Qt frame used for side.
    side=QFrame();side.setObjectName('sidebar');side.setFixedWidth(215)
    # Create the Qt vbox layout used for sidebar.
    sidebar=QVBoxLayout(side);sidebar.setContentsMargins(14,28,14,20);sidebar.setSpacing(7)
    # Place the widget in its layout or page stack.
    sidebar.addWidget(label('ParentVault AI','brand'))
    # Place the widget in its layout or page stack.
    sidebar.addWidget(label('Document to Calendar','muted'));sidebar.addSpacing(30)
    # Create the Qt button group used for navigation.
    w.navigation=QButtonGroup(w);w.navigation.setExclusive(True)
    # Process each i, name from enumerate.
    for i,name in enumerate(['Document','Review Rules','Calendar','Saved Records','Research Comparison']):
        # Create the Qt push button used for item.
        item=QPushButton(name);item.setObjectName('nav');item.setCheckable(True)
        # Use add button on navigation.
        w.navigation.addButton(item,i);sidebar.addWidget(item)
    # Use flexible space to align the surrounding controls.
    sidebar.addStretch()
    # Place the widget in its layout or page stack.
    sidebar.addWidget(label('SAMPLE WORKSPACE\n\nUse fictional test documents. Review every rule before saving.','muted'))
    # Place the widget in its layout or page stack.
    root.addWidget(side)
    # Create the Qt widget used for workspace.
    workspace=QWidget();outer=QVBoxLayout(workspace);outer.setContentsMargins(0,0,0,12)
    # Stack the pages so navigation shows one at a time without creating a new window.
    w.tabs=QStackedWidget();outer.addWidget(w.tabs,1)
    # Set status from label.
    w.status=label('Select a fictional PDF to begin.','status');outer.addWidget(w.status)
    # Place the widget in its layout or page stack.
    root.addWidget(workspace,1)
    # Use the clicked button's ID as the index of the page to show.
    w.navigation.idClicked.connect(w.show_page)
    # Register the callback that receives this Qt signal.
    w.tabs.currentChanged.connect(w.page_changed)

    # Set document, layout from page.
    document,layout=page('Start with your document','Select a parenting plan, extract its schedule, then review the evidence.')
    # Create the Qt splitter used for split.
    split=QSplitter();layout.addWidget(split,1)
    # Set frame, left from card.
    frame,left=card('Document preview');w.document_source=source_view()
    # Create the Qt pdf document used for pdf document.
    w.pdf_document=QPdfDocument(w)
    # Create the Qt pdf view used for document pdf view.
    w.document_pdf_view=QPdfView();w.document_pdf_view.setDocument(w.pdf_document)
    # Use set zoom mode on document pdf view.
    w.document_pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
    # Use set page mode on document pdf view.
    w.document_pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
    # Create the Qt tab widget used for document preview tabs.
    w.document_preview_tabs=QTabWidget();w.document_preview_tabs.addTab(w.document_pdf_view,'PDF preview')
    # Use add tab on document preview tabs.
    w.document_preview_tabs.addTab(w.document_source,'Extracted text')
    # Place the widget in its layout or page stack.
    left.addWidget(w.document_preview_tabs,1);split.addWidget(frame)
    # Create the Qt widget used for panel.
    panel=QWidget();right=QVBoxLayout(panel);right.setContentsMargins(0,0,0,0);right.setSpacing(16)
    # Set frame, content from card.
    frame,content=card('Select a PDF');w.file_label=label('No document selected','muted');content.addWidget(w.file_label)
    # Set open button from button.
    w.open_button=button('Choose PDF',w.open_pdf);content.addWidget(w.open_button)
    # Set sample button from button.
    w.sample_button=button('Open sample plan',lambda:w.load_pdf(ASSET_ROOT/'fixtures'/'formal_recurring_plan.pdf'));content.addWidget(w.sample_button)
    # Place the widget in its layout or page stack.
    content.addWidget(label('Text-based PDF • Up to 10 MB • Scanned pages require OCR','muted'));right.addWidget(frame)
    # Set frame, content from card.
    frame,content=card('Extract scheduling rules')
    # Place the widget in its layout or page stack.
    content.addWidget(label('Choose a method. Results are proposals until you review and approve them.','muted'))
    # Create the Qt line edit used for model.
    w.model=QLineEdit('parentvault-research');w.model.setAccessibleName('Loaded local model identifier')
    # Place the widget in its layout or page stack.
    content.addWidget(label('Loaded local model'));content.addWidget(w.model)
    # Set model check button from button.
    w.model_check_button=button('Check local model connection',w.check_model);content.addWidget(w.model_check_button)
    # Set model status from label.
    w.model_status=label('Connection not checked. Baseline works without LM Studio.','muted');content.addWidget(w.model_status)
    # Create the Qt hbox layout used for actions.
    actions=QHBoxLayout();w.baseline_button=button('Baseline extraction',w.run_baseline)
    # Set ai button from button.
    w.ai_button=button('Local model extraction',w.run_ai,True)
    # Place the widget in its layout or page stack.
    actions.addWidget(w.baseline_button);actions.addWidget(w.ai_button);content.addLayout(actions)
    # Place the widget in its layout or page stack.
    right.addWidget(frame)
    # Place the widget in its layout or page stack.
    right.addWidget(label('The source stays local. Unsupported, incomplete, or conflicting information must be resolved before a calendar is approved.','notice'))
    # Use flexible space to align the surrounding controls.
    right.addStretch();split.addWidget(panel);split.setSizes([560,480]);w.tabs.addWidget(document)

    # Set review, layout from page.
    review,layout=page('Review scheduling rules','Compare the proposed rules with your document before approving.')
    # Create the Qt splitter used for split.
    split=QSplitter();layout.addWidget(split,1)
    # Set frame, left from card.
    frame,left=card('Source document');w.source=source_view()
    # Create the Qt pdf view used for review pdf view.
    w.review_pdf_view=QPdfView();w.review_pdf_view.setDocument(w.pdf_document)
    # Use set zoom mode on review pdf view.
    w.review_pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
    # Use set page mode on review pdf view.
    w.review_pdf_view.setPageMode(QPdfView.PageMode.SinglePage)
    # Create the Qt tab widget used for review preview tabs.
    w.review_preview_tabs=QTabWidget();w.review_preview_tabs.addTab(w.review_pdf_view,'PDF preview')
    # Use add tab on review preview tabs.
    w.review_preview_tabs.addTab(w.source,'Extracted text')
    # Place the widget in its layout or page stack.
    left.addWidget(w.review_preview_tabs,1);split.addWidget(frame)
    # Create the Qt scroll area used for scroll.
    scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.Shape.NoFrame)
    # Set frame, right from card.
    frame,right=card('Proposed rules');scroll.setWidget(frame);split.addWidget(scroll);split.setSizes([520,520])
    # Set approval badge from label.
    w.approval_badge=label('Not yet approved','muted');right.addWidget(w.approval_badge)
    # Create the Qt grid layout used for form.
    form=QGridLayout();right.addLayout(form)
    # Create the Qt date edit used for anchor edit.
    w.anchor_edit=QDateEdit();w.anchor_edit.setCalendarPopup(True);w.anchor_edit.setDisplayFormat('MMM d, yyyy')
    # Use set date on anchor edit.
    w.anchor_edit.setDate(w.month_default_date());w.anchor_edit.setAccessibleName('Anchor date')
    # Place the widget in its layout or page stack.
    form.addWidget(label('Anchor date'),0,0);form.addWidget(label('Cycle length'),0,1)
    # Place the widget in its layout or page stack.
    form.addWidget(w.anchor_edit,1,0);form.addWidget(label('14 days'),1,1)
    # Place the widget in its layout or page stack.
    right.addWidget(label('Overnight rotation','cardTitle'))
    # Create the Qt grid layout used for grid.
    grid=QGridLayout();w.cycle_edits=[]
    # Process each i from range.
    for i in range(14):
        # Create the Qt combo box used for owner.
        owner=QComboBox();owner.addItem('A','A');owner.addItem('B','B')
        # Provide a meaningful label to assistive technology.
        owner.setAccessibleName(f'Overnight owner for cycle day {i+1}')
        # Place the widget in its layout or page stack.
        grid.addWidget(label(f'Day {i+1}'),(i//7)*2,i%7)
        # Place the widget in its layout or page stack.
        grid.addWidget(owner,(i//7)*2+1,i%7);w.cycle_edits.append(owner)
        # Register the callback that receives this Qt signal.
        owner.currentIndexChanged.connect(w.form_edited)
    # Nest the layout inside the current section.
    right.addLayout(grid)
    # Create the Qt grid layout used for exchange.
    exchange=QGridLayout();right.addLayout(exchange)
    # Create the Qt line edit used for exchange day.
    w.exchange_day=QLineEdit();w.exchange_day.setPlaceholderText('Not stated')
    # Create the Qt line edit used for exchange time.
    w.exchange_time=QLineEdit();w.exchange_time.setPlaceholderText('Not stated')
    # Place the widget in its layout or page stack.
    exchange.addWidget(label('Exchange weekday'),0,0);exchange.addWidget(label('Exchange time'),0,1)
    # Place the widget in its layout or page stack.
    exchange.addWidget(w.exchange_day,1,0);exchange.addWidget(w.exchange_time,1,1)
    # Set evidence label from label.
    w.evidence_label=label('Source references appear after extraction.','muted');right.addWidget(w.evidence_label)
    # Set warning label from label.
    w.warning_label=label('Review required: verify the anchor and rotation against the source.','notice');right.addWidget(w.warning_label)
    # Create the Qt check box used for review checkbox.
    w.review_checkbox=QCheckBox('I have reviewed these rules and their source.');right.addWidget(w.review_checkbox)
    # Register the callback that receives this Qt signal.
    w.review_checkbox.toggled.connect(w.update_controls)
    # Set approve button from button.
    w.approve_button=button('Approve reviewed rules',w.approve,True);right.addWidget(w.approve_button)
    # Place the widget in its layout or page stack.
    right.addWidget(button('Back to document',lambda:w.show_page(0)))
    # Place the widget in its layout or page stack.
    right.addWidget(button('Continue to calendar',lambda:w.show_page(2)))
    # Place the widget in its layout or page stack.
    right.addWidget(label('Overnight assignments are not precise handoff instructions.','muted'))
    # Create the Qt group box used for advanced.
    advanced=QGroupBox('Advanced structured rules');advanced.setCheckable(True);advanced.setChecked(False)
    # Create the Qt vbox layout used for advanced layout.
    advanced_layout=QVBoxLayout(advanced);w.rules=QPlainTextEdit();w.rules.setMinimumHeight(200)
    # Provide a meaningful label to assistive technology.
    w.rules.setAccessibleName('Proposed scheduling rules JSON');advanced_layout.addWidget(w.rules)
    # Use set visible on rules.
    w.rules.setVisible(False);advanced.toggled.connect(w.rules.setVisible);right.addWidget(advanced)
    # Notify the controller when the rule text changes so prior approval is cleared.
    w.rules.textChanged.connect(w.rules_edited)
    # Register the callback that receives this Qt signal.
    w.anchor_edit.dateChanged.connect(w.form_edited)
    # Register the callback that receives this Qt signal.
    w.exchange_day.textEdited.connect(w.form_edited);w.exchange_time.textEdited.connect(w.form_edited)
    # Use flexible space to align the surrounding controls.
    right.addStretch();w.tabs.addWidget(review)

    # Set result, layout from page.
    result,layout=page('Your parenting calendar','A monthly view generated from the reviewed 14-day rotation.')
    # Create the Qt hbox layout used for actions.
    actions=QHBoxLayout();w.generate_button=button('Generate approved month',w.generate,True)
    # Set export button from button.
    w.export_button=button('Export CSV',w.export);actions.addWidget(w.generate_button);actions.addStretch();actions.addWidget(w.export_button)
    # Place the widget in its layout or page stack.
    actions.addWidget(button('Save plan',lambda:w.show_page(3)));layout.addLayout(actions)
    # Create the Qt splitter used for split.
    split=QSplitter();layout.addWidget(split,1)
    # Set frame, left from card.
    frame,left=card('Monthly calendar');w.month=OwnershipCalendar();w.month.setGridVisible(True)
    # Register the callback that receives this Qt signal.
    w.month.currentPageChanged.connect(w.month_changed);left.addWidget(w.month,1)
    # Place the widget in its layout or page stack.
    left.addWidget(label('Parent A — blue     Parent B — gold\nThe table includes text labels for every overnight.','muted'));split.addWidget(frame)
    # Set frame, right from card.
    frame,right=card('Overnight ownership');w.table=QTableWidget(0,2)
    # Name the columns so their values can be understood.
    w.table.setHorizontalHeaderLabels(['Date','Assigned to']);w.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    # Use set stretch last section on horizontal header.
    w.table.horizontalHeader().setStretchLastSection(True);right.addWidget(w.table,1);split.addWidget(frame)
    # Use set sizes on split.
    split.setSizes([680,350]);w.tabs.addWidget(result)

    # Set records, layout from page.
    records,layout=page('Saved records','Return to a saved plan and its source, or remove a local record.')
    # Set frame, content from card.
    frame,content=card('Save the current approved plan');row=QHBoxLayout()
    # Create the Qt line edit used for record name.
    w.record_name=QLineEdit();w.record_name.setPlaceholderText('Name this fictional configuration')
    # Set save button from button.
    w.save_button=button('Save approved plan',w.save,True);row.addWidget(w.record_name,1);row.addWidget(w.save_button)
    # Nest the layout inside the current section.
    content.addLayout(row);layout.addWidget(frame)
    # Set frame, content from card.
    frame,content=card('Your plans');w.record_list=QComboBox();content.addWidget(w.record_list)
    # Keep the legacy ID-backed selection internally, but use one visible table
    # as the action target so a second selector cannot bypass the search filter.
    w.record_list.hide()
    # Create the Qt line edit used for record search.
    w.record_search=QLineEdit();w.record_search.setPlaceholderText('Search by plan name or filename')
    # Register the callback that receives this Qt signal.
    w.record_search.textChanged.connect(w.filter_records);content.insertWidget(1,w.record_search)
    # Create the Qt table widget used for record table.
    w.record_table=QTableWidget(0,3);w.record_table.setHorizontalHeaderLabels(['Plan and source','Review status','Saved'])
    # Use set edit triggers on record table.
    w.record_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    # Use set selection behavior on record table.
    w.record_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    # Use set selection mode on record table.
    w.record_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    # Use set stretch last section on horizontal header.
    w.record_table.horizontalHeader().setStretchLastSection(True)
    # Register the callback that receives this Qt signal.
    w.record_table.itemSelectionChanged.connect(w.record_selected)
    # Place the widget in its layout or page stack.
    content.addWidget(w.record_table)
    # Create the Qt hbox layout used for row.
    row=QHBoxLayout();w.load_button=button('Load for review',w.load);w.delete_button=button('Delete selected record…',w.delete)
    # Place the widget in its layout or page stack.
    row.addWidget(w.load_button);row.addWidget(w.delete_button);row.addStretch();content.addLayout(row)
    # Place the widget in its layout or page stack.
    content.addWidget(label('Loading a record always requires review and approval again.','notice'));layout.addWidget(frame)
    # Use flexible space to align the surrounding controls.
    layout.addStretch();w.tabs.addWidget(records)

    # Set comparison, layout from page.
    comparison,layout=page('Research comparison','Run a measured extraction comparison, or review recorded experiment results.')
    # Set frame, content from card.
    frame,content=card('Recorded experiment results')
    # Set comparison label from label.
    w.comparison_label=label('No experiment results loaded.','muted');content.addWidget(w.comparison_label)
    # Set compare run button from button.
    w.compare_run_button=button('Run comparison on current document',w.run_comparison,True);content.addWidget(w.compare_run_button)
    # Set compare export button from button.
    w.compare_export_button=button('Export latest comparison',w.export_comparison);content.addWidget(w.compare_export_button)
    # Set comparison button from button.
    w.comparison_button=button('Open saved experiment results',w.choose_comparison);content.addWidget(w.comparison_button)
    # Create the Qt table widget used for comparison table.
    w.comparison_table=QTableWidget(0,len(HEADERS));w.comparison_table.setHorizontalHeaderLabels(HEADERS)
    # Use set edit triggers on comparison table.
    w.comparison_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    # Allow long text to wrap within the available width.
    w.comparison_table.setWordWrap(True);w.comparison_table.horizontalHeader().setStretchLastSection(True)
    # Place the widget in its layout or page stack.
    content.addWidget(w.comparison_table,1);layout.addWidget(frame,1)
    # Place the widget in its layout or page stack.
    layout.addWidget(label('Run both methods on the current document, or open historical evidence. Accuracy is scored only against explicitly reviewed rules; comparison never grants approval.','notice'))
    # Place the widget in its layout or page stack.
    w.tabs.addWidget(comparison);w.show_page(0)

