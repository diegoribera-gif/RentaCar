def user_role(request):
    """Context processor para pasar el rol del usuario a todos los templates"""
    def get_user_role(user):
        if user.is_authenticated:
            if user.is_staff:
                return 'administrador'
            elif hasattr(user, 'empleado'):
                return 'empleado'
            elif hasattr(user, 'cliente'):
                return 'cliente'
        return 'anonimo'
    
    return {
        'user_role': get_user_role(request.user) if request.user.is_authenticated else 'anonimo'
    }