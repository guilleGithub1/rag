

class PatronExtraccion:
    def __init__(self):
        self.patrones = {
            "ICBC": {
                "VISA": {
                    "transaccion": r"^(?P<transaction_date>\s*\d{2}.\d{2}.\d{2})(?P<id_trans>\s+\d{6}\*)(?P<description>\s+[\w\s*. -]+(?:\([\w,\s]+\))?)(?P<amount>\s+\d{1,5}(?:.\d{2})?\d{1,5}(?:,\d{2})?)",
                    "transaccion_cuota": r"^(?P<transaction_date>\s*\d{2}.\d{2}.\d{2})(?P<id_trans>\s+\d{6}\*)(?P<description>\s+[\w\s*. -]+(?:\([\w,\s]+\))?)(?P<coutas>\s+C.\d{2}/\d{2})(?P<amount>\s+\d{1,5}(?:.\d{2})?\d{1,5}(?:,\d{2})?)",
                    "fecha_cierre": r"(CIERRE\s+ACTUAL\s+)(?P<dia>\d{2})\s+(?P<mes>[A-Za-z]{3})\s+(?P<anio>\d{2})",
                    "fecha_vencimiento": r"(VENCIMIENTO\s+ACTUAL\s+)(?P<dia>\d{2})\s+(?P<mes>[A-Za-z]{3})\s+(?P<anio>\d{2})",
                },
                "MASTERCARD": {
                    # ... Patrones para ICBC + MASTERCARD
                },
                # ... Otros tipos de tarjeta para ICBC
            },
            "BBVA": {
                # ... Patrones para BBVA + VISA, MASTERCARD, etc.
                "VISA":{
                    "fecha_emision": r"F. Emision\s*(\d{2}/\d{2}/\d{4})",
                    "detalles": r"Detalle:\s*(.*?)Monto:",
                    "monto": r"Importe:\s*ARS\s*([\d,\.]+)",
                    "fecha_vencimiento": r"Vencimiento:\s*(\d{2}/\d{2}/\d{4})",
                }
            },
            "SANTANDER":{
                "MASTERCARD":{
                    "fecha_emision": r"Fecha de Emision\s*(\d{4}-\d{2}-\d{2})",
                    "detalles": r"Concepto\s*(.*?)Importe",
                    "monto": r"Importe\s*\$([\d,\.]+)",
                    "fecha_vencimiento": r"Vence el\s*(\d{4}-\d{2}-\d{2})",
                }
            },
            # ... Otros bancos
        }

    def obtener_patron(self, banco, tarjeta, dato):
        try:
            return self.patrones[banco][tarjeta][dato]
        except KeyError:
            raise ValueError(f"No se encontró un patrón para Banco: {banco}, Tarjeta: {tarjeta}, Dato: {dato}")
