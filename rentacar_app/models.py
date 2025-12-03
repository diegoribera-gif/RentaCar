from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from datetime import date

class Cliente(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cliente')
    cedula_identidad = models.CharField(max_length=15, unique=True)
    telefono = models.CharField(max_length=15)
    direccion = models.TextField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    licencia_conducir = models.CharField(max_length=20)
    fecha_vencimiento_licencia = models.DateField()
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} - CI: {self.cedula_identidad}"
    
    @property
    def licencia_valida(self):
        return self.fecha_vencimiento_licencia >= date.today()

class Vehiculo(models.Model):
    TIPOS_VEHICULO = [
        ('SEDAN', 'Sedán'),
        ('SUV', 'SUV'),
        ('PICKUP', 'Pickup'),
        ('VAN', 'Van'),
        ('DEPORTIVO', 'Deportivo'),
    ]
    
    ESTADOS = [
        ('DISPONIBLE', 'Disponible'),
        ('RESERVADO', 'Reservado'),
        ('MANTENIMIENTO', 'En Mantenimiento'),
        ('INACTIVO', 'Inactivo'),
    ]
    
    placa = models.CharField(max_length=10, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    año = models.IntegerField(validators=[MinValueValidator(2000)])
    tipo = models.CharField(max_length=20, choices=TIPOS_VEHICULO)
    capacidad_pasajeros = models.IntegerField()
    precio_dia = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='DISPONIBLE')
    imagen = models.ImageField(upload_to='vehiculos/', null=True, blank=True)
    descripcion = models.TextField(blank=True)
    kilometraje = models.IntegerField(default=0)
    fecha_adquisicion = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
    
    def __str__(self):
        return f"{self.marca} {self.modelo} - {self.placa}"
    
    @property
    def disponible_para_reserva(self):
        return self.estado == 'DISPONIBLE'

class Reserva(models.Model):
    ESTADOS_RESERVA = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('ACTIVA', 'Activa'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='reservas')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='reservas')
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS_RESERVA, default='PENDIENTE')
    precio_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observaciones = models.TextField(blank=True)
    codigo_reserva = models.CharField(max_length=10, unique=True, blank=True)
    
    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-fecha_reserva']
    
    def __str__(self):
        return f"Reserva {self.codigo_reserva} - {self.cliente}"
    
    def save(self, *args, **kwargs):
        # Calcular precio total si tenemos las fechas y el vehículo
        if self.fecha_inicio and self.fecha_fin and self.vehiculo:
            dias = (self.fecha_fin - self.fecha_inicio).days
            if dias < 1:
                dias = 1
            self.precio_total = dias * self.vehiculo.precio_dia
        
        # Si es un nuevo registro y no tiene código de reserva
        if not self.pk and not self.codigo_reserva:
            # Guardamos primero para obtener el ID (sin el código)
            super().save(*args, **kwargs)
            # Generamos el código con el ID
            self.codigo_reserva = f"R{self.id:06d}"
            # Actualizamos el registro con el código
            super().save(update_fields=['codigo_reserva'])
        else:
            # Para actualizaciones o si ya tiene código
            if not self.codigo_reserva and self.id:
                self.codigo_reserva = f"R{self.id:06d}"
            super().save(*args, **kwargs)
    
    @property
    def duracion_dias(self):
        if self.fecha_inicio and self.fecha_fin:
            return (self.fecha_fin - self.fecha_inicio).days
        return 0

class Contrato(models.Model):
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='contrato')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    terminos_condiciones = models.TextField()
    firmado = models.BooleanField(default=False)
    fecha_firma = models.DateTimeField(null=True, blank=True)
    archivo_pdf = models.FileField(upload_to='contratos/', null=True, blank=True)
    
    class Meta:
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"
    
    def __str__(self):
        return f"Contrato - {self.reserva.codigo_reserva}"

class Reporte(models.Model):
    TIPOS_REPORTE = [
        ('FINANCIERO', 'Reporte Financiero'),
        ('VEHICULOS', 'Reporte de Vehículos'),
        ('CLIENTES', 'Reporte de Clientes'),
        ('RESERVAS', 'Reporte de Reservas'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPOS_REPORTE)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    datos = models.JSONField()
    generado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.fecha_generacion.strftime('%d/%m/%Y')}"

class Empleado(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='empleado')
    telefono = models.CharField(max_length=15)
    direccion = models.TextField()
    fecha_contratacion = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
    
    def __str__(self):
        return f"{self.usuario.get_full_name()}"