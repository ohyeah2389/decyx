# suggestion_dialog.py

from javax.swing import (
    JDialog, JPanel, JCheckBox, JButton, JScrollPane, BoxLayout, JLabel, JTextField, JTextArea, JTable
)
from javax.swing.table import DefaultTableModel
from java.awt import Dimension

from decyx.utils import find_data_type_by_name, format_new_type
from decyx.config import DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT


def show_suggestion_dialog(suggestions, variables_with_old_types, tool):
    dialog = JDialog()
    dialog.setTitle("Claude Suggestions")
    dialog.setModal(True)
    selected_suggestions = [None]

    panel = JPanel()
    panel.setLayout(BoxLayout(panel, BoxLayout.Y_AXIS))

    func_panel = JPanel()
    func_panel.setLayout(BoxLayout(func_panel, BoxLayout.X_AXIS))
    func_checkbox = JCheckBox("Rename function to:", True)
    func_name_field = JTextField(suggestions.get("function_name", ""), 24)
    func_name_field.setMaximumSize(Dimension(260, 25))
    func_panel.add(func_checkbox)
    func_panel.add(func_name_field)
    panel.add(func_panel)

    column_names = ["Old Name", "New Name", "Old Type", "New Type", "Rename", "Retype"]
    table_model = DefaultTableModel([], column_names)
    variable_table = JTable(table_model)
    old_name_to_type = {var["old_name"]: var["old_type"] for var in variables_with_old_types}
    type_validity = []

    for var in suggestions["variables"]:
        old_name = var["old_name"]
        new_name = var.get("new_name", "")
        old_type = old_name_to_type.get(old_name, "unknown")
        new_type = format_new_type(var.get("new_type", ""))
        retype_default = bool(new_type) and find_data_type_by_name(new_type, tool) is not None
        type_validity.append(retype_default)
        shown_new_type = new_type if retype_default or not new_type else "{} [INVALID]".format(new_type)
        table_model.addRow([old_name, new_name, old_type, shown_new_type, True, retype_default])

    table_scroll = JScrollPane(variable_table)
    table_scroll.setPreferredSize(Dimension(700, 300))
    panel.add(table_scroll)

    valid_retypes = sum(1 for is_valid in type_validity if is_valid)
    invalid_retypes = len(type_validity) - valid_retypes
    summary_label = JLabel(
        "<html><b>Summary:</b><br>"
        "Rename suggestions: {}/{} total variables<br>"
        "Retype suggestions: {}/{} valid, {}/{} invalid</html>".format(
            len(suggestions["variables"]),
            len(suggestions["variables"]),
            valid_retypes,
            len(type_validity),
            invalid_retypes,
            len(type_validity),
        )
    )
    panel.add(summary_label)

    select_buttons = JPanel()

    def select_all(column, value):
        for row in range(table_model.getRowCount()):
            table_model.setValueAt(value, row, column)

    select_renames = JButton("Select All Renames")
    select_renames.addActionListener(lambda _: select_all(4, True))
    unselect_renames = JButton("Unselect All Renames")
    unselect_renames.addActionListener(lambda _: select_all(4, False))
    select_retypes = JButton("Select All Retypes")
    select_retypes.addActionListener(lambda _: select_all(5, True))
    unselect_retypes = JButton("Unselect All Retypes")
    unselect_retypes.addActionListener(lambda _: select_all(5, False))
    select_buttons.add(select_renames)
    select_buttons.add(unselect_renames)
    select_buttons.add(select_retypes)
    select_buttons.add(unselect_retypes)
    panel.add(select_buttons)

    explanation_area = None
    if suggestions.get("explanation"):
        panel.add(JLabel("Explanation:"))
        explanation_area = JTextArea(suggestions["explanation"], 5, 30)
        explanation_area.setEditable(False)
        explanation_area.setLineWrap(True)
        explanation_area.setWrapStyleWord(True)
        panel.add(JScrollPane(explanation_area))

    bottom_button_panel = JPanel()

    def on_apply(_):
        selected = {"function_name": None, "variables": [], "explanation": None}
        if func_checkbox.isSelected():
            selected["function_name"] = func_name_field.getText()

        for row in range(table_model.getRowCount()):
            old_name = table_model.getValueAt(row, 0)
            new_name = table_model.getValueAt(row, 1)
            new_type = str(table_model.getValueAt(row, 3) or "").replace(" [INVALID]", "")
            rename = bool(table_model.getValueAt(row, 4))
            retype = bool(table_model.getValueAt(row, 5))
            if not rename and not retype:
                selected["variables"].append(None)
                continue
            var_suggestion = {"old_name": old_name}
            if rename:
                var_suggestion["new_name"] = new_name
            if retype:
                var_suggestion["new_type"] = new_type
            selected["variables"].append(var_suggestion)

        if explanation_area is not None:
            selected["explanation"] = explanation_area.getText()
        selected_suggestions[0] = selected
        dialog.dispose()

    def on_cancel(_):
        dialog.dispose()

    apply_button = JButton("Apply Selected")
    apply_button.addActionListener(on_apply)
    cancel_button = JButton("Cancel")
    cancel_button.addActionListener(on_cancel)
    bottom_button_panel.add(apply_button)
    bottom_button_panel.add(cancel_button)
    panel.add(bottom_button_panel)

    dialog.getContentPane().add(panel)
    dialog.setSize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
    dialog.setLocationRelativeTo(None)
    dialog.setDefaultCloseOperation(JDialog.DISPOSE_ON_CLOSE)
    dialog.setVisible(True)
    return selected_suggestions[0]
