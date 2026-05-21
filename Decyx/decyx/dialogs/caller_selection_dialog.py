# caller_selection_dialog.py

from javax.swing import JDialog, JPanel, JCheckBox, JButton, JScrollPane, BoxLayout, JLabel, JTextArea
from java.awt import BorderLayout, Dimension

from decyx.decompiler import decompile_function


def show_caller_selection_dialog(callers, current_program, monitor):
    if not callers:
        return []

    selected_callers = []
    dialog = JDialog()
    dialog.setTitle("Select Callers to Include")
    dialog.setModal(True)
    panel = JPanel(BorderLayout())
    callers_panel = JPanel()
    callers_panel.setLayout(BoxLayout(callers_panel, BoxLayout.Y_AXIS))
    caller_checkboxes = []

    for caller in callers:
        checkbox = JCheckBox(caller.getName(), False)
        caller_checkboxes.append((checkbox, caller))
        callers_panel.add(checkbox)

    controls = JPanel()
    controls.setLayout(BoxLayout(controls, BoxLayout.Y_AXIS))
    controls.add(JLabel("Select callers to include as additional context:"))

    scroll_callers = JScrollPane(callers_panel)
    scroll_callers.setPreferredSize(Dimension(280, 320))
    left_panel = JPanel(BorderLayout())
    left_panel.add(controls, BorderLayout.NORTH)
    left_panel.add(scroll_callers, BorderLayout.CENTER)

    preview_panel = JPanel(BorderLayout())
    preview_label = JLabel("Caller Function Preview:")
    preview_area = JTextArea()
    preview_area.setEditable(False)
    preview_area.setLineWrap(True)
    preview_area.setWrapStyleWord(True)
    preview_area.setText("Select a caller to see its decompiled code preview.")
    preview_scroll = JScrollPane(preview_area)
    preview_scroll.setPreferredSize(Dimension(560, 320))
    preview_panel.add(preview_label, BorderLayout.NORTH)
    preview_panel.add(preview_scroll, BorderLayout.CENTER)

    def reset_preview():
        preview_label.setText("Caller Function Preview:")
        preview_area.setText("Select a caller to see its decompiled code preview.")
        preview_area.setCaretPosition(0)

    def set_preview(caller, selected):
        if not selected:
            preview_label.setText("Caller Function Preview:")
            preview_area.setText("Select a caller to see its decompiled code preview.")
            preview_area.setCaretPosition(0)
            return
        decompiled_code, _ = decompile_function(caller, current_program, monitor)
        if decompiled_code:
            preview_label.setText("Caller Function Preview (Length: {} characters):".format(len(decompiled_code)))
            preview_area.setText(decompiled_code)
        else:
            preview_label.setText("Caller Function Preview:")
            preview_area.setText("Decompilation failed or no code available.")
        preview_area.setCaretPosition(0)

    for checkbox, caller in caller_checkboxes:
        checkbox.addActionListener(lambda e, c=caller: set_preview(c, e.getSource().isSelected()))

    buttons_panel = JPanel()
    select_all_button = JButton("Select All Callers")
    unselect_all_button = JButton("Unselect All Callers")
    ok_button = JButton("OK")
    cancel_button = JButton("Cancel")

    def on_select_all(_):
        for checkbox, _caller in caller_checkboxes:
            checkbox.setSelected(True)

    def on_unselect_all(_):
        for checkbox, _caller in caller_checkboxes:
            checkbox.setSelected(False)
        reset_preview()

    def on_ok(_):
        for checkbox, caller in caller_checkboxes:
            if checkbox.isSelected():
                selected_callers.append(caller)
        dialog.dispose()

    def on_cancel(_):
        selected_callers[:] = []
        dialog.dispose()

    select_all_button.addActionListener(on_select_all)
    unselect_all_button.addActionListener(on_unselect_all)
    ok_button.addActionListener(on_ok)
    cancel_button.addActionListener(on_cancel)
    buttons_panel.add(select_all_button)
    buttons_panel.add(unselect_all_button)
    buttons_panel.add(ok_button)
    buttons_panel.add(cancel_button)

    panel.add(left_panel, BorderLayout.WEST)
    panel.add(preview_panel, BorderLayout.CENTER)
    panel.add(buttons_panel, BorderLayout.SOUTH)
    dialog.getContentPane().add(panel)
    dialog.setSize(900, 420)
    dialog.setLocationRelativeTo(None)
    dialog.setDefaultCloseOperation(JDialog.DISPOSE_ON_CLOSE)
    dialog.setVisible(True)
    return selected_callers
