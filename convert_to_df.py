import pandas as pd
import os
def read_profit_and_loss_tab(download_dir, file_name):
   file_path = os.path.join(download_dir, file_name)
   if os.path.exists(file_path):
       # Read the Excel file
       try:
           # Load only the "Profit and Loss" sheet
           profit_and_loss_df = pd.read_excel(file_path, sheet_name="Profit & Loss")
           # Perform any additional processing here if needed
           print("Profit and Loss Data:")
           print(profit_and_loss_df.head())
       except Exception as e:
           print(f"Error reading Excel file or extracting Profit and Loss tab: {e}")
   else:
       print(f"File {file_name} not found in {download_dir}")
if __name__ == '__main__':
   download_dir = "/tmp"  # Adjust this if using a different directory
   file_name = "profit_and_loss.xlsx"
   read_profit_and_loss_tab(download_dir, file_name)
