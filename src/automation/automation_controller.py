"""
Automation controller for orchestrating AI operations.

This module provides the main controller that coordinates between
Google Sheets operations and AI platform interactions.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from ..utils.logger import get_logger
from ..sheets.sheets_manager import SheetsManager
from .browser_manager import BrowserManager
from .retry_manager import RetryManager
from .base_handler import BaseAIHandler
from .chatgpt_handler import ChatGPTHandler


class ProcessingStatus(Enum):
    """Status of processing operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class ProcessingTask:
    """Data class for processing tasks."""
    row_index: int
    copy_column: int
    processing_column: int
    error_column: int
    paste_column: int
    text_to_process: str
    ai_platform: str
    ai_model: str
    ai_settings: Dict[str, Any]
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    result: Optional[str] = None


class AutomationController:
    """
    Main controller for AI automation operations.
    
    This class orchestrates the entire automation process, coordinating
    between Google Sheets operations and AI platform interactions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the automation controller.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # Initialize managers
        self.sheets_manager = None
        self.browser_manager = None
        self.retry_manager = RetryManager(self.logger)
        
        # AI handlers
        self.ai_handlers: Dict[str, BaseAIHandler] = {}
        
        # Processing state
        self.current_spreadsheet_url = None
        self.current_sheet_name = None
        self.work_instruction_row = None
        self.copy_columns = []
        self.processing_tasks: List[ProcessingTask] = []
        
        # Statistics
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "skipped_tasks": 0,
            "start_time": None,
            "end_time": None
        }
        
        # Callbacks for GUI updates
        self.progress_callback: Optional[Callable[[int, int, str], None]] = None
        self.log_callback: Optional[Callable[[str, str], None]] = None
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Set callback for progress updates."""
        self.progress_callback = callback
    
    def set_log_callback(self, callback: Callable[[str, str], None]):
        """Set callback for log messages."""
        self.log_callback = callback
    
    def _log_message(self, level: str, message: str):
        """Log message and send to callback if available."""
        if level.lower() == "info":
            self.logger.info(message)
        elif level.lower() == "warning":
            self.logger.warning(message)
        elif level.lower() == "error":
            self.logger.error(message)
        else:
            self.logger.debug(message)
        
        if self.log_callback:
            self.log_callback(level, message)
    
    def _update_progress(self, current: int, total: int, status: str):
        """Update progress and send to callback if available."""
        if self.progress_callback:
            self.progress_callback(current, total, status)
    
    def initialize_sheets_manager(self, credentials_path: str) -> bool:
        """
        Initialize Google Sheets manager.
        
        Args:
            credentials_path: Path to Google API credentials
            
        Returns:
            bool: True if initialization successful
        """
        try:
            self.sheets_manager = SheetsManager(credentials_path)
            self._log_message("info", "Google Sheets manager initialized successfully")
            return True
        except Exception as e:
            self._log_message("error", f"Failed to initialize Sheets manager: {str(e)}")
            return False
    
    def initialize_browser_manager(self, headless: bool = False) -> bool:
        """
        Initialize browser manager.
        
        Args:
            headless: Whether to run browser in headless mode
            
        Returns:
            bool: True if initialization successful
        """
        try:
            self.browser_manager = BrowserManager(headless=headless)
            driver = self.browser_manager.get_driver()
            if driver:
                self._log_message("info", "Browser manager initialized successfully")
                return True
            else:
                self._log_message("error", "Failed to get browser driver")
                return False
        except Exception as e:
            self._log_message("error", f"Failed to initialize browser manager: {str(e)}")
            return False
    
    def setup_ai_handler(self, platform: str, settings: Dict[str, Any]) -> bool:
        """
        Setup AI handler for a specific platform.
        
        Args:
            platform: AI platform name
            settings: Platform-specific settings
            
        Returns:
            bool: True if setup successful
        """
        try:
            if not self.browser_manager:
                self._log_message("error", "Browser manager not initialized")
                return False
            
            driver = self.browser_manager.get_driver()
            
            if platform.lower() == "chatgpt":
                handler = ChatGPTHandler(driver, self.logger)
            else:
                self._log_message("error", f"Unsupported AI platform: {platform}")
                return False
            
            # Login to the platform
            if not handler.login():
                self._log_message("error", f"Failed to login to {platform}")
                return False
            
            # Configure settings
            if not handler.configure_settings(settings):
                self._log_message("warning", f"Some settings could not be configured for {platform}")
            
            self.ai_handlers[platform.lower()] = handler
            self._log_message("info", f"AI handler for {platform} setup successfully")
            return True
            
        except Exception as e:
            self._log_message("error", f"Failed to setup {platform} handler: {str(e)}")
            return False
    
    def load_spreadsheet(self, url: str, sheet_name: str) -> bool:
        """
        Load and analyze spreadsheet structure.
        
        Args:
            url: Google Sheets URL
            sheet_name: Sheet name to work with
            
        Returns:
            bool: True if loading successful
        """
        try:
            if not self.sheets_manager:
                self._log_message("error", "Sheets manager not initialized")
                return False
            
            self._log_message("info", f"Loading spreadsheet: {url}")
            self._log_message("info", f"Sheet name: {sheet_name}")
            
            # Extract spreadsheet ID from URL
            spreadsheet_id = self.sheets_manager.extract_spreadsheet_id(url)
            if not spreadsheet_id:
                self._log_message("error", "Invalid spreadsheet URL")
                return False
            
            # Set current spreadsheet
            self.current_spreadsheet_url = url
            self.current_sheet_name = sheet_name
            
            # Find work instruction row (row with "作業" in column A)
            self.work_instruction_row = self._find_work_instruction_row(spreadsheet_id, sheet_name)
            if not self.work_instruction_row:
                self._log_message("error", "Could not find work instruction row ('作業' in column A)")
                return False
            
            self._log_message("info", f"Work instruction row found at row {self.work_instruction_row}")
            
            # Find copy columns
            self.copy_columns = self._find_copy_columns(spreadsheet_id, sheet_name, self.work_instruction_row)
            if not self.copy_columns:
                self._log_message("error", "No 'コピー' columns found in work instruction row")
                return False
            
            self._log_message("info", f"Found {len(self.copy_columns)} copy columns: {self.copy_columns}")
            
            return True
            
        except Exception as e:
            self._log_message("error", f"Failed to load spreadsheet: {str(e)}")
            return False
    
    def _find_work_instruction_row(self, spreadsheet_id: str, sheet_name: str) -> Optional[int]:
        """Find the row containing '作業' in column A."""
        try:
            # Search in first 20 rows
            range_name = f"{sheet_name}!A1:A20"
            values = self.sheets_manager.read_range(spreadsheet_id, range_name)
            
            if values:
                for i, row in enumerate(values):
                    if row and len(row) > 0 and row[0] == "作業":
                        return i + 1  # 1-based row number
            
            return None
            
        except Exception as e:
            self._log_message("error", f"Error finding work instruction row: {str(e)}")
            return None
    
    def _find_copy_columns(self, spreadsheet_id: str, sheet_name: str, instruction_row: int) -> List[int]:
        """Find columns containing 'コピー' in the instruction row."""
        try:
            # Read the entire instruction row (assuming max 50 columns)
            range_name = f"{sheet_name}!{instruction_row}:{instruction_row}"
            values = self.sheets_manager.read_range(spreadsheet_id, range_name)
            
            copy_columns = []
            if values and len(values) > 0:
                row = values[0]
                for i, cell in enumerate(row):
                    if cell == "コピー":
                        copy_columns.append(i + 1)  # 1-based column number
            
            return copy_columns
            
        except Exception as e:
            self._log_message("error", f"Error finding copy columns: {str(e)}")
            return []
    
    def analyze_processing_tasks(self, ai_configs: Dict[int, Dict[str, Any]]) -> bool:
        """
        Analyze and create processing tasks.
        
        Args:
            ai_configs: Dictionary mapping copy column to AI configuration
            
        Returns:
            bool: True if analysis successful
        """
        try:
            if not self.sheets_manager or not self.work_instruction_row:
                self._log_message("error", "Spreadsheet not loaded")
                return False
            
            spreadsheet_id = self.sheets_manager.extract_spreadsheet_id(self.current_spreadsheet_url)
            self.processing_tasks = []
            
            # Find data rows (rows with numbers in column A)
            data_rows = self._find_data_rows(spreadsheet_id, self.current_sheet_name)
            
            for row_index in data_rows:
                for copy_column in self.copy_columns:
                    if copy_column not in ai_configs:
                        continue
                    
                    # Calculate related columns
                    processing_column = copy_column - 2
                    error_column = copy_column - 1
                    paste_column = copy_column + 1
                    
                    # Validate column positions
                    if processing_column < 1:
                        self._log_message("warning", f"Invalid processing column for copy column {copy_column}")
                        continue
                    
                    # Check if processing is needed
                    if not self._needs_processing(spreadsheet_id, self.current_sheet_name, 
                                                 row_index, processing_column):
                        continue
                    
                    # Get text to process
                    text_to_process = self._get_cell_text(spreadsheet_id, self.current_sheet_name,
                                                        row_index, copy_column)
                    if not text_to_process:
                        continue
                    
                    # Create processing task
                    ai_config = ai_configs[copy_column]
                    task = ProcessingTask(
                        row_index=row_index,
                        copy_column=copy_column,
                        processing_column=processing_column,
                        error_column=error_column,
                        paste_column=paste_column,
                        text_to_process=text_to_process,
                        ai_platform=ai_config.get("platform", "chatgpt"),
                        ai_model=ai_config.get("model", "GPT-4"),
                        ai_settings=ai_config.get("settings", {})
                    )
                    
                    self.processing_tasks.append(task)
            
            self.stats["total_tasks"] = len(self.processing_tasks)
            self._log_message("info", f"Created {len(self.processing_tasks)} processing tasks")
            return len(self.processing_tasks) > 0
            
        except Exception as e:
            self._log_message("error", f"Failed to analyze processing tasks: {str(e)}")
            return False
    
    def _find_data_rows(self, spreadsheet_id: str, sheet_name: str) -> List[int]:
        """Find rows with numeric values in column A."""
        try:
            # Read column A (assuming max 1000 rows)
            range_name = f"{sheet_name}!A:A"
            values = self.sheets_manager.read_range(spreadsheet_id, range_name)
            
            data_rows = []
            if values:
                for i, row in enumerate(values):
                    if row and len(row) > 0:
                        try:
                            # Try to convert to int
                            int(row[0])
                            data_rows.append(i + 1)  # 1-based row number
                        except ValueError:
                            # If conversion fails, check if it's empty (end of data)
                            if not row[0]:
                                break
            
            return data_rows
            
        except Exception as e:
            self._log_message("error", f"Error finding data rows: {str(e)}")
            return []
    
    def _needs_processing(self, spreadsheet_id: str, sheet_name: str, 
                         row: int, processing_column: int) -> bool:
        """Check if a row needs processing."""
        try:
            cell_value = self._get_cell_text(spreadsheet_id, sheet_name, row, processing_column)
            return not cell_value or cell_value.lower() in ["", "未処理"]
        except Exception:
            return True
    
    def _get_cell_text(self, spreadsheet_id: str, sheet_name: str, 
                      row: int, column: int) -> str:
        """Get text from a specific cell."""
        try:
            # Convert column number to letter
            column_letter = self._column_number_to_letter(column)
            range_name = f"{sheet_name}!{column_letter}{row}"
            
            values = self.sheets_manager.read_range(spreadsheet_id, range_name)
            if values and len(values) > 0 and len(values[0]) > 0:
                return str(values[0][0])
            return ""
        except Exception:
            return ""
    
    def _column_number_to_letter(self, column_number: int) -> str:
        """Convert column number to Excel-style letter."""
        result = ""
        while column_number > 0:
            column_number -= 1
            result = chr(column_number % 26 + ord('A')) + result
            column_number //= 26
        return result
    
    def execute_automation(self) -> bool:
        """
        Execute the automation process.
        
        Returns:
            bool: True if execution completed successfully
        """
        try:
            if not self.processing_tasks:
                self._log_message("error", "No processing tasks available")
                return False
            
            self.stats["start_time"] = time.time()
            self._log_message("info", f"Starting automation with {len(self.processing_tasks)} tasks")
            
            # Group tasks by AI platform for efficiency
            tasks_by_platform = {}
            for task in self.processing_tasks:
                platform = task.ai_platform.lower()
                if platform not in tasks_by_platform:
                    tasks_by_platform[platform] = []
                tasks_by_platform[platform].append(task)
            
            # Process tasks by platform
            for platform, tasks in tasks_by_platform.items():
                if platform not in self.ai_handlers:
                    self._log_message("error", f"No handler available for platform: {platform}")
                    for task in tasks:
                        task.status = ProcessingStatus.ERROR
                        task.error_message = f"No handler for platform {platform}"
                        self.stats["failed_tasks"] += 1
                    continue
                
                self._process_platform_tasks(platform, tasks)
            
            self.stats["end_time"] = time.time()
            self._update_processing_status()
            
            # Generate summary
            self._generate_execution_summary()
            
            return True
            
        except Exception as e:
            self._log_message("error", f"Automation execution failed: {str(e)}")
            return False
    
    def _process_platform_tasks(self, platform: str, tasks: List[ProcessingTask]):
        """Process tasks for a specific AI platform."""
        handler = self.ai_handlers[platform]
        
        for i, task in enumerate(tasks):
            try:
                self._log_message("info", f"Processing task {i+1}/{len(tasks)} for {platform}")
                self._update_progress(
                    sum(1 for t in self.processing_tasks if t.status == ProcessingStatus.COMPLETED) + i,
                    len(self.processing_tasks),
                    f"Processing {platform} task {i+1}/{len(tasks)}"
                )
                
                task.status = ProcessingStatus.IN_PROGRESS
                
                # Update processing status in sheet
                self._update_cell_value(task.row_index, task.processing_column, "処理中")
                
                # Configure handler for this task
                if not handler.configure_settings(task.ai_settings):
                    self._log_message("warning", f"Could not configure all settings for task")
                
                # Process the text
                def process_operation():
                    return handler.process_text(task.text_to_process)
                
                success, result, error_msg = self.retry_manager.execute_with_retry(
                    process_operation,
                    f"process_text_{platform}",
                    {"row": task.row_index, "column": task.copy_column}
                )
                
                if success and result:
                    task.status = ProcessingStatus.COMPLETED
                    task.result = result
                    self.stats["completed_tasks"] += 1
                    
                    # Update sheets
                    self._update_cell_value(task.row_index, task.processing_column, "処理済み")
                    self._update_cell_value(task.row_index, task.paste_column, result)
                    self._log_message("info", f"Task completed successfully")
                    
                else:
                    task.status = ProcessingStatus.ERROR
                    task.error_message = error_msg or "Unknown error"
                    self.stats["failed_tasks"] += 1
                    
                    # Update error in sheet
                    self._update_cell_value(task.row_index, task.error_column, task.error_message)
                    self._log_message("error", f"Task failed: {task.error_message}")
                
            except Exception as e:
                task.status = ProcessingStatus.ERROR
                task.error_message = str(e)
                self.stats["failed_tasks"] += 1
                
                self._update_cell_value(task.row_index, task.error_column, str(e))
                self._log_message("error", f"Task processing error: {str(e)}")
    
    def _update_cell_value(self, row: int, column: int, value: str):
        """Update a cell value in the spreadsheet."""
        try:
            if not self.sheets_manager:
                return
            
            spreadsheet_id = self.sheets_manager.extract_spreadsheet_id(self.current_spreadsheet_url)
            column_letter = self._column_number_to_letter(column)
            range_name = f"{self.current_sheet_name}!{column_letter}{row}"
            
            self.sheets_manager.update_range(spreadsheet_id, range_name, [[value]])
            
        except Exception as e:
            self._log_message("error", f"Failed to update cell {row},{column}: {str(e)}")
    
    def _update_processing_status(self):
        """Update processing status for all tasks."""
        try:
            if not self.sheets_manager:
                return
            
            spreadsheet_id = self.sheets_manager.extract_spreadsheet_id(self.current_spreadsheet_url)
            
            # Batch update for efficiency
            updates = []
            for task in self.processing_tasks:
                if task.status == ProcessingStatus.COMPLETED:
                    processing_column = self._column_number_to_letter(task.processing_column)
                    updates.append({
                        'range': f"{self.current_sheet_name}!{processing_column}{task.row_index}",
                        'values': [["処理済み"]]
                    })
            
            if updates:
                # Note: This would require implementing batch_update in SheetsManager
                # For now, we'll use individual updates
                pass
                
        except Exception as e:
            self._log_message("error", f"Failed to update processing status: {str(e)}")
    
    def _generate_execution_summary(self):
        """Generate and log execution summary."""
        duration = self.stats["end_time"] - self.stats["start_time"]
        
        summary = f"""
Automation Execution Summary:
============================
Total Tasks: {self.stats['total_tasks']}
Completed: {self.stats['completed_tasks']}
Failed: {self.stats['failed_tasks']}
Skipped: {self.stats['skipped_tasks']}
Success Rate: {(self.stats['completed_tasks'] / self.stats['total_tasks'] * 100):.1f}%
Duration: {duration:.1f} seconds

Retry Statistics:
{self.retry_manager.get_retry_statistics()}
        """
        
        self._log_message("info", summary)
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            if self.browser_manager:
                self.browser_manager.quit_driver()
                self._log_message("info", "Browser manager cleaned up")
        except Exception as e:
            self._log_message("error", f"Cleanup error: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current automation status."""
        return {
            "spreadsheet_url": self.current_spreadsheet_url,
            "sheet_name": self.current_sheet_name,
            "work_instruction_row": self.work_instruction_row,
            "copy_columns": self.copy_columns,
            "total_tasks": len(self.processing_tasks),
            "stats": self.stats,
            "ai_handlers": list(self.ai_handlers.keys()),
            "retry_stats": self.retry_manager.get_retry_statistics()
        }