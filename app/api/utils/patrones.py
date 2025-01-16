

class PatronExtraccion:
    def __init__(self):
        self.patrones = {
            "ICBC": {
                "VISA": {
                    "fecha_emision": r"Fecha Emision:\s*(\d{2}/\d{2}/\d{4})",
                    "detalles": r"Detalles:\s*(.*?)Monto:",
                    "monto": r"Monto:\s*\$([\d,\.]+)",
                    "fecha_vencimiento": r"Fecha Vencimiento:\s*(\d{2}/\d{2}/\d{4})",
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
