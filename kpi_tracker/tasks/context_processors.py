def active_cycle(request):
    if not request.user.is_authenticated:
        return {}
    try:
        from .models import Cycle
        cycle_id = request.session.get('active_cycle_id')
        if cycle_id:
            try:
                cycle = Cycle.objects.get(id=cycle_id)
            except Cycle.DoesNotExist:
                cycle = Cycle.objects.filter(is_active=True).first() or Cycle.objects.order_by('-year').first()
        else:
            cycle = Cycle.objects.filter(is_active=True).first() or Cycle.objects.order_by('-year').first()
        if cycle and not cycle_id:
            request.session['active_cycle_id'] = cycle.id
        return {
            'active_cycle': cycle,
            'all_cycles': Cycle.objects.order_by('-year'),
        }
    except Exception:
        return {}
