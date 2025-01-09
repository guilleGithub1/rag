import pdftotext
import re
import pandas as pd

transactions = []
coutas= []
transaction_pattern = "^(?P<transaction_date>\s*\d{2}-\w{3}-\d{2})(?P<description>\s+[\w\s*-]+(?:\([\w,\s]+\))?)((?P<id_trans>\s+\d{5}))(?P<amount>\s+\d{1,5}(?:,\d{2})?)"
cuotas_pattern = "^(?P<transaction_date>\s*\d{2}-\w{3}-\d{2})(?P<description>\s+[\w\s*-]+(?:\([\w,\s]+\))?)(?P<coutas>\s+\d{2}/\d{2})((?P<id_trans>\s+\d{5}))(?P<amount>\s+\d{1,5}(?:,\d{2})?)"


with open("./EResumenMaster.PDF2024-02-26.pdf", "rb") as file:
    pdf = pdftotext.PDF(file, physical=True)
    for page_num in range(len(pdf)):
        page = pdf[page_num]
        lines = page.split("\n")
        for line in lines:
            print(line.lstrip())
            match_transacciones = re.search(pattern=transaction_pattern, string=line)
            match_cuotas = re.search(pattern=cuotas_pattern, string=line)
            if match_transacciones:
                transactions.append(match_transacciones.groupdict())
            elif match_cuotas:
                coutas.append(match_cuotas.groupdict())


df_transaciones = pd.DataFrame(transactions)
df_cuotas = pd.DataFrame(coutas)


print(df_transaciones)
print(df_cuotas)