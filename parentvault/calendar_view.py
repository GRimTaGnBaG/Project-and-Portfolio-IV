"""Paint ownership labels inside Qt's existing month-navigation widget."""
from PySide6.QtCore import QRectF,Qt
from PySide6.QtGui import QColor,QFont,QPen
from PySide6.QtWidgets import QCalendarWidget


class OwnershipCalendar(QCalendarWidget):
    """Draw only assignments from actual generated rows, using text and color."""
    def __init__(self):
        super().__init__()
        self.owners={}
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)

    def set_ownership(self,rows):
        self.owners={row['date']:row['parent'] for row in rows}
        self.updateCells()

    def paintCell(self,painter,rect,day):
        owner=self.owners.get(day.toString('yyyy-MM-dd'))
        if owner is None:
            super().paintCell(painter,rect,day)
            return
        painter.save()
        painter.fillRect(rect,QColor('white'))
        painter.setPen(QPen(QColor('#e0e8f0')));painter.drawRect(rect.adjusted(0,0,-1,-1))
        painter.setFont(QFont('Segoe UI',10));painter.setPen(QColor('#24354b'))
        painter.drawText(rect.left()+9,rect.top()+20,str(day.day()))
        chip=QRectF(rect.left()+7,rect.top()+28,max(20,rect.width()-14),24)
        painter.setPen(QPen(QColor('#c6daf8' if owner=='A' else '#f1d99c')))
        painter.setBrush(QColor('#e4efff' if owner=='A' else '#fff0c9'))
        painter.drawRoundedRect(chip,4,4)
        painter.setPen(QColor('#245caa' if owner=='A' else '#835b11'))
        painter.setFont(QFont('Segoe UI',9))
        painter.drawText(chip,Qt.AlignmentFlag.AlignCenter,'Parent '+owner)
        painter.restore()
