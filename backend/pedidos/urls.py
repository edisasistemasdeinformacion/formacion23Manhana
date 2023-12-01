from rest_framework import routers
from django.urls import path
from .api import WebPedidosViewSet, WebPedidosLinViewSet, IntegraPedidoViewSet, ActualizaPedidoViewSet, TiposPedidoVtaViewSet, TextosVentasViewSet, DescuentosTramosHorariosClienteViewSet, EcomFormasEnvioTarifasViewSet

router = routers.DefaultRouter()
router.register('lineas', WebPedidosLinViewSet, 'lineas')
router.register('pedidos', WebPedidosViewSet, 'pedidos')
router.register('integrapedido', IntegraPedidoViewSet, 'integrapedido')
router.register('actualizapedido', ActualizaPedidoViewSet, 'actualizapedido')
router.register('tipospedido', TiposPedidoVtaViewSet, 'tipospedido')
router.register('textosventas', TextosVentasViewSet, 'textosventas')
router.register('dtostramohorario',
                DescuentosTramosHorariosClienteViewSet, 'dtostramohorario')
router.register('tarifasEnvioPortes',
                EcomFormasEnvioTarifasViewSet, 'tarifasEnvioPortes')

urlpatterns = router.urls
