# action_selection_dialog.py

from javax.swing import JDialog, JPanel, JCheckBox, JButton, BoxLayout, JLabel
from java.awt import BorderLayout


def show_action_select_dialog():
    selected_actions = []
    dialog = JDialog()
    dialog.setTitle("Select Actions to Perform")
    dialog.setModal(True)
    panel = JPanel()
    panel.setLayout(BoxLayout(panel, BoxLayout.Y_AXIS))
    panel.add(JLabel("Select the actions you want to perform:"))

    rename_retype_checkbox = JCheckBox("Rename and Retype Variables", True)
    rename_retype_checkbox.setToolTipText("Rename variables and update their types")
    explanation_checkbox = JCheckBox("Get Function Explanation", False)
    explanation_checkbox.setToolTipText("Obtain explanations for functions")
    line_comments_checkbox = JCheckBox("Add Line Comments", False)
    line_comments_checkbox.setToolTipText("Add comments to lines of code")
    panel.add(rename_retype_checkbox)
    panel.add(explanation_checkbox)
    panel.add(line_comments_checkbox)

    button_panel = JPanel()

    def on_ok(_):
        if rename_retype_checkbox.isSelected():
            selected_actions.append("rename_retype")
        if explanation_checkbox.isSelected():
            selected_actions.append("explanation")
        if line_comments_checkbox.isSelected():
            selected_actions.append("line_comments")
        dialog.dispose()

    def on_cancel(_):
        dialog.dispose()

    ok_button = JButton("OK")
    ok_button.addActionListener(on_ok)
    cancel_button = JButton("Cancel")
    cancel_button.addActionListener(on_cancel)
    button_panel.add(ok_button)
    button_panel.add(cancel_button)

    dialog.getContentPane().add(panel, BorderLayout.CENTER)
    dialog.getContentPane().add(button_panel, BorderLayout.SOUTH)
    dialog.setSize(320, 200)
    dialog.setLocationRelativeTo(None)
    dialog.setDefaultCloseOperation(JDialog.DISPOSE_ON_CLOSE)
    dialog.setVisible(True)
    return selected_actions
