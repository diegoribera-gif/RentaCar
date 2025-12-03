from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os
from datetime import datetime
from django.http import HttpResponse
from django.db.models import Count, Sum, Q
from decimal import Decimal
from .models import Reserva, Vehiculo, Cliente

# ========== FUNCIÓN AUXILIAR PARA CONVERTIR DECIMAL A FLOAT ==========

def convertir_decimal_a_float(datos):
    """
    Convierte recursivamente todos los valores Decimal en un diccionario/listas a float
    para que sean serializables a JSON.
    """
    if isinstance(datos, dict):
        return {key: convertir_decimal_a_float(value) for key, value in datos.items()}
    elif isinstance(datos, list):
        return [convertir_decimal_a_float(item) for item in datos]
    elif isinstance(datos, Decimal):
        return float(datos)
    else:
        return datos

def generar_contrato_pdf(reserva):
    """Genera un contrato en PDF para una reserva"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Estilo personalizado para el título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1,  # Centrado
        textColor=colors.HexColor('#2c3e50')
    )
    
    # Título del contrato
    title = Paragraph("CONTRATO DE ALQUILER DE VEHÍCULO", title_style)
    story.append(title)
    
    # Información de la empresa
    empresa_style = ParagraphStyle(
        'Empresa',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12,
        alignment=1
    )
    empresa = Paragraph("<b>RENTACAR</b><br/>Calle Raúl Otero Reich y Vía Puerto Suárez<br/>Teléfono: +591-XXX-XXXX", empresa_style)
    story.append(empresa)
    story.append(Spacer(1, 20))
    
    # Información del contrato
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Datos del contrato
    story.append(Paragraph(f"<b>Número de Contrato:</b> {reserva.codigo_reserva}", info_style))
    story.append(Paragraph(f"<b>Fecha de Emisión:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", info_style))
    story.append(Spacer(1, 15))
    
    # Datos del cliente
    story.append(Paragraph("<b>DATOS DEL CLIENTE</b>", styles['Heading2']))
    story.append(Paragraph(f"<b>Nombre Completo:</b> {reserva.cliente.usuario.get_full_name()}", info_style))
    story.append(Paragraph(f"<b>Cédula de Identidad:</b> {reserva.cliente.cedula_identidad}", info_style))
    story.append(Paragraph(f"<b>Licencia de Conducir:</b> {reserva.cliente.licencia_conducir}", info_style))
    story.append(Paragraph(f"<b>Teléfono:</b> {reserva.cliente.telefono}", info_style))
    story.append(Paragraph(f"<b>Dirección:</b> {reserva.cliente.direccion}", info_style))
    story.append(Spacer(1, 15))
    
    # Datos del vehículo
    story.append(Paragraph("<b>DATOS DEL VEHÍCULO</b>", styles['Heading2']))
    story.append(Paragraph(f"<b>Vehículo:</b> {reserva.vehiculo.marca} {reserva.vehiculo.modelo}", info_style))
    story.append(Paragraph(f"<b>Placa:</b> {reserva.vehiculo.placa}", info_style))
    story.append(Paragraph(f"<b>Año:</b> {reserva.vehiculo.año}", info_style))
    story.append(Paragraph(f"<b>Tipo:</b> {reserva.vehiculo.get_tipo_display()}", info_style))
    story.append(Paragraph(f"<b>Capacidad:</b> {reserva.vehiculo.capacidad_pasajeros} pasajeros", info_style))
    story.append(Spacer(1, 15))
    
    # Términos del alquiler
    story.append(Paragraph("<b>TÉRMINOS DEL ALQUILER</b>", styles['Heading2']))
    story.append(Paragraph(f"<b>Fecha de Inicio:</b> {reserva.fecha_inicio.strftime('%d/%m/%Y %H:%M')}", info_style))
    story.append(Paragraph(f"<b>Fecha de Fin:</b> {reserva.fecha_fin.strftime('%d/%m/%Y %H:%M')}", info_style))
    story.append(Paragraph(f"<b>Duración:</b> {reserva.duracion_dias} días", info_style))
    story.append(Paragraph(f"<b>Precio por Día:</b> Bs. {reserva.vehiculo.precio_dia}", info_style))
    story.append(Paragraph(f"<b>Precio Total:</b> Bs. {reserva.precio_total}", info_style))
    story.append(Spacer(1, 15))
    
    # Términos y condiciones
    story.append(Paragraph("<b>TÉRMINOS Y CONDICIONES</b>", styles['Heading2']))
    terminos = [
        "1. El cliente se compromete a devolver el vehículo en el mismo estado en que fue recibido.",
        "2. Cualquier daño al vehículo será responsabilidad del cliente.",
        "3. El cliente debe presentar licencia de conducir válida al momento de la entrega.",
        "4. No se permite el uso del vehículo fuera de los límites departamentales sin autorización.",
        "5. El combustible utilizado durante el alquiler es responsabilidad del cliente.",
        "6. Cualquier infracción de tránsito cometida durante el período de alquiler será responsabilidad del cliente.",
        "7. La empresa se reserva el derecho de cancelar el contrato en caso de incumplimiento de los términos.",
    ]
    
    for termino in terminos:
        story.append(Paragraph(termino, info_style))
    
    story.append(Spacer(1, 30))
    
    # Firmas
    firmas_style = ParagraphStyle(
        'Firmas',
        parent=styles['Normal'],
        fontSize=10,
        spaceBefore=20
    )
    
    firmas_data = [
        ['', ''],
        ['_________________________', '_________________________'],
        ['Firma del Cliente', 'Firma del Representante RentaCar'],
        [f'{reserva.cliente.usuario.get_full_name()}', 'RentaCar'],
        [f'CI: {reserva.cliente.cedula_identidad}', f'Fecha: {datetime.now().strftime("%d/%m/%Y")}']
    ]
    
    firmas_table = Table(firmas_data, colWidths=[3*inch, 3*inch])
    firmas_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(firmas_table)
    
    # Generar PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def generar_reporte_pdf(reporte_data, tipo_reporte):
    """Genera reportes en PDF"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Título del reporte
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=30,
        alignment=1,
        textColor=colors.HexColor('#2c3e50')
    )
    
    titulos = {
        'FINANCIERO': 'REPORTE FINANCIERO',
        'RESERVAS': 'REPORTE DE RESERVAS',
        'VEHICULOS': 'REPORTE DE VEHÍCULOS',
        'CLIENTES': 'REPORTE DE CLIENTES'
    }
    
    title = Paragraph(titulos.get(tipo_reporte, 'REPORTE'), title_style)
    story.append(title)
    
    # Fecha de generación
    fecha_style = ParagraphStyle(
        'Fecha',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=20,
        alignment=1
    )
    fecha = Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", fecha_style)
    story.append(fecha)
    
    # Contenido específico según el tipo de reporte
    content_style = ParagraphStyle(
        'Content',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=12
    )
    
    if tipo_reporte == 'FINANCIERO':
        total_ingresos = reporte_data.get('total_ingresos', 0)
        story.append(Paragraph(f"<b>Total de Ingresos:</b> Bs. {total_ingresos:,.2f}", content_style))
        story.append(Paragraph(f"<b>Total de Reservas:</b> {reporte_data.get('total_reservas', 0)}", content_style))
        
        # Tabla de reservas por tipo de vehículo
        if 'reservas_por_tipo' in reporte_data:
            story.append(Spacer(1, 15))
            story.append(Paragraph("<b>Reservas por Tipo de Vehículo</b>", styles['Heading2']))
            
            tabla_data = [['Tipo de Vehículo', 'Cantidad', 'Total (Bs.)']]
            for item in reporte_data['reservas_por_tipo']:
                tabla_data.append([
                    item.get('vehiculo__tipo', 'Desconocido'),
                    str(item.get('cantidad', 0)),
                    f"{item.get('total', 0):,.2f}"
                ])
            
            tabla = Table(tabla_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7'))
            ]))
            story.append(tabla)
    
    elif tipo_reporte == 'RESERVAS':
        story.append(Paragraph(f"<b>Total de Reservas:</b> {reporte_data.get('total_reservas', 0)}", content_style))
        tasa_ocupacion = reporte_data.get('tasa_ocupacion', 0)
        story.append(Paragraph(f"<b>Tasa de Ocupación:</b> {tasa_ocupacion:.1f}%", content_style))
    
    elif tipo_reporte == 'VEHICULOS':
        total_vehiculos = reporte_data.get('total_vehiculos', 0)
        story.append(Paragraph(f"<b>Total de Vehículos:</b> {total_vehiculos}", content_style))
        
        # Contar vehículos disponibles si no está en los datos
        if 'vehiculos_disponibles' in reporte_data:
            disponibles = reporte_data['vehiculos_disponibles']
        else:
            disponibles = Vehiculo.objects.filter(estado='DISPONIBLE').count()
            
        story.append(Paragraph(f"<b>Vehículos Disponibles:</b> {disponibles}", content_style))
        story.append(Paragraph(f"<b>Vehículos en Mantenimiento:</b> {Vehiculo.objects.filter(estado='MANTENIMIENTO').count()}", content_style))
    
    elif tipo_reporte == 'CLIENTES':
        total_clientes = reporte_data.get('total_clientes', 0)
        story.append(Paragraph(f"<b>Total de Clientes:</b> {total_clientes}", content_style))
        
        clientes_activos = reporte_data.get('clientes_con_licencia_valida', 0)
        story.append(Paragraph(f"<b>Clientes con Licencia Válida:</b> {clientes_activos}", content_style))
    
    story.append(Spacer(1, 30))
    
    # Pie de página
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=1,
        textColor=colors.HexColor('#7f8c8d')
    )
    footer = Paragraph("Sistema RentaCar - Generado automáticamente", footer_style)
    story.append(footer)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def generar_reporte_vehiculos():
    """Genera datos para reporte de vehículos"""
    vehiculos = Vehiculo.objects.all()
    
    # Vehículos por tipo
    vehiculos_por_tipo = list(vehiculos.values('tipo').annotate(
        total=Count('id')
    ))
    
    # Vehículos por estado
    vehiculos_por_estado = list(vehiculos.values('estado').annotate(
        total=Count('id')
    ))
    
    # Vehículos más rentados
    vehiculos_mas_rentados = list(vehiculos.annotate(
        num_reservas=Count('reservas')
    ).order_by('-num_reservas')[:5].values(
        'marca', 'modelo', 'placa', 'num_reservas'
    ))
    
    # Ingresos por vehículo - CONVERTIR DECIMAL A FLOAT
    ingresos_por_vehiculo_raw = list(vehiculos.annotate(
        total_ingresos=Sum('reservas__precio_total')
    ).filter(total_ingresos__isnull=False).order_by('-total_ingresos')[:5].values(
        'marca', 'modelo', 'placa', 'total_ingresos'
    ))
    
    # Convertir Decimal a float
    ingresos_por_vehiculo = []
    for item in ingresos_por_vehiculo_raw:
        ingresos_por_vehiculo.append({
            'marca': item['marca'],
            'modelo': item['modelo'],
            'placa': item['placa'],
            'total_ingresos': float(item['total_ingresos'] or 0)
        })
    
    datos = {
        'total_vehiculos': vehiculos.count(),
        'vehiculos_por_tipo': vehiculos_por_tipo,
        'vehiculos_por_estado': vehiculos_por_estado,
        'vehiculos_mas_rentados': vehiculos_mas_rentados,
        'ingresos_por_vehiculo': ingresos_por_vehiculo,
        'vehiculos_disponibles': vehiculos.filter(estado='DISPONIBLE').count(),
        'fecha_generacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return datos

def generar_reporte_clientes():
    """Genera datos para reporte de clientes - VERSIÓN SIMPLE"""
    clientes = Cliente.objects.select_related('usuario').all()
    
    # Clientes más frecuentes
    clientes_mas_frecuentes_raw = list(clientes.annotate(
        num_reservas=Count('reservas'),
        total_gastado=Sum('reservas__precio_total')
    ).order_by('-num_reservas')[:10])
    
    clientes_mas_frecuentes = []
    for cliente in clientes_mas_frecuentes_raw:
        clientes_mas_frecuentes.append({
            'nombre': cliente.usuario.get_full_name() or cliente.usuario.username,
            'cedula': cliente.cedula_identidad,
            'telefono': cliente.telefono,
            'num_reservas': cliente.num_reservas or 0,
            'total_gastado': float(cliente.total_gastado or 0),
            'licencia_valida': cliente.licencia_valida,
            'activo': cliente.activo
        })
    
    # Clientes por fecha de registro (simplificado para SQLite)
    # Agrupar manualmente por año
    clientes_por_año = {}
    for cliente in clientes:
        if cliente.fecha_registro:
            año = cliente.fecha_registro.year
            clientes_por_año[año] = clientes_por_año.get(año, 0) + 1
        else:
            año = 'Sin fecha'
            clientes_por_año[año] = clientes_por_año.get(año, 0) + 1
    
    clientes_por_año_list = []
    for año, total in sorted(clientes_por_año.items()):
        clientes_por_año_list.append({
            'año': str(año),
            'total': total
        })
    
    # Clientes por mes del año actual (para mostrar tendencia)
    from datetime import datetime, timedelta
    año_actual = datetime.now().year
    clientes_este_año = clientes.filter(
        fecha_registro__year=año_actual
    )
    
    clientes_por_mes = []
    for mes in range(1, 13):
        cantidad = clientes_este_año.filter(
            fecha_registro__month=mes
        ).count()
        clientes_por_mes.append({
            'mes': f'{mes:02d}/{año_actual}',
            'total': cantidad
        })
    
    datos = {
        'total_clientes': clientes.count(),
        'clientes_con_licencia_valida': clientes.filter(licencia_valida=True).count(),
        'clientes_sin_licencia_valida': clientes.filter(licencia_valida=False).count(),
        'clientes_activos': clientes.filter(activo=True).count(),
        'clientes_con_reservas': clientes.filter(reservas__isnull=False).distinct().count(),
        'clientes_mas_frecuentes': clientes_mas_frecuentes,
        'clientes_por_año': clientes_por_año_list,
        'clientes_por_mes': clientes_por_mes,
        'fecha_generacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return datos

def verificar_disponibilidad_vehiculo(vehiculo_id, fecha_inicio, fecha_fin, reserva_excluida=None):
    """Verifica si un vehículo está disponible en un rango de fechas"""
    reservas_conflictivas = Reserva.objects.filter(
        vehiculo_id=vehiculo_id,
        fecha_inicio__lte=fecha_fin,
        fecha_fin__gte=fecha_inicio,
        estado__in=['CONFIRMADA', 'ACTIVA', 'PENDIENTE']
    )
    
    if reserva_excluida:
        reservas_conflictivas = reservas_conflictivas.exclude(id=reserva_excluida.id)
    
    return not reservas_conflictivas.exists()

def generar_reporte_financiero(fecha_inicio=None, fecha_fin=None):
    """Genera datos para reporte financiero"""
    from django.db.models import Sum, Count
    
    # Filtrar por fechas si se proporcionan
    filtros = {}
    if fecha_inicio:
        filtros['fecha_reserva__date__gte'] = fecha_inicio
    if fecha_fin:
        filtros['fecha_reserva__date__lte'] = fecha_fin
    
    reservas = Reserva.objects.filter(
        estado__in=['COMPLETADA', 'ACTIVA'],
        **filtros
    )
    
    total_ingresos = reservas.aggregate(total=Sum('precio_total'))['total'] or Decimal('0')
    total_reservas = reservas.count()
    
    # Reservas por tipo de vehículo - CONVERTIR DECIMAL A FLOAT
    reservas_por_tipo_raw = list(reservas.values('vehiculo__tipo').annotate(
        total=Sum('precio_total'),
        cantidad=Count('id')
    ))
    
    reservas_por_tipo = []
    for item in reservas_por_tipo_raw:
        reservas_por_tipo.append({
            'vehiculo__tipo': item['vehiculo__tipo'],
            'total': float(item['total'] or 0),
            'cantidad': item['cantidad']
        })
    
    # Detalle de reservas
    reservas_detalle_raw = list(reservas.values(
        'codigo_reserva', 'cliente__usuario__first_name',
        'vehiculo__marca', 'vehiculo__modelo', 'precio_total', 'fecha_reserva'
    )[:20])  # Limitar a 20 reservas para no hacer el reporte muy grande
    
    reservas_detalle = []
    for item in reservas_detalle_raw:
        reservas_detalle.append({
            'codigo_reserva': item['codigo_reserva'],
            'cliente': item['cliente__usuario__first_name'] or 'Sin nombre',
            'vehiculo': f"{item['vehiculo__marca']} {item['vehiculo__modelo']}",
            'precio_total': float(item['precio_total'] or 0),
            'fecha_reserva': item['fecha_reserva'].strftime('%Y-%m-%d %H:%M') if item['fecha_reserva'] else ''
        })
    
    datos = {
        'total_ingresos': float(total_ingresos),
        'total_reservas': total_reservas,
        'reservas_por_tipo': reservas_por_tipo,
        'reservas_detalle': reservas_detalle,
        'periodo': f"{fecha_inicio or 'Inicio'} a {fecha_fin or 'Fin'}",
        'fecha_generacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return datos

def generar_reporte_reservas(fecha_inicio=None, fecha_fin=None):
    """Genera datos para reporte de reservas"""
    from django.db.models import Count
    
    # Filtrar por fechas si se proporcionan
    filtros = {}
    if fecha_inicio:
        filtros['fecha_reserva__date__gte'] = fecha_inicio
    if fecha_fin:
        filtros['fecha_reserva__date__lte'] = fecha_fin
    
    reservas = Reserva.objects.filter(**filtros)
    
    total_reservas = reservas.count()
    
    # Reservas por estado
    reservas_por_estado_raw = list(reservas.values('estado').annotate(
        total=Count('id')
    ))
    
    reservas_por_estado = []
    for item in reservas_por_estado_raw:
        reservas_por_estado.append({
            'estado': item['estado'],
            'total': item['total']
        })
    
    # Reservas por vehículo
    reservas_por_vehiculo = list(reservas.values(
        'vehiculo__marca', 'vehiculo__modelo'
    ).annotate(
        total=Count('id')
    ).order_by('-total')[:10])  # Top 10 vehículos
    
    # Calcular tasa de ocupación (simplificado)
    total_vehiculos = Vehiculo.objects.count()
    tasa_ocupacion = 0
    
    if total_vehiculos > 0 and total_reservas > 0:
        # Estimación simple: porcentaje de vehículos con al menos una reserva
        vehiculos_con_reservas = Vehiculo.objects.filter(
            reservas__in=reservas
        ).distinct().count()
        tasa_ocupacion = (vehiculos_con_reservas / total_vehiculos) * 100
    
    datos = {
        'total_reservas': total_reservas,
        'reservas_por_estado': reservas_por_estado,
        'reservas_por_vehiculo': reservas_por_vehiculo,
        'tasa_ocupacion': round(tasa_ocupacion, 2),
        'periodo': f"{fecha_inicio or 'Inicio'} a {fecha_fin or 'Fin'}",
        'fecha_generacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return datos