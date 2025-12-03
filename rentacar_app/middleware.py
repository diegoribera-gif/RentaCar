from django.shortcuts import redirect
from django.contrib.auth import logout

def get_user_role(user):
    """Determina el rol del usuario"""
    if user.is_staff:
        return 'administrador'
    elif hasattr(user, 'cliente'):
        return 'cliente'
    else:
        return 'empleado'

class RoleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Si la vista tiene el atributo 'roles_permitidos', verificar acceso
        if hasattr(view_func, 'roles_permitidos'):
            if not request.user.is_authenticated:
                return redirect('login')
            
            user_role = get_user_role(request.user)
            if user_role not in view_func.roles_permitidos:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("No tiene permisos para acceder a esta página")
        
        return None

def roles_requeridos(roles):
    """Decorator para especificar roles requeridos en una vista"""
    def decorator(view_func):
        view_func.roles_permitidos = roles
        return view_func
    return decorator