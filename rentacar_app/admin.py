from django.contrib import admin
from .models import Cliente, Vehiculo, Reserva, Contrato, Reporte, Empleado

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'cedula_identidad', 'telefono', 'fecha_registro']
    search_fields = ['usuario__first_name', 'usuario__last_name', 'cedula_identidad']
    list_filter = ['fecha_registro']

@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ['marca', 'modelo', 'placa', 'año', 'tipo', 'precio_dia', 'estado']
    list_filter = ['tipo', 'estado', 'año']
    search_fields = ['marca', 'modelo', 'placa']

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['codigo_reserva', 'cliente', 'vehiculo', 'fecha_inicio', 'fecha_fin', 'estado', 'precio_total']
    list_filter = ['estado', 'fecha_reserva']
    search_fields = ['codigo_reserva', 'cliente__usuario__first_name', 'vehiculo__placa']

@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ['reserva', 'fecha_creacion', 'firmado']
    list_filter = ['firmado', 'fecha_creacion']

@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'fecha_generacion', 'generado_por']
    list_filter = ['tipo', 'fecha_generacion']
    readonly_fields = ['fecha_generacion', 'generado_por']

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'telefono', 'fecha_contratacion', 'activo']
    list_filter = ['activo', 'fecha_contratacion']
    search_fields = ['usuario__first_name', 'usuario__last_name', 'usuario__email']
    list_editable = ['activo']