# prompt_review_dialog.py

from javax.swing import JDialog, JPanel, JButton, JScrollPane, BoxLayout, JLabel, JTextArea
from java.awt import BorderLayout

from decyx.config import SKIP_PROMPT_CONFIRMATION


def show_prompt_review_dialog(prompt, title):
    if SKIP_PROMPT_CONFIRMATION:
        return prompt

    final_prompt = [None]
    dialog = JDialog()
    dialog.setTitle(title)
    dialog.setModal(True)
    panel = JPanel()
    panel.setLayout(BoxLayout(panel, BoxLayout.Y_AXIS))
    panel.add(JLabel("Review and edit the final prompt before sending to Claude API:"))
    prompt_text_area = JTextArea(prompt, 20, 60)
    prompt_text_area.setLineWrap(True)
    prompt_text_area.setWrapStyleWord(True)
    prompt_text_area.setToolTipText("Edit the prompt here")
    panel.add(JScrollPane(prompt_text_area))

    button_panel = JPanel()

    def on_send(_):
        final_prompt[0] = prompt_text_area.getText()
        dialog.dispose()

    def on_cancel(_):
        dialog.dispose()

    send_button = JButton("Send to Claude API")
    send_button.addActionListener(on_send)
    cancel_button = JButton("Cancel")
    cancel_button.addActionListener(on_cancel)
    button_panel.add(send_button)
    button_panel.add(cancel_button)

    dialog.getContentPane().add(JScrollPane(panel), BorderLayout.CENTER)
    dialog.getContentPane().add(button_panel, BorderLayout.SOUTH)
    dialog.setSize(700, 500)
    dialog.setLocationRelativeTo(None)
    dialog.setDefaultCloseOperation(JDialog.DISPOSE_ON_CLOSE)
    dialog.setVisible(True)
    return final_prompt[0]
