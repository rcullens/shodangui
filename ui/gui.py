import sys
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextEdit, QLabel, QTableWidget,
    QTableWidgetItem, QSplitter, QHeaderView, QTabWidget, QMessageBox,
    QListWidget, QListWidgetItem
)
from core.generator import AIDorkGenerator
from core.validator import ShodanValidator
from core.executor import ExploitExecutor

CYBER_STYLE = """
QMainWindow {
    background-color: #0b0f19;
}
QWidget {
    color: #00ffcc;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
}
QLineEdit, QTextEdit, QListWidget {
    background-color: #121826;
    border: 1px solid #00ffcc;
    border-radius: 4px;
    color: #00ffcc;
    padding: 6px;
}
QLineEdit:focus, QTextEdit:focus, QListWidget:focus {
    border: 1px solid #ff007f;
    background-color: #1a2233;
}
QListWidget::item:selected {
    background-color: #ff007f;
    color: #0b0f19;
}
QPushButton {
    background-color: #121826;
    border: 1px solid #ff007f;
    color: #ff007f;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #ff007f;
    color: #0b0f19;
}
QTableWidget {
    background-color: #121826;
    border: 1px solid #00ffcc;
    gridline-color: #1a2233;
    color: #00ffcc;
}
QHeaderView::section {
    background-color: #1a2233;
    color: #ff007f;
    padding: 5px;
    border: 1px solid #00ffcc;
    font-weight: bold;
}
QTableWidget::item:selected {
    background-color: #ff007f;
    color: #0b0f19;
}
QTabWidget::pane {
    border: 1px solid #00ffcc;
    background-color: #0b0f19;
}
QTabBar::tab {
    background-color: #121826;
    color: #00ffcc;
    padding: 8px 16px;
    border: 1px solid #00ffcc;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #ff007f;
    color: #0b0f19;
    font-weight: bold;
}
"""

class ScanWorker(QThread):
    finished_signal = pyqtSignal(dict)
    status_signal = pyqtSignal(str)

    def __init__(self, api_key, keyword, scan_type="general", model_name="llama3.2"):
        super().__init__()
        self.api_key = api_key
        self.keyword = keyword
        self.scan_type = scan_type
        self.model_name = model_name

    def run(self):
        self.status_signal.emit(f"[*] Asking AI ({self.model_name}) to forge custom dorks...")
        ai_gen = AIDorkGenerator(model_name=self.model_name)
        dorks = ai_gen.generate_dorks(self.keyword, category=self.scan_type)
        
        self.status_signal.emit(f"[*] Generated {len(dorks)} custom dorks. Validating via Shodan...")
        validator = ShodanValidator(self.api_key)
        results_map = {}
        
        for idx, dork in enumerate(dorks, 1):
            self.status_signal.emit(f"[*] Probing dork [{idx}/{len(dorks)}]: {dork}")
            hits = validator.test_dork(dork)
            if hits:
                results_map[dork] = hits
                
        self.finished_signal.emit(results_map)
        self.status_signal.emit("[+] Scan complete. Select a query to view targets.")

class CyberDorkGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SHODAN // AI DORK FORGE v7.0 (AI MSF PLAYBOOK)")
        self.resize(1250, 850)
        self.setStyleSheet(CYBER_STYLE)
        
        self.general_results = {}
        self.sql_results = {}
        self.current_selected_target = None
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        config_layout = QHBoxLayout()
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("SHODAN API KEY")
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.model_input = QLineEdit("llama3.2")
        self.model_input.setPlaceholderText("Ollama Model (e.g. llama3.2)")
        
        config_layout.addWidget(QLabel("API KEY:"))
        config_layout.addWidget(self.api_input, 3)
        config_layout.addWidget(QLabel("AI MODEL:"))
        config_layout.addWidget(self.model_input, 1)
        main_layout.addLayout(config_layout)
        
        self.tabs = QTabWidget()
        
        self.tab_general = QWidget()
        self.init_general_tab()
        self.tabs.addTab(self.tab_general, "AI GENERAL DORK FORGE")
        
        self.tab_sql = QWidget()
        self.init_sql_tab()
        self.tabs.addTab(self.tab_sql, "AI SQL VULN & SQLMAP")
        
        main_layout.addWidget(self.tabs)
        
        action_layout = QHBoxLayout()
        self.sqlmap_btn = QPushButton("RUN SQLMAP ON SELECTED TARGET")
        self.sqlmap_btn.clicked.connect(self.trigger_sqlmap)
        
        self.ai_playbook_btn = QPushButton("GENERATE AI MSF PLAYBOOK")
        self.ai_playbook_btn.clicked.connect(self.trigger_ai_msf_playbook)
        
        action_layout.addWidget(self.sqlmap_btn)
        action_layout.addWidget(self.ai_playbook_btn, 2)
        main_layout.addLayout(action_layout)
        
        self.target_status_label = QLabel("ACTIVE TARGET: NONE SELECTED")
        self.target_status_label.setStyleSheet("color: #00ffcc; font-weight: bold; background-color: #121826; padding: 4px; border: 1px solid #00ffcc;")
        main_layout.addWidget(self.target_status_label)
        
        self.status_label = QLabel("SYSTEM READY...")
        self.status_label.setStyleSheet("color: #ff007f; font-weight: bold;")
        main_layout.addWidget(self.status_label)

    def init_general_tab(self):
        layout = QVBoxLayout(self.tab_general)
        top_layout = QHBoxLayout()
        
        self.gen_keyword = QLineEdit()
        self.gen_keyword.setPlaceholderText("Enter keyword/system (e.g., Android point of sale systems)")
        self.gen_btn = QPushButton("FORGE & SCAN")
        self.gen_btn.clicked.connect(lambda: self.start_scan("general"))
        
        top_layout.addWidget(self.gen_keyword, 4)
        top_layout.addWidget(self.gen_btn, 1)
        layout.addLayout(top_layout)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.gen_table = QTableWidget()
        self.gen_table.setColumnCount(3)
        self.gen_table.setHorizontalHeaderLabels(["AI-Generated Dork Query", "Hits", "Status"])
        self.gen_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.gen_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.gen_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.gen_table.cellClicked.connect(lambda r, c: self.load_targets_into_list(r, "general"))
        splitter.addWidget(self.gen_table)
        
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.gen_target_list = QListWidget()
        self.gen_target_list.itemClicked.connect(self.on_target_selected)
        right_splitter.addWidget(self.gen_target_list)
        
        self.gen_inspector = QTextEdit()
        self.gen_inspector.setReadOnly(True)
        self.gen_inspector.setPlaceholderText("// Target telemetry & AI MSF playbook will render here...")
        right_splitter.addWidget(self.gen_inspector)
        right_splitter.setSizes([200, 300])
        
        splitter.addWidget(right_splitter)
        splitter.setSizes([500, 700])
        layout.addWidget(splitter)

    def init_sql_tab(self):
        layout = QVBoxLayout(self.tab_sql)
        top_layout = QHBoxLayout()
        
        self.sql_keyword = QLineEdit()
        self.sql_keyword.setPlaceholderText("Enter target application/software (e.g., POS inventory portal)")
        self.sql_btn = QPushButton("FORGE SQL VULNS")
        self.sql_btn.clicked.connect(lambda: self.start_scan("sql"))
        
        top_layout.addWidget(self.sql_keyword, 4)
        top_layout.addWidget(self.sql_btn, 1)
        layout.addLayout(top_layout)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.sql_table = QTableWidget()
        self.sql_table.setColumnCount(3)
        self.sql_table.setHorizontalHeaderLabels(["AI-Generated SQL Vector", "Hits", "Status"])
        self.sql_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.sql_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.sql_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.sql_table.cellClicked.connect(lambda r, c: self.load_targets_into_list(r, "sql"))
        splitter.addWidget(self.sql_table)
        
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.sql_target_list = QListWidget()
        self.sql_target_list.itemClicked.connect(self.on_target_selected)
        right_splitter.addWidget(self.sql_target_list)
        
        self.sql_inspector = QTextEdit()
        self.sql_inspector.setReadOnly(True)
        self.sql_inspector.setPlaceholderText("// Verified SQL telemetry and AI MSF playbook will render here...")
        right_splitter.addWidget(self.sql_inspector)
        right_splitter.setSizes([200, 300])
        
        splitter.addWidget(right_splitter)
        splitter.setSizes([500, 700])
        layout.addWidget(splitter)

    def start_scan(self, scan_type):
        api_key = self.api_input.text().strip()
        keyword = self.gen_keyword.text().strip() if scan_type == "general" else self.sql_keyword.text().strip()
        model_name = self.model_input.text().strip() or "llama3.2"
        
        if not api_key or not keyword:
            self.status_label.setText("[!] ERROR: API Key and Keyword required.")
            return
            
        if scan_type == "general":
            self.gen_btn.setEnabled(False)
            self.gen_table.setRowCount(0)
            self.gen_target_list.clear()
            self.gen_inspector.clear()
        else:
            self.sql_btn.setEnabled(False)
            self.sql_table.setRowCount(0)
            self.sql_target_list.clear()
            self.sql_inspector.clear()
        
        self.worker = ScanWorker(api_key, keyword, scan_type=scan_type, model_name=model_name)
        self.worker.status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(lambda res: self.handle_results(res, scan_type))
        self.worker.start()

    def update_status(self, message):
        self.status_label.setText(message)

    def handle_results(self, results_map, scan_type):
        if scan_type == "general":
            self.general_results = results_map
            self.gen_btn.setEnabled(True)
            self.gen_table.setRowCount(len(results_map))
            for row, (dork, hits) in enumerate(results_map.items()):
                self.gen_table.setItem(row, 0, QTableWidgetItem(dork))
                self.gen_table.setItem(row, 1, QTableWidgetItem(str(len(hits))))
                self.gen_table.setItem(row, 2, QTableWidgetItem("VERIFIED"))
        else:
            self.sql_results = results_map
            self.sql_btn.setEnabled(True)
            self.sql_table.setRowCount(len(results_map))
            for row, (dork, hits) in enumerate(results_map.items()):
                self.sql_table.setItem(row, 0, QTableWidgetItem(dork))
                self.sql_table.setItem(row, 1, QTableWidgetItem(str(len(hits))))
                self.sql_table.setItem(row, 2, QTableWidgetItem("SQL VULN"))

    def load_targets_into_list(self, row, scan_type):
        if scan_type == "general":
            item = self.gen_table.item(row, 0)
            if not item: return
            dork = item.text()
            hits = self.general_results.get(dork, [])
            target_list_widget = self.gen_target_list
            inspector = self.gen_inspector
        else:
            item = self.sql_table.item(row, 0)
            if not item: return
            dork = item.text()
            hits = self.sql_results.get(dork, [])
            target_list_widget = self.sql_target_list
            inspector = self.sql_inspector
            
        target_list_widget.clear()
        
        for idx, hit in enumerate(hits, 1):
            label = f"[{idx}] {hit['ip']}:{hit['port']} ({hit['location']} - {hit['org']})"
            list_item = QListWidgetItem(label)
            list_item.setData(Qt.ItemDataRole.UserRole, hit)
            target_list_widget.addItem(list_item)
            
        inspector.setText(f"=== QUERY LOADED ===\n{dork}\nClick any target in the list above to select active IP/Port.")

    def on_target_selected(self, item):
        hit = item.data(Qt.ItemDataRole.UserRole)
        if not hit:
            return
            
        self.current_selected_target = hit
        target_ip = hit['ip']
        target_port = hit['port']
        
        self.target_status_label.setText(f"ACTIVE TARGET: {target_ip}:{target_port} ({hit['org']})")
        
        output = f"=== SELECTED TARGET TELEMETRY ===\n"
        output += f"IP: {target_ip}\n"
        output += f"Port: {target_port}\n"
        output += f"Location: {hit['location']}\n"
        output += f"Organization: {hit['org']}\n"
        output += f"Title: {hit['title']}\n"
        output += f"Vulnerabilities: {', '.join(hit['vulns']) if hit['vulns'] else 'None Listed (Direct Exposure)'}\n\n"
        output += f"Banner Snippet:\n{hit['banner'].strip()}\n"
        
        active_inspector = self.gen_inspector if self.tabs.currentIndex() == 0 else self.sql_inspector
        active_inspector.setText(output)

    def trigger_ai_msf_playbook(self):
        if not self.current_selected_target:
            QMessageBox.warning(self, "Warning", "Please select a specific target from the target list first.")
            return
            
        model_name = self.model_input.text().strip() or "llama3.2"
        self.status_label.setText(f"[*] Asking AI ({model_name}) to forge custom MSF playbook...")
        
        playbook = ExploitExecutor.generate_msf_playbook(self.current_selected_target, model_name=model_name)
        
        active_inspector = self.gen_inspector if self.tabs.currentIndex() == 0 else self.sql_inspector
        active_inspector.append(f"\n\n=== AI METASPLOIT OPERATOR PLAYBOOK ===\n{playbook}")
        self.status_label.setText("[+] AI Metasploit playbook generated.")

    def trigger_sqlmap(self):
        if not self.current_selected_target:
            QMessageBox.warning(self, "Warning", "Please select a target from the target list first.")
            return
            
        target_ip = self.current_selected_target['ip']
        target_port = self.current_selected_target['port']
        target_url = f"http://{target_ip}:{target_port}/"
        
        self.status_label.setText(f"[*] Running sqlmap against {target_url}...")
        output = ExploitExecutor.run_sqlmap(target_url)
        
        active_inspector = self.gen_inspector if self.tabs.currentIndex() == 0 else self.sql_inspector
        active_inspector.append(f"\n\n=== SQLMAP OUTPUT ({target_ip}:{target_port}) ===\n{output}")
        self.status_label.setText("[+] sqlmap execution finished.")
