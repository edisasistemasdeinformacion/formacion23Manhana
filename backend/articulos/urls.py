from rest_framework import routers
from django.urls import path
from .api import ArticuloViewSet, CadenaLogisticaViewSet, PrecioViewSet, FamiliaViewSet, ImagenViewSet, DescargarImagenes, GaleriaViewSet,\
    FiltrosViewSet, StockViewSet, EcomArtAgrupHijosViewSet, EcomArtAgrupCondViewSet, ArticulosDocViewSet, ArticulosAuxViewSet,\
    EcomSubPresentacionesViewSet, FamiliasImagenesViewSet, CodigosBarrasViewSet, PresentacionesViewSet, PresenArticuloViewSet, \
    SugerenciasViewSet, ClavesEstadisticasArtViewSet, ArticulosClavesEstadisticasViewSet,OfertasMultiplesViewSet, StockAluminioViewSet

router = routers.DefaultRouter()
router.register('articulos', ArticuloViewSet, 'articulos')
router.register('precio', PrecioViewSet, 'precio')
router.register('familias', FamiliaViewSet, 'familias')
router.register('imagen', ImagenViewSet, 'imagen')
router.register('descargar_imagenes', DescargarImagenes, 'descargar_imagenes')
router.register('galeria', GaleriaViewSet, 'galeria')
router.register('filtros', FiltrosViewSet, 'filtros')
router.register('agrupacionhijos', EcomArtAgrupHijosViewSet, 'agrupacionhijos')
router.register('agrupacioncondiciones',
                EcomArtAgrupCondViewSet, 'agrupacioncondiciones')
router.register('stock', StockViewSet, 'stock')
router.register('articulosdoc', ArticulosDocViewSet, 'articulosdoc')
router.register('articulosaux', ArticulosAuxViewSet, 'articulosaux')
router.register('subpresentaciones',
                EcomSubPresentacionesViewSet, 'subpresentaciones')
router.register('familiasimagenes',
                FamiliasImagenesViewSet, 'familiasimagenes')
router.register('codigosbarras',
                CodigosBarrasViewSet, 'codigosbarras')
router.register('cadenalogistica',
                CadenaLogisticaViewSet, 'cadenalogistica')
router.register('presentaciones',
                PresentacionesViewSet, 'presentaciones')
router.register('presenarticulo',
                PresenArticuloViewSet, 'presenarticulo')
router.register('sugerencias',
                SugerenciasViewSet, 'sugerencias')
router.register('clavesestadisticas',
                ClavesEstadisticasArtViewSet, 'clavesestadisticas')
router.register('artclavesestadisticas',
                ArticulosClavesEstadisticasViewSet, 'artclavesestadisticas')
router.register('ofertasMultiples', OfertasMultiplesViewSet, 'ofertasMultiples')

router.register('stockAluminio', StockAluminioViewSet, 'stockAluminio')

urlpatterns = router.urls

# urlpatterns.append(
#    path('articulos/<int:codigo_articulo>/<slug:slug>', PrecioViewSet.list))
