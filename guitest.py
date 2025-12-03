import tkinter as tk
from tkinter import messagebox

def on_submit():
    """Handle button click event."""
    user_text = entry.get().strip()
    if not user_text:
        messagebox.showwarning("Input Error", "Please enter some text.")
        return
    messagebox.showinfo("You Entered", f"You typed: {user_text}")

# Create the main application window
root = tk.Tk()
root.title("Tkinter Example")
root.geometry("300x150")  # Width x Height

# Create and place a label
label = tk.Label(root, text="Enter something:", font=("Arial", 12))
label.pack(pady=10)

# Create and place an entry widget
entry = tk.Entry(root, width=25)
entry.pack(pady=5)

# Create and place a button
submit_btn = tk.Button(root, text="Submit", command=on_submit)
submit_btn.pack(pady=10)

# Start the Tkinter event loop
root.mainloop()
