"""Paint ownership labels inside Qt's existing month-navigation widget."""
# Bring in QRectF, Qt from PySide6.QtCore.
from PySide6.QtCore import QRectF,Qt
# Bring in QColor, QFont, QPen from PySide6.QtGui.
from PySide6.QtGui import QColor,QFont,QPen
# Bring in QCalendarWidget from PySide6.QtWidgets.
from PySide6.QtWidgets import QCalendarWidget


class OwnershipCalendar(QCalendarWidget):
    """Draw only assignments from actual generated rows, using text and color."""
    def __init__(self):
        # Use init on super.
        super().__init__()
        # Group the named values in owners.
        self.owners={}
        # Use set vertical header format on self.
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)

    def set_ownership(self,rows):
        # Build owners by transforming the entries from rows.
        self.owners={row['date']:row['parent'] for row in rows}
        # Request a repaint after the ownership lookup changes.
        self.updateCells()

    # Draw the owner badge on assigned dates and use Qt’s default for other dates.
    def paintCell(self,painter,rect,day):
        # Set owner from get.
        owner=self.owners.get(day.toString('yyyy-MM-dd'))
        # Handle the case where owner is no value.
        if owner is None:
            # Use paint cell on super.
            super().paintCell(painter,rect,day)
            # End this operation here.
            return
        # Preserve the current state or write the record through its storage interface.
        painter.save()
        # Use fill rect on painter.
        painter.fillRect(rect,QColor('white'))
        # Select the outline or text color for the next drawing command.
        painter.setPen(QPen(QColor('#e0e8f0')));painter.drawRect(rect.adjusted(0,0,-1,-1))
        # Select the font used to draw the next text.
        painter.setFont(QFont('Segoe UI',10));painter.setPen(QColor('#24354b'))
        # Draw the date or ownership label in the calendar cell.
        painter.drawText(rect.left()+9,rect.top()+20,str(day.day()))
        # Create the Qt rect f used for chip.
        chip=QRectF(rect.left()+7,rect.top()+28,max(20,rect.width()-14),24)
        # Select the outline or text color for the next drawing command.
        painter.setPen(QPen(QColor('#c6daf8' if owner=='A' else '#f1d99c')))
        # Select the fill color for the next shape.
        painter.setBrush(QColor('#e4efff' if owner=='A' else '#fff0c9'))
        # Use draw rounded rect on painter.
        painter.drawRoundedRect(chip,4,4)
        # Select the outline or text color for the next drawing command.
        painter.setPen(QColor('#245caa' if owner=='A' else '#835b11'))
        # Select the font used to draw the next text.
        painter.setFont(QFont('Segoe UI',9))
        # Draw the date or ownership label in the calendar cell.
        painter.drawText(chip,Qt.AlignmentFlag.AlignCenter,'Parent '+owner)
        # Restore the painter settings so they cannot affect neighboring cells.
        painter.restore()
