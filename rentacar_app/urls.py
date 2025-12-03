from django.urls import path
from . import views

urlpatterns = [
    
    # Página principal pública
    path('', views.inicio, name='inicio'),
    
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Dashboard (ahora protegido)
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Clientes - URLs COMPLETAS
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/<int:cliente_id>/', views.detalle_cliente, name='detalle_cliente'),
    path('clientes/<int:cliente_id>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:cliente_id>/eliminar/', views.eliminar_cliente, name='eliminar_cliente'),
    path('clientes/<int:cliente_id>/activar/', views.activar_cliente, name='activar_cliente'),
    path('perfil/', views.perfil_cliente, name='perfil_cliente'),  # Perfil del cliente actual
    
    # Empleados (solo admin)
    path('empleados/', views.lista_empleados, name='lista_empleados'),
    path('empleados/crear/', views.crear_empleado, name='crear_empleado'),
    path('empleados/<int:empleado_id>/desactivar/', views.desactivar_empleado, name='desactivar_empleado'),
    path('empleados/<int:empleado_id>/activar/', views.activar_empleado, name='activar_empleado'),
    path('empleados/<int:empleado_id>/', views.detalle_empleado, name='detalle_empleado'),  # NUEVO
path('empleados/<int:empleado_id>/editar/', views.editar_empleado, name='editar_empleado'),  # NUEVO
path('empleados/<int:empleado_id>/eliminar/', views.eliminar_empleado, name='eliminar_empleado'),  # NUEVO
    
    # Vehículos - URLs COMPLETAS
    path('vehiculos/', views.lista_vehiculos, name='lista_vehiculos'),
    path('vehiculos/crear/', views.crear_vehiculo, name='crear_vehiculo'),
    path('vehiculos/<int:vehiculo_id>/', views.detalle_vehiculo, name='detalle_vehiculo'),
    path('vehiculos/<int:vehiculo_id>/editar/', views.editar_vehiculo, name='editar_vehiculo'),
    path('vehiculos/<int:vehiculo_id>/eliminar/', views.eliminar_vehiculo, name='eliminar_vehiculo'),
    path('vehiculos/<int:vehiculo_id>/activar/', views.activar_vehiculo, name='activar_vehiculo'),
    path('vehiculos/disponibilidad/', views.disponibilidad_vehiculos, name='disponibilidad_vehiculos'),
    
    # Reservas - URLs COMPLETAS
    path('reservas/', views.lista_reservas, name='lista_reservas'),
    path('reservas/crear/', views.crear_reserva, name='crear_reserva'),
    path('reservas/<int:reserva_id>/', views.detalle_reserva, name='detalle_reserva'),
    path('reservas/<int:reserva_id>/editar/', views.editar_reserva, name='editar_reserva'),
    path('reservas/<int:reserva_id>/eliminar/', views.eliminar_reserva, name='eliminar_reserva'),
    path('reservas/<int:reserva_id>/confirmar/', views.confirmar_reserva, name='confirmar_reserva'),
    path('reservas/<int:reserva_id>/cancelar/', views.cancelar_reserva, name='cancelar_reserva'),
    path('reservas/<int:reserva_id>/contrato/', views.descargar_contrato, name='descargar_contrato'),
    
    # Reportes
    path('reportes/', views.reportes, name='reportes'),
    
    # APIs
    path('api/disponibilidad/', views.api_disponibilidad, name='api_disponibilidad'),
    
    # Diagnóstico
    path('diagnostico/vehiculos/', views.diagnostico_vehiculos, name='diagnostico_vehiculos'),
    
    # Página principal redirige al dashboard
    path('', views.dashboard, name='home'),
]