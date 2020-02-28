from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices


class TextEdit(QTextEdit):
    """reload mousePressEvent class"""

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

    def mousePressEvent(self, me):
        # 继承父类方法
        super().mousePressEvent(me)
        url = self.anchorAt(me.pos())
        if url.endswith('.zip') or url.endswith('.gz'):
            QDesktopServices.openUrl(QUrl(url))

