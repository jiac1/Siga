import base64

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from .procesador import procesar_archivo

TAMANO_MAXIMO = 20 * 1024 * 1024  # 20 MB


def home(request):
    return render(request, 'heatmap/home.html')


def procesar(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    archivo = request.FILES.get('archivo')
    if not archivo:
        return render(request, 'heatmap/home.html', {'error': 'No se recibió ningún archivo.'})

    if not archivo.name.lower().endswith('.xlsx'):
        return render(request, 'heatmap/home.html', {'error': 'Solo se aceptan archivos .xlsx'})

    if archivo.size > TAMANO_MAXIMO:
        return render(request, 'heatmap/home.html', {'error': 'El archivo supera el máximo de 20 MB.'})

    try:
        resultado = procesar_archivo(archivo)

        # El Excel generado viaja en la propia página (enlace data:) en vez de
        # guardarse en sesión: así el servicio no guarda estado y puede correr
        # en varias instancias detrás del balanceador de AWS sin sesiones
        # compartidas. (El prototipo usaba la sesión.)
        excel_b64 = base64.b64encode(resultado['excel_bytes'].read()).decode('ascii')
        nombre_excel = archivo.name[:-5] + '_heatmap.xlsx'

        context = {
            'heatmap_data':      resultado['heatmap_data'],
            'salas_libres_data': resultado['salas_libres_data'],
            'indice_data':       resultado['indice_data'],
            'stats':             resultado['stats'],
            'days':              resultado['days'],
            'nombre_archivo':    archivo.name,
            'excel_b64':         excel_b64,
            'excel_nombre':      nombre_excel,
        }
        return render(request, 'heatmap/resultados.html', context)

    except ValueError as e:
        return render(request, 'heatmap/home.html', {'error': str(e)})
    except Exception as e:
        return render(request, 'heatmap/home.html', {'error': f'Error al procesar: {str(e)}'})


def descargar_excel(request):
    """Compatibilidad con enlaces antiguos: el Excel ahora se descarga desde la página de resultados."""
    excel_b64 = request.session.get('excel_data') if hasattr(request, 'session') else None
    if not excel_b64:
        return HttpResponse('El Excel se descarga directamente desde la página de resultados. '
                            'Procesa un archivo nuevamente.', status=410)
    response = HttpResponse(
        base64.b64decode(excel_b64),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{request.session.get("excel_nombre", "heatmap.xlsx")}"'
    return response
