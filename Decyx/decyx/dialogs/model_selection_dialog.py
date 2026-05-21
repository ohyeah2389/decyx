# model_selection_dialog.py

from javax.swing import JDialog, JPanel, JButton, BoxLayout, JLabel, JComboBox
from java.awt import BorderLayout


def show_model_select_dialog(models):
    selected_model = [None]
    dialog = JDialog()
    dialog.setTitle("Select Claude Model")
    dialog.setModal(True)

    panel = JPanel()
    panel.setLayout(BoxLayout(panel, BoxLayout.Y_AXIS))
    instruction = JLabel("Select the Claude model to use:")
    instruction.setToolTipText("Choose the desired Claude model")
    panel.add(instruction)
    model_combo_box = JComboBox(models)
    model_combo_box.setSelectedIndex(0)
    model_combo_box.setToolTipText("Select a Claude model from the dropdown")
    panel.add(model_combo_box)

    button_panel = JPanel()

    def on_ok(_):
        selected_model[0] = model_combo_box.getSelectedItem()
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
    dialog.setSize(320, 150)
    dialog.setLocationRelativeTo(None)
    dialog.setDefaultCloseOperation(JDialog.DISPOSE_ON_CLOSE)
    dialog.setVisible(True)
    return selected_model[0]
