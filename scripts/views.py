from esper.views import register_view
from django.http import JsonResponse


# Example view that incremental an id parameter by one.
# Visit /api/example?id=1 and it should return {"id": 2}.
@register_view(r'^api/example', name='example')
def example(request):
    id = request.GET.get('id')
    return JsonResponse({'id': int(id) + 1})
