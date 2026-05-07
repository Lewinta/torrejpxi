import frappe
from frappe.query_builder import Order

GE = frappe.qb.DocType("Gas Entry")
GI = frappe.qb.DocType("Gas Entry Item")

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart(data, filters)
    return columns, data, None, chart

def get_columns(filters):
    columns = [
        {
            "fieldname": "customer",
            "label": "Cliente",
            "fieldtype": "Data",
            "width": 230
        },
    ]
    if filters.get("based_on") == "Consumo":
        columns += [
            {
                "fieldname": "average_consumption",
                "label": "Promedio Consumo (Gal)",
                "fieldtype": "Float",
                "precision": 3,
                "width": 200
            },
            {
                "fieldname": "last_consumption",
                "label": "Último Consumo (Gal)",
                "fieldtype": "Float",
                "precision": 3,
                "width": 200
            },
            {
                "fieldname": "difference",
                "label": "Diferencia",
                "fieldtype": "Float",
                "precision": 3,
                "width": 150
            },
        ]
    elif filters.get("based_on") == "Monto":
        columns += [
            {
                "fieldname": "average_amount",
                "label": "Promedio Monto",
                "fieldtype": "Currency",
                "precision": 3,
                "width": 200
            },
            {
                "fieldname": "last_amount",
                "label": "Último Monto",
                "fieldtype": "Currency",
                "precision": 3,
                "width": 200
            },
            {
                "fieldname": "difference",
                "label": "Diferencia",
                "fieldtype": "Currency",
                "precision": 3,
                "width": 150
            },
        ]

    return columns

def get_data(filters):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    based_on = filters.get("based_on")

    # Obtener los datos de Gas Entry Item junto con la fecha de Gas Entry
    data = (
        frappe.qb.from_(GI)
        .join(GE).on(GI.parent == GE.name)
        .select(
            GI.customer,
            GI.used_gal,
            GI.used_amount,
            GE.date
        )
        .where(
            (GE.date >= from_date) &
            (GE.date <= to_date) &
            (GE.docstatus == 1)
        )
        .orderby(GE.date, order=Order.desc)
    ).run(as_dict=True, debug=True)

    # Organizar por cliente
    customer_data = {}
    for row in data:
        cust = row.customer
        if cust not in customer_data:
            customer_data[cust] = {
                "consumptions": [],
                "amounts": [],
            }

        customer_data[cust]["consumptions"].append(row.used_gal)
        customer_data[cust]["amounts"].append(row.used_amount)

    # Construir los resultados
    result = []
    for customer, values in customer_data.items():
        if based_on == "Consumo":
            average = sum(values["consumptions"]) / len(values["consumptions"])
            last = values["consumptions"][0]
            diff = round(last - average, 3)
            result.append({
                "customer": customer,
                "average_consumption": round(average, 3),
                "last_consumption": round(last, 3),
                "difference": diff
            })
        elif based_on == "Monto":
            average = sum(values["amounts"]) / len(values["amounts"])
            last = values["amounts"][0]
            diff = round(last - average, 3)
            result.append({
                "customer": customer,
                "average_amount": round(average, 3),
                "last_amount": round(last, 3),
                "difference": diff
            })

    return sorted(result, key=lambda x: x["customer"])

def get_chart(data, filters):
    based_on = filters.get("based_on")
    
    labels = [row["customer"] for row in data]

    if based_on == "Consumo":
        average = [row["average_consumption"] for row in data]
        latest = [row["last_consumption"] for row in data]
        y_label = "Consumo (Gal)"
    else:
        average = [row["average_amount"] for row in data]
        latest = [row["last_amount"] for row in data]
        y_label = "Monto ($)"

    chart = {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Promedio",
                    "values": average
                },
                {
                    "name": "Último",
                    "values": latest
                },
            ]
        },
        "type": "bar",
        "barOptions": {
            "stacked": False
        },
        "colors": ["#34a853", "#fbbc05"],
        "axisOptions": {"xIsSeries": True, "yAxisMode": "tick", "xAxisMode": "tick"},
    }

    return chart