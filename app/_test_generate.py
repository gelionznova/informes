import os
from services.docx_generator import generate_documents

sample = {
    "informe_no": "04",
    "contrato_no": "2.28.04-186-A",
    "fecha_contrato": "20/12/25",
    "objeto_contractual": "Objeto de prueba",
    "entidad_contratante": "Municipio de Caldono",
    "nit": "891501723-1",
    "contratista": "Yennyfer Tatiana Basto",
    "cc": "1062298038",
    "ciudad_expedicion": "Santander de Quilichao",
    "plazo_dia": "31",
    "plazo_mes": "diciembre",
    "plazo_anio": "2025",
    "fecha_inicio_contrato": "09/09/25",
    "fecha_vencimiento_contrato": "31/12/25",
    "valor_inicial": "$ 10,000,000",
    "cdp": "518 del 9 septiembre 2025",
    "rp": "933 del 9 septiembre 2025",
    "periodo_i_de": "29/11/25",
    "periodo_i_a": "31/12/25",
    "fecha_expedicion_informe_dia": "20",
    "fecha_expedicion_informe_mes": "diciembre",
    "fecha_expedicion_informe_año": "2025",
    "fecha_presentacion_informe": "20/12/25",
    "obligaciones_directas": "Actividad 1\nActividad 2",
    "obligaciones_directas_ejecutadas": "Ejecutada 1\nEjecutada 2",
    "obligaciones_generales": "General 1\nGeneral 2",
    "obligaciones_generales_ejecutadas": "Gen ejecutada 1\nGen ejecutada 2",
    "aportes_planilla": "93356613",
    "aportes_mes": "12/2025",
    "fecha_pago_aportes": "15/12/25",
    "operador_planilla": "Compensar",
    "aportes_valor_salud": "$ 178,000",
    "aportes_valor_pension": "$ 227,800",
    "aportes_valor_riesgos": "$ 7,500",
    "aportes_valor_caja_compensacion_familiar": "$ 52,000",
    "total_aportes": "$ 465,300",
    "valor_contrato": "$ 10,000,000",
    "valor_anticipo": "$ 0",
    "valor_pago_anticipado": "$ 0",
    "valor_adiciones": "$ 0",
    "valor_ejecutado": "$ 7,500,000",
    "valor_a_cobrar": "$ 2,500,000",
    "saldo_pendiente": "$ 0",
    "valor_presente_informe": "$ 2,500,000",
    "actas_subtotal": "$ 7,500,000",
    "actas_parciales": [
        {"acta": "Acta parcial 1", "periodo": "09/09/2025-30/09/2025", "valor": "$ 2,500,000"},
        {"acta": "Acta parcial 2", "periodo": "01/10/2025-28/10/2025", "valor": "$ 2,500,000"},
        {"acta": "Acta parcial 3", "periodo": "29/10/2025-28/11/2025", "valor": "$ 2,500,000"},
    ],
    "obligaciones_directas_items": [
        {
            "actividad_contrato": "Actividad 1",
            "actividad_ejecutada": "Ejecutada 1",
            "aporta_evidencias": "SI",
        },
        {
            "actividad_contrato": "Actividad 2",
            "actividad_ejecutada": "Ejecutada 2",
            "aporta_evidencias": "NO",
        },
    ],
    "obligaciones_generales_items": [
        {
            "actividad_contrato": "General 1",
            "actividad_ejecutada": "Gen ejecutada 1",
            "aporta_evidencias": "SI",
        },
    ],
}

if __name__ == "__main__":
    outputs = generate_documents(sample, 99999)
    for key, path in outputs.items():
        print(f"{key}: {path}")
