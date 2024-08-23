            
import win32com.client
import pandas as pd


xlapp = win32com.client.DispatchEx("Excel.Application")
 
wb = xlapp.Workbooks.Open("C:/Users/Dhruv Gogri/Desktop/Dhruv/vault-1/Reliance Industr.xlsx")
  
wb.RefreshAll()
wb.Save()
xlapp.Quit()

df =pd.read_excel('Reliance Industr.xlsx',skiprows=2)
print(df.head(10))
 
 
