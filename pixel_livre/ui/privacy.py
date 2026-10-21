"""Privacy inspector dialog; all file reads run outside the GUI thread."""
from pathlib import Path
from html import escape
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser, QPushButton
from pixel_livre.core.privacy import LIMITATIONS, inspect_privacy


class PrivacyWorker(QThread):
    result = Signal(object)
    failed = Signal(str)

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path

    def run(self):
        try:
            self.result.emit(inspect_privacy(self.path))
        except Exception:
            self.failed.emit('Não foi possível analisar esta imagem. Verifique se o arquivo está acessível e íntegro.')


class PrivacyDialog(QDialog):
    """Keep the worker alive until completion, including Escape/window close."""
    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        self.setObjectName('privacyDialog')
        self.setWindowTitle('Raio-X da Privacidade')
        self.resize(800, 650)
        self.setMinimumSize(580, 480)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        header = QHBoxLayout()
        title = QLabel('Raio-X da Privacidade')
        title.setObjectName('title')
        header.addWidget(title)
        header.addStretch()
        badge = QLabel('Análise local')
        badge.setObjectName('badge')
        header.addWidget(badge)
        layout.addLayout(header)
        self.heading = QLabel('Analisando metadados…')
        self.heading.setObjectName('section')
        self.heading.setWordWrap(True)
        layout.addWidget(self.heading)
        filename = QLabel(path.name)
        filename.setObjectName('muted')
        filename.setTextFormat(Qt.TextFormat.PlainText)
        filename.setWordWrap(True)
        layout.addWidget(filename)
        self.details = QTextBrowser()
        self.details.setObjectName('privacyResults')
        self.details.setReadOnly(True)
        self.details.setOpenLinks(False)
        self.details.setOpenExternalLinks(False)
        self.details.setAccessibleName('Achados do Raio-X da Privacidade')
        layout.addWidget(self.details, 1)
        self.details.setPlainText('Lendo os metadados da imagem…')
        note = QLabel(LIMITATIONS)
        note.setObjectName('muted')
        note.setWordWrap(True)
        layout.addWidget(note)
        self.close_button = QPushButton('Fechar')
        self.close_button.setObjectName('primary')
        self.close_button.setMinimumWidth(110)
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.reject)
        footer = QHBoxLayout()
        assurance = QLabel('O original permanece intacto.\nNenhum arquivo é enviado.')
        assurance.setObjectName('muted')
        footer.addWidget(assurance, 1)
        footer.addWidget(self.close_button)
        layout.addLayout(footer)
        self.worker = PrivacyWorker(path, self)
        self.worker.result.connect(self.show_report)
        self.worker.failed.connect(self.show_error)
        self.worker.finished.connect(lambda: self.close_button.setEnabled(True))
        self.worker.start()

    def show_report(self, report):
        count = len(report.findings)
        self.heading.setText('Análise incompleta' if report.warnings else
                             (f'{count} campo(s) de metadados encontrado(s)' if count else
                              'Nenhum metadado reconhecido encontrado'))
        # Only our layout is HTML. File-controlled text is always escaped, so
        # metadata cannot introduce links, remote images or rich-text markup.
        sections = [f'<p style="color:#805311">{escape(warning)}</p>' for warning in report.warnings]
        category = None
        for finding in sorted(report.findings, key=lambda item: (item.category, item.field)):
            if finding.category != category:
                category = finding.category
                sections.append(f'<h3 style="color:#5365b0">{escape(category)}</h3>')
            sections.append(f'<p><b>{escape(finding.field)}</b><br>'
                            f'{escape(finding.value)}<br>'
                            f'<span style="color:#526178">{escape(finding.explanation)}</span></p>')
        if not sections:
            sections.append('<h3>Nenhum campo para exibir</h3>'
                            '<p>Não encontramos metadados reconhecidos nesta imagem.</p>'
                            '<p style="color:#526178">Isso não garante anonimato: confira também '
                            'o conteúdo visível antes de compartilhar.</p>')
        self.details.setHtml(''.join(sections))

    def show_error(self, message):
        self.heading.setText(message)
        self.details.setPlainText('A análise não foi concluída. Nenhuma conclusão sobre a privacidade deste arquivo foi gerada.')

    def reject(self):
        if not self.worker.isRunning():
            super().reject()

    def closeEvent(self, event):
        if self.worker.isRunning():
            event.ignore()
        else:
            super().closeEvent(event)
