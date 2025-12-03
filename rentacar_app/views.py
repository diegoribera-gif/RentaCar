from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User 
from django.contrib import messages  # ✅ IMPORTACIÓN AÑADIDA
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from decimal import Decimal
import json
from django.db.models import Sum, Count, Avg
from datetime import datetime, timedelta

from .models import Cliente, Vehiculo, Reserva, Contrato, Reporte, Empleado
from .forms import ClienteForm, VehiculoForm, ReservaForm, UserForm, EmpleadoForm, EmpleadoUserForm
from .utils import (
    generar_contrato_pdf, generar_reporte_pdf, generar_reporte_vehiculos, 
    generar_reporte_clientes, verificar_disponibilidad_vehiculo,
    generar_reporte_financiero, generar_reporte_reservas
)

def inicio(request):
    """Página principal pública del sistema"""
    # Obtener todos los vehículos disponibles
    vehiculos = Vehiculo.objects.filter(estado='DISPONIBLE')[:6]  # Mostrar solo 6
    
    # Si hay más de 6, mostrar indicador
    total_vehiculos = Vehiculo.objects.filter(estado='DISPONIBLE').count()
    
    context = {
        'vehiculos': vehiculos,
        'total_vehiculos': total_vehiculos,
        'titulo': 'Sistema RentaCar - Alquiler de Vehículos'
    }
    return render(request, 'inicio.html', context)


# ✅ FUNCIONES DE VERIFICACIÓN DE ROLES
def es_administrador(user):
    return user.is_authenticated and (user.is_staff or hasattr(user, 'empleado'))

def es_empleado(user):
    return user.is_authenticated and hasattr(user, 'empleado')

def es_cliente(user):
    return user.is_authenticated and hasattr(user, 'cliente')

def get_user_role(user):
    """Determina el rol del usuario"""
    if user.is_staff:
        return 'administrador'
    elif hasattr(user, 'empleado'):
        return 'empleado'
    elif hasattr(user, 'cliente'):
        return 'cliente'
    else:
        return 'sin_rol'

# Vistas de Autenticación
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Credenciales inválidas'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        # ✅ Usar UserForm (TIENE first_name, last_name, email)
        user_form = UserForm(request.POST)
        cliente_form = ClienteForm(request.POST)
        
        if user_form.is_valid() and cliente_form.is_valid():
            # Guardar usuario CON todos los datos
            user = user_form.save()
            
            # Guardar cliente vinculado al usuario
            cliente = cliente_form.save(commit=False)
            cliente.usuario = user  # Vincular cliente al usuario
            
            # Guardar cliente
            cliente.save()
            
            # Iniciar sesión
            login(request, user)
            
            # Mensaje de éxito
            messages.success(request, '¡Registro exitoso! Bienvenido a RentaCar.')
            
            return redirect('dashboard')
        else:
            # ✅ MOSTRAR ERRORES DETALLADOS
            error_messages = []
            
            # Errores del formulario de usuario
            if user_form.errors:
                for field, errors in user_form.errors.items():
                    for error in errors:
                        error_messages.append(f"{field}: {error}")
            
            # Errores del formulario de cliente
            if cliente_form.errors:
                for field, errors in cliente_form.errors.items():
                    for error in errors:
                        error_messages.append(f"{field}: {error}")
            
            # Mostrar todos los errores
            for error_msg in error_messages:
                messages.error(request, error_msg)
    else:
        user_form = UserForm()
        cliente_form = ClienteForm()
    
    return render(request, 'register.html', {
        'user_form': user_form,
        'cliente_form': cliente_form
    })

@login_required
def dashboard(request):
    user_role = get_user_role(request.user)
    
    # Datos comunes
    total_vehiculos = Vehiculo.objects.count()
    
    if user_role == 'administrador' or user_role == 'empleado':
        # Dashboard para administradores y empleados (MANTENER EXISTENTE)
        total_clientes = Cliente.objects.count()
        total_reservas = Reserva.objects.count()
        reservas_activas = Reserva.objects.filter(estado='ACTIVA').count()
        
        mes_actual = timezone.now().month
        año_actual = timezone.now().year
        ingresos_mes = Reserva.objects.filter(
            fecha_reserva__month=mes_actual,
            fecha_reserva__year=año_actual,
            estado__in=['COMPLETADA', 'ACTIVA']
        ).aggregate(total=Sum('precio_total'))['total'] or 0
        
        reservas_recientes = Reserva.objects.select_related('cliente', 'vehiculo').order_by('-fecha_reserva')[:5]
        vehiculos_populares = Vehiculo.objects.annotate(num_reservas=Count('reservas')).order_by('-num_reservas')[:3]
        
        context = {
            'user_role': user_role,
            'total_clientes': total_clientes,
            'total_vehiculos': total_vehiculos,
            'total_reservas': total_reservas,
            'reservas_activas': reservas_activas,
            'ingresos_mes': ingresos_mes,
            'reservas_recientes': reservas_recientes,
            'vehiculos_populares': vehiculos_populares,
        }
        
    else:
        # ========== DASHBOARD PARA CLIENTES (ACTUALIZADO) ==========
        cliente = request.user.cliente
        mis_reservas = Reserva.objects.filter(cliente=cliente).order_by('-fecha_reserva')[:5]
        reservas_activas = Reserva.objects.filter(cliente=cliente, estado='ACTIVA').count()
        vehiculos_disponibles = Vehiculo.objects.filter(estado='DISPONIBLE').count()
        
        # Contar contratos disponibles
        contratos_disponibles = 0
        for reserva in mis_reservas:
            if reserva.contrato:
                contratos_disponibles += 1
        
        context = {
            'user_role': user_role,
            'cliente': cliente,
            'mis_reservas': mis_reservas,
            'reservas_activas': reservas_activas,
            'vehiculos_disponibles': vehiculos_disponibles,
            'contratos_disponibles': contratos_disponibles,
            'total_vehiculos': total_vehiculos,
        }
    
    return render(request, 'dashboard.html', context)

# Vistas de Clientes
@login_required
def lista_clientes(request):
    clientes = Cliente.objects.select_related('usuario').all()
    return render(request, 'clientes/lista.html', {'clientes': clientes})

@login_required
def crear_cliente(request):
    """
    Vista para crear cliente desde el panel administrativo
    """
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        cliente_form = ClienteForm(request.POST)
        if user_form.is_valid() and cliente_form.is_valid():
            user = user_form.save()
            cliente = cliente_form.save(commit=False)
            cliente.usuario = user
            
            # ✅ AÑADIR: Calcular estado de licencia
            from datetime import date
            fecha_vencimiento = cliente.fecha_vencimiento_licencia
            cliente.licencia_valida = fecha_vencimiento >= date.today() if fecha_vencimiento else False
            
            cliente.save()
            messages.success(request, 'Cliente creado exitosamente.')
            return redirect('lista_clientes')
    else:
        user_form = UserForm()
        cliente_form = ClienteForm()
    return render(request, 'clientes/crear.html', {
        'user_form': user_form,
        'cliente_form': cliente_form
    })

# Vistas de Vehículos
@login_required
def lista_vehiculos(request):
    vehiculos = Vehiculo.objects.all()
    
    # ✅ DEBUG: Verificar qué datos se están obteniendo
    print(f"DEBUG: Se encontraron {vehiculos.count()} vehículos")
    for vehiculo in vehiculos:
        print(f"DEBUG: {vehiculo.marca} {vehiculo.modelo} - {vehiculo.placa}")
    
    return render(request, 'vehiculos/lista.html', {'vehiculos': vehiculos})

@login_required
def crear_vehiculo(request):
    if request.method == 'POST':
        form = VehiculoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_vehiculos')
    else:
        form = VehiculoForm()
    return render(request, 'vehiculos/crear.html', {'form': form})

@login_required
def disponibilidad_vehiculos(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    vehiculos = Vehiculo.objects.filter(estado='DISPONIBLE')
    
    if fecha_inicio and fecha_fin:
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
            
            reservas_conflictivas = Reserva.objects.filter(
                Q(fecha_inicio__lte=fecha_fin_dt) & Q(fecha_fin__gte=fecha_inicio_dt),
                estado__in=['CONFIRMADA', 'ACTIVA', 'PENDIENTE']
            )
            vehiculos_reservados_ids = reservas_conflictivas.values_list('vehiculo_id', flat=True)
            vehiculos = vehiculos.exclude(id__in=vehiculos_reservados_ids)
            
        except ValueError:
            pass
    
    return render(request, 'vehiculos/disponibilidad.html', {
        'vehiculos': vehiculos,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    })

# Vistas de Reservas
@login_required
def lista_reservas(request):
    reservas = Reserva.objects.select_related('cliente', 'vehiculo').all()
    return render(request, 'reservas/lista.html', {'reservas': reservas})

@login_required
def crear_reserva(request):
    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            reserva = form.save()
            return redirect('detalle_reserva', reserva_id=reserva.id)
    else:
        form = ReservaForm()
    return render(request, 'reservas/crear.html', {'form': form})

@login_required
def detalle_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    return render(request, 'reservas/detalle.html', {'reserva': reserva})

@login_required
@user_passes_test(es_administrador)
def reportes(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        formato = request.POST.get('formato', 'web')
        
        # Generar reporte según el tipo
        if tipo == 'FINANCIERO':
            datos = generar_reporte_financiero(fecha_inicio, fecha_fin)
        elif tipo == 'RESERVAS':
            datos = generar_reporte_reservas(fecha_inicio, fecha_fin)
        elif tipo == 'VEHICULOS':
            datos = generar_reporte_vehiculos()
        else:
            datos = generar_reporte_clientes()
        
        # CONVERTIR DATOS DECIMAL A FLOAT PARA JSON
        datos = convertir_decimal_a_float(datos)
        
        if formato == 'pdf':
            pdf_buffer = generar_reporte_pdf(datos, tipo)
            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            filename = f"reporte_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
        # Guardar reporte en base de datos
        reporte = Reporte.objects.create(
            tipo=tipo,
            fecha_inicio=fecha_inicio if fecha_inicio else None,
            fecha_fin=fecha_fin if fecha_fin else None,
            datos=datos,
            generado_por=request.user
        )
        
        return render(request, 'reportes/resultado.html', {
            'reporte': reporte,
            'datos': datos,
            'tipo': tipo
        })
    
    return render(request, 'reportes/generar.html')

# ========== FUNCIÓN PARA CONVERTIR DECIMAL A FLOAT ==========

def convertir_decimal_a_float(datos):
    """
    Convierte todos los valores Decimal en un diccionario/listas a float
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


# API para disponibilidad en tiempo real
@login_required
def api_disponibilidad(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if not fecha_inicio or not fecha_fin:
        return JsonResponse({'error': 'Fechas requeridas'}, status=400)
    
    try:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
        
        vehiculos_disponibles = Vehiculo.objects.filter(estado='DISPONIBLE')
        
        reservas_conflictivas = Reserva.objects.filter(
            Q(fecha_inicio__lte=fecha_fin_dt) & Q(fecha_fin__gte=fecha_inicio_dt),
            estado__in=['CONFIRMADA', 'ACTIVA', 'PENDIENTE']
        )
        vehiculos_no_disponibles = reservas_conflictivas.values_list('vehiculo_id', flat=True)
        vehiculos_disponibles = vehiculos_disponibles.exclude(id__in=vehiculos_no_disponibles)
        
        datos = []
        for vehiculo in vehiculos_disponibles:
            datos.append({
                'id': vehiculo.id,
                'marca': vehiculo.marca,
                'modelo': vehiculo.modelo,
                'placa': vehiculo.placa,
                'precio_dia': float(vehiculo.precio_dia),
                'tipo': vehiculo.get_tipo_display(),
                'imagen_url': vehiculo.imagen.url if vehiculo.imagen else None
            })
        
        return JsonResponse({'vehiculos': datos})
    
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)

# Añadir esta vista para descargar contratos
@login_required
def descargar_contrato(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    pdf_buffer = generar_contrato_pdf(reserva)
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    filename = f"contrato_{reserva.codigo_reserva}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

# Añadir esta vista para el perfil del cliente
@login_required
def perfil_cliente(request):
    if hasattr(request.user, 'cliente'):
        cliente = request.user.cliente
        reservas = Reserva.objects.filter(cliente=cliente).order_by('-fecha_reserva')
        return render(request, 'clientes/perfil.html', {
            'cliente': cliente,
            'reservas': reservas
        })
    else:
        return redirect('dashboard')

# ✅ VISTAS PARA EMPLEADOS (solo administradores)
@login_required
@user_passes_test(es_administrador)
def lista_empleados(request):
    empleados = Empleado.objects.select_related('usuario').all()
    return render(request, 'empleados/lista.html', {'empleados': empleados})

@login_required
@user_passes_test(es_administrador)
def crear_empleado(request):
    if request.method == 'POST':
        user_form = EmpleadoUserForm(request.POST)
        empleado_form = EmpleadoForm(request.POST)
        if user_form.is_valid() and empleado_form.is_valid():
            user = user_form.save()
            empleado = empleado_form.save(commit=False)
            empleado.usuario = user
            empleado.save()
            messages.success(request, 'Empleado creado exitosamente!')
            return redirect('lista_empleados')
    else:
        user_form = EmpleadoUserForm()
        empleado_form = EmpleadoForm()
    
    return render(request, 'empleados/crear.html', {
        'user_form': user_form,
        'empleado_form': empleado_form
    })

@login_required
@user_passes_test(es_administrador)
def desactivar_empleado(request, empleado_id):
    """Desactivar empleado (no eliminar para mantener historial)"""
    empleado = get_object_or_404(Empleado, id=empleado_id)
    if request.method == 'POST':
        empleado.activo = False
        empleado.save()
        messages.success(request, f'Empleado {empleado.usuario.get_full_name()} desactivado exitosamente.')
        return redirect('lista_empleados')
    
    return render(request, 'empleados/confirmar_desactivar.html', {'empleado': empleado})

@login_required
@user_passes_test(es_administrador)
def activar_empleado(request, empleado_id):
    """Activar empleado previamente desactivado"""
    empleado = get_object_or_404(Empleado, id=empleado_id)
    if request.method == 'POST':
        empleado.activo = True
        empleado.save()
        messages.success(request, f'Empleado {empleado.usuario.get_full_name()} activado exitosamente.')
        return redirect('lista_empleados')
    
    return render(request, 'empleados/confirmar_activar.html', {'empleado': empleado})

# ========== VISTAS PARA EMPLEADOS (COMPLETAS) ==========

@login_required
@user_passes_test(es_administrador)
def detalle_empleado(request, empleado_id):
    """Ver detalles de un empleado específico"""
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    # Obtener estadísticas del empleado
    reservas_gestionadas = Reserva.objects.filter(
        gestionado_por=empleado
    ).count() if hasattr(empleado, 'reservas_gestionadas') else 0
    
    return render(request, 'empleados/detalle.html', {
        'empleado': empleado,
        'reservas_gestionadas': reservas_gestionadas
    })

@login_required
@user_passes_test(es_administrador)
def editar_empleado(request, empleado_id):
    """Editar un empleado existente - CON CAMBIO DE CONTRASEÑA"""
    empleado = get_object_or_404(Empleado, id=empleado_id)
    usuario = empleado.usuario
    
    if request.method == 'POST':
        empleado_form = EmpleadoForm(request.POST, instance=empleado)
        
        if empleado_form.is_valid():
            # Obtener datos del formulario
            nuevo_username = request.POST.get('username', '').strip()
            nuevo_email = request.POST.get('email', '').strip()
            nuevo_first_name = request.POST.get('first_name', '').strip()
            nuevo_last_name = request.POST.get('last_name', '').strip()
            nueva_password = request.POST.get('password1', '').strip()
            confirmar_password = request.POST.get('password2', '').strip()
            
            # Validar campos obligatorios
            if not nuevo_username:
                messages.error(request, 'El nombre de usuario es obligatorio.')
                return render(request, 'empleados/editar.html', {
                    'empleado_form': empleado_form,
                    'empleado': empleado,
                    'usuario': usuario
                })
            
            if not nuevo_email:
                messages.error(request, 'El email es obligatorio.')
                return render(request, 'empleados/editar.html', {
                    'empleado_form': empleado_form,
                    'empleado': empleado,
                    'usuario': usuario
                })
            
            # Validar contraseñas si se proporcionaron
            if nueva_password or confirmar_password:
                if nueva_password != confirmar_password:
                    messages.error(request, 'Las contraseñas no coinciden.')
                    return render(request, 'empleados/editar.html', {
                        'empleado_form': empleado_form,
                        'empleado': empleado,
                        'usuario': usuario
                    })
                if len(nueva_password) < 8:
                    messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
                    return render(request, 'empleados/editar.html', {
                        'empleado_form': empleado_form,
                        'empleado': empleado,
                        'usuario': usuario
                    })
            
            # Verificar si el username cambió
            if nuevo_username != usuario.username:
                if User.objects.filter(username=nuevo_username).exclude(id=usuario.id).exists():
                    messages.error(request, 'Ya existe un usuario con este nombre de usuario.')
                    return render(request, 'empleados/editar.html', {
                        'empleado_form': empleado_form,
                        'empleado': empleado,
                        'usuario': usuario
                    })
                usuario.username = nuevo_username
            
            # Verificar si el email cambió
            if nuevo_email != usuario.email:
                if User.objects.filter(email=nuevo_email).exclude(id=usuario.id).exists():
                    messages.error(request, 'Ya existe un usuario con este email.')
                    return render(request, 'empleados/editar.html', {
                        'empleado_form': empleado_form,
                        'empleado': empleado,
                        'usuario': usuario
                    })
                usuario.email = nuevo_email
            
            # Actualizar nombres y apellidos
            usuario.first_name = nuevo_first_name
            usuario.last_name = nuevo_last_name
            
            # Cambiar contraseña si se proporcionó una nueva
            if nueva_password:
                usuario.set_password(nueva_password)
                messages.info(request, 'Contraseña actualizada correctamente.')
            
            # Guardar cambios del usuario
            usuario.save()
            
            # Guardar cambios del empleado
            empleado_form.save()
            
            messages.success(request, '¡Empleado actualizado exitosamente!')
            return redirect('detalle_empleado', empleado_id=empleado.id)
        else:
            # Mostrar errores del formulario
            for field, errors in empleado_form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        empleado_form = EmpleadoForm(instance=empleado)
    
    return render(request, 'empleados/editar.html', {
        'empleado_form': empleado_form,
        'empleado': empleado,
        'usuario': usuario
    })

@login_required
@user_passes_test(es_administrador)
def eliminar_empleado(request, empleado_id):
    """Eliminar permanentemente un empleado"""
    empleado = get_object_or_404(Empleado, id=empleado_id)
    usuario = empleado.usuario
    nombre_completo = usuario.get_full_name()
    
    if request.method == 'POST':
        # Verificar si el empleado tiene reservas gestionadas
        # Primero, verifica qué campo relaciona reservas con empleados
        # Si no existe 'gestionado_por', probablemente se llame 'empleado' o no exista
        try:
            # Intenta diferentes nombres de campo
            reservas_count = 0
            if hasattr(Reserva, 'empleado'):
                reservas_count = Reserva.objects.filter(empleado=empleado).count()
            elif hasattr(Reserva, 'gestionado_por'):
                reservas_count = Reserva.objects.filter(gestionado_por=empleado).count()
            elif hasattr(Reserva, 'empleado_reserva'):
                reservas_count = Reserva.objects.filter(empleado_reserva=empleado).count()
            
            if reservas_count > 0:
                messages.error(
                    request, 
                    f'No se puede eliminar el empleado {nombre_completo} porque tiene {reservas_count} reservas gestionadas.'
                )
                return redirect('detalle_empleado', empleado_id=empleado.id)
        except Exception as e:
            # Si hay error al verificar, continuar con eliminación
            print(f"Error al verificar reservas: {e}")
        
        # Eliminar empleado y usuario
        empleado.delete()
        usuario.delete()
        
        messages.success(request, f'Empleado {nombre_completo} eliminado exitosamente!')
        return redirect('lista_empleados')
    
    return render(request, 'empleados/eliminar.html', {'empleado': empleado})

# ✅ VISTA TEMPORAL PARA DIAGNÓSTICO
@login_required
def diagnostico_vehiculos(request):
    """Vista de diagnóstico para vehículos"""
    vehiculos = Vehiculo.objects.all()
    datos = {
        'total_vehiculos': vehiculos.count(),
        'vehiculos': list(vehiculos.values('marca', 'modelo', 'placa', 'estado')),
        'usuario_autenticado': request.user.is_authenticated,
        'usuario': request.user.username,
    }
    
    return JsonResponse(datos)

# ========== VISTAS PARA CLIENTES (AGREGAR AL FINAL DEL ARCHIVO) ==========

@login_required
def detalle_cliente(request, cliente_id):
    """Ver detalles de un cliente específico"""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    reservas = Reserva.objects.filter(cliente=cliente).order_by('-fecha_reserva')[:10]
    
    return render(request, 'clientes/detalle.html', {
        'cliente': cliente,
        'reservas': reservas
    })

@login_required
def editar_cliente(request, cliente_id):
    """Editar un cliente existente - VERSIÓN SIMPLE CORREGIDA"""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    usuario = cliente.usuario  # Obtener el usuario asociado al cliente
    
    if request.method == 'POST':
        cliente_form = ClienteForm(request.POST, instance=cliente)
        
        if cliente_form.is_valid():
            # Obtener datos del formulario
            nuevo_username = request.POST.get('username', '').strip()
            nuevo_email = request.POST.get('email', '').strip()
            nuevo_first_name = request.POST.get('first_name', '').strip()
            nuevo_last_name = request.POST.get('last_name', '').strip()
            
            # Validar campos obligatorios
            if not nuevo_username:
                messages.error(request, 'El nombre de usuario es obligatorio.')
                return render(request, 'clientes/editar.html', {
                    'cliente_form': cliente_form,
                    'cliente': cliente,
                    'usuario': usuario
                })
            
            if not nuevo_email:
                messages.error(request, 'El email es obligatorio.')
                return render(request, 'clientes/editar.html', {
                    'cliente_form': cliente_form,
                    'cliente': cliente,
                    'usuario': usuario
                })
            
            # Verificar si el username cambió
            if nuevo_username != usuario.username:
                # Verificar si ya existe otro usuario con ese username
                if User.objects.filter(username=nuevo_username).exclude(id=usuario.id).exists():
                    messages.error(request, 'Ya existe un usuario con este nombre de usuario.')
                    return render(request, 'clientes/editar.html', {
                        'cliente_form': cliente_form,
                        'cliente': cliente,
                        'usuario': usuario
                    })
                usuario.username = nuevo_username
            
            # Verificar si el email cambió
            if nuevo_email != usuario.email:
                # Verificar si ya existe otro usuario con ese email
                if User.objects.filter(email=nuevo_email).exclude(id=usuario.id).exists():
                    messages.error(request, 'Ya existe un usuario con este email.')
                    return render(request, 'clientes/editar.html', {
                        'cliente_form': cliente_form,
                        'cliente': cliente,
                        'usuario': usuario
                    })
                usuario.email = nuevo_email
            
            # Actualizar nombres y apellidos (pueden estar vacíos)
            usuario.first_name = nuevo_first_name
            usuario.last_name = nuevo_last_name
            
            # Guardar cambios
            usuario.save()
            cliente_form.save()
            
            messages.success(request, '¡Cliente actualizado exitosamente!')
            return redirect('detalle_cliente', cliente_id=cliente.id)
        else:
            # Mostrar errores del formulario si no es válido
            for field, errors in cliente_form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        cliente_form = ClienteForm(instance=cliente)
    
    return render(request, 'clientes/editar.html', {
        'cliente_form': cliente_form,
        'cliente': cliente,
        'usuario': usuario
    })

@login_required
def eliminar_cliente(request, cliente_id):
    """Eliminar un cliente"""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'POST':
        # También eliminar el usuario asociado
        usuario = cliente.usuario
        cliente.delete()
        usuario.delete()
        messages.success(request, 'Cliente eliminado exitosamente!')
        return redirect('lista_clientes')
    
    return render(request, 'clientes/eliminar.html', {'cliente': cliente})

@login_required
def activar_cliente(request, cliente_id):
    """Activar/desactivar cliente"""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'POST':
        cliente.activo = not cliente.activo
        cliente.save()
        
        estado = "activado" if cliente.activo else "desactivado"
        messages.success(request, f'Cliente {estado} exitosamente!')
    
    return redirect('lista_clientes')


# ========== VISTAS PARA VEHÍCULOS (AGREGAR AL FINAL DEL ARCHIVO) ==========

@login_required
def detalle_vehiculo(request, vehiculo_id):
    """Ver detalles de un vehículo específico"""
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    reservas = Reserva.objects.filter(vehiculo=vehiculo).order_by('-fecha_reserva')[:10]
    
    return render(request, 'vehiculos/detalle.html', {
        'vehiculo': vehiculo,
        'reservas': reservas
    })

@login_required
def editar_vehiculo(request, vehiculo_id):
    """Editar un vehículo existente"""
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    
    if request.method == 'POST':
        form = VehiculoForm(request.POST, request.FILES, instance=vehiculo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vehículo actualizado exitosamente!')
            return redirect('detalle_vehiculo', vehiculo_id=vehiculo.id)
    else:
        form = VehiculoForm(instance=vehiculo)
    
    return render(request, 'vehiculos/editar.html', {
        'form': form,
        'vehiculo': vehiculo
    })

@login_required
def eliminar_vehiculo(request, vehiculo_id):
    """Eliminar un vehículo"""
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    
    if request.method == 'POST':
        vehiculo.delete()
        messages.success(request, 'Vehículo eliminado exitosamente!')
        return redirect('lista_vehiculos')
    
    return render(request, 'vehiculos/eliminar.html', {'vehiculo': vehiculo})

@login_required
def activar_vehiculo(request, vehiculo_id):
    """Activar/desactivar vehículo"""
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    
    if request.method == 'POST':
        vehiculo.disponible = not vehiculo.disponible
        vehiculo.save()
        
        estado = "activado" if vehiculo.disponible else "desactivado"
        messages.success(request, f'Vehículo {estado} exitosamente!')
    
    return redirect('lista_vehiculos')


# ========== VISTAS PARA RESERVAS (AGREGAR AL FINAL DEL ARCHIVO) ==========

@login_required
def editar_reserva(request, reserva_id):
    """Editar una reserva existente"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    if request.method == 'POST':
        form = ReservaForm(request.POST, instance=reserva)
        if form.is_valid():
            # Calcular precio total si cambió el vehículo o las fechas
            reserva_editada = form.save(commit=False)
            
            # Recalcular días si cambiaron las fechas
            if reserva_editada.fecha_inicio and reserva_editada.fecha_fin:
                diferencia = reserva_editada.fecha_fin - reserva_editada.fecha_inicio
                dias = diferencia.days + 1
                
                # Calcular precio total
                if reserva_editada.vehiculo:
                    reserva_editada.precio_total = dias * reserva_editada.vehiculo.precio_dia
            
            reserva_editada.save()
            messages.success(request, 'Reserva actualizada exitosamente!')
            return redirect('detalle_reserva', reserva_id=reserva.id)
    else:
        form = ReservaForm(instance=reserva)
    
    return render(request, 'reservas/editar.html', {
        'form': form,
        'reserva': reserva
    })

@login_required
def eliminar_reserva(request, reserva_id):
    """Eliminar una reserva"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    if request.method == 'POST':
        reserva.delete()
        messages.success(request, 'Reserva eliminada exitosamente!')
        return redirect('lista_reservas')
    
    return render(request, 'reservas/eliminar.html', {'reserva': reserva})

@login_required
def confirmar_reserva(request, reserva_id):
    """Confirmar una reserva pendiente"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    if request.method == 'POST':
        if reserva.estado == 'PENDIENTE':
            reserva.estado = 'CONFIRMADA'
            reserva.save()
            messages.success(request, f'Reserva {reserva.codigo_reserva} confirmada exitosamente!')
        else:
            messages.warning(request, 'Solo se pueden confirmar reservas pendientes.')
    
    return redirect('detalle_reserva', reserva_id=reserva.id)

@login_required
def cancelar_reserva(request, reserva_id):
    """Cancelar una reserva"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    if request.method == 'POST':
        if reserva.estado in ['PENDIENTE', 'CONFIRMADA', 'ACTIVA']:
            reserva.estado = 'CANCELADA'
            reserva.save()
            messages.success(request, f'Reserva {reserva.codigo_reserva} cancelada exitosamente!')
        else:
            messages.warning(request, 'No se puede cancelar una reserva en este estado.')
    
    return redirect('detalle_reserva', reserva_id=reserva.id)