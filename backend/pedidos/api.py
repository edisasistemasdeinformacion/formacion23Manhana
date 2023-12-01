from itertools import count
import simplejson as json
from portales.enconders import fecha_encoder
from django.http import Http404
from rest_framework.response import Response
from pedidos.models import WebPedidos, WebPedidosLin, TiposPedidoVta, DescuentosTramosHorariosCliente, EcomFormasEnvioTarifas
from articulos.models import EcomArticulosProvincias, Articulo
from rest_framework import viewsets, status
from .serializers import WebPedidosSerializer, WebPedidosLinSerializer, IntegraPedidoSerializer, TiposPedidoVtaSerializer, TextosVentasSerializer, DescuentosTramosHorariosClienteSerializer, EcomFormasEnvioTarifasSerializer
from rest_framework.decorators import action
from .helpers import procesa_linea, procesa_pedido
from formas_pago.models import FormasPago
from domicilios.models import DomiciliosEnvio, EcomAlmacenesProvincias
from pedidos.models import TextosVentas
from django.db.models import Q
from django.db.models import F
from usuarios import permisos
from .functions import ultimoPedido, calculaPortes, insertarLineaPedido, comprobarRiesgo, recalcularPedidoGrupos
import datetime
from portales.lisa import comunica_lisa
import logging
from usuarios.models import EcomUsuarioWebPermisos
from portal.functions import registraActividad
from django.utils import timezone
from django.db.models import Max, Count
from portal.functions import enviarAlerta

logger = logging.getLogger("rad_logger")

# Pedidos Viewset


class WebPedidosViewSet(viewsets.ModelViewSet):
    # queryset = WebPedidos.objects.all()
    permission_classes = [
        permisos.AllowSemiPrivate
    ]

    serializer_class = WebPedidosSerializer

    def get_queryset(self):

        portal = self.request.session['portal']
        usuario = self.request.user

        pedidos = WebPedidos.objects.filter(codigo_empresa=portal['codigo_empresa'],
                                            codigo_cliente=usuario.codigo_cliente)

        return pedidos

    def destroy(self, request, pk=None):

        pedido = ultimoPedido(self.request)

        if pedido.estado_pedido == 'A' or pedido.estado_pedido == 'P':

            pedido.estado_pedido = 'B'

            pedido.save()

            nuevo_pedido = ultimoPedido(self.request)

            pedido_serializado = WebPedidosSerializer(nuevo_pedido).data

            return Response(pedido_serializado, status=status.HTTP_201_CREATED)

        else:
            return Response('El pedido actual no está abierto, no puede eliminarse', status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):

        portal = self.request.session['portal']
        usuario = self.request.user

        if self.request.query_params.get('activo') is not None and self.request.query_params.get('activo') == 'S':
            pedidos = ultimoPedido(self.request)
            serializer = self.get_serializer(pedidos)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif self.request.query_params.get('anteriores') is not None and self.request.query_params.get('anteriores') == 'S':
            hoy = datetime.date.today()
            fecha = hoy - \
                datetime.timedelta(days=portal['dias_pedidos_anteriores'])

            pedidos = self.get_queryset().filter(
                fecha_valor__gte=fecha).order_by('-fecha_valor', '-id_pedido').exclude(estado_pedido='A')

            if portal['tipo_linea_pedidos'] == 'P':
                pedidos = pedidos.filter(numero_serie__isnull=False,
                                         numero_pedido__isnull=False)
            elif portal['tipo_linea_pedidos'] == 'O':
                pedidos = pedidos.filter(numero_serie_pres__isnull=False,
                                         numero_pres__isnull=False)
            else:
                pedidos = pedidos

            serializer = self.get_serializer(pedidos, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)
        elif self.request.query_params.get('pendientes') is not None and self.request.query_params.get('pendientes') == 'S':
            hoy = datetime.date.today()

            pedidos = self.get_queryset().filter(
                estado_pedido__in=['P', 'A']).exclude(id_pedido=self.request.query_params.get('id_pedido_seleccionado')).order_by('-fecha_pedido', '-id_pedido')

            serializer = self.get_serializer(pedidos, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            pedidos = ultimoPedido(self.request)
            serializer = self.get_serializer(pedidos)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        portal = self.request.session['portal']
        usuario = self.request.user

        pedido = WebPedidos.objects.filter(
            codigo_empresa=usuario.codigo_empresa)
        num_pedido = pedido.aggregate(Max('id_pedido'))
        if num_pedido['id_pedido__max'] is None:
            id_pedido = 1
        else:
            id_pedido = num_pedido['id_pedido__max'] + 1

        pedido = WebPedidos(id_pedido=id_pedido,
                            codigo_empresa=usuario.codigo_empresa, codigo_cliente=usuario.codigo_cliente, estado_pedido='A', origen_pedido='WEB',
                            organizacion_comercial=usuario.organizacion_comercial, almacen=usuario.codigo_almacen, tipo_pedido=usuario.tipo_pedido)

        pedido.save()
        serializer = self.get_serializer(pedido)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def calculaportes(self, request):

        portal = self.request.session['portal']
        usuario = self.request.user

        pedido_activo = ultimoPedido(self.request)

        if WebPedidosLin.objects.filter(id_pedido=pedido_activo.id_pedido).exists():

            try:
                calculaPortes(portal, usuario, pedido_activo)
            except Exception:
                return Response("Se ha producido un error calculando los portes del pedido, por favor, inténtelo más tarde", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        pedido = ultimoPedido(self.request)

        pedido_serializado = WebPedidosSerializer(pedido).data

        return Response(pedido_serializado, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def generarpedido(self, request, *args, **kwargs):
        portal = self.request.session['portal']
        usuario = self.request.user

        if request.query_params.get("pedido_anterior") is not None:

            id_pedido_anterior = request.query_params.get("pedido_anterior")

            if WebPedidos.objects.filter(codigo_empresa=portal['codigo_empresa'],
                                         codigo_cliente=usuario.codigo_cliente,
                                         id_pedido=id_pedido_anterior).exists():

                pedido = WebPedidos.objects.get(codigo_empresa=portal['codigo_empresa'],
                                                codigo_cliente=usuario.codigo_cliente,
                                                id_pedido=id_pedido_anterior)

                if WebPedidosLin.objects.filter(id_pedido=pedido.id_pedido).exists():
                    lineas = WebPedidosLin.objects.filter(
                        id_pedido=pedido.id_pedido)

                    pedido = ultimoPedido(self.request)

                    for linea in lineas:

                        articulo = Articulo.objects.get(
                            codigo_empresa=portal['codigo_empresa'], codigo_articulo=linea.articulo)

                        linea_pedido = {
                            'articulo': articulo.codigo_articulo,
                            'descripcion': articulo.descrip_comercial,
                            'precio_venta': "",
                            'observaciones': "",
                            'estado_linea': linea.estado_linea,
                            'cantidad_pedida': linea.cantidad_pedida,
                            'presentacion_pedido': linea.presentacion_pedido,
                            'tipo_linea': portal['tipo_linea_pedidos'],
                            'sub_pres': linea.sub_pres,
                            'sub_pres_cant': linea.sub_pres_cant,
                            'sub_pres_fc': linea.sub_pres_fc,
                            'presentacion_escogida': linea.presentacion_escogida,
                            'pres_fc': linea.pres_fc,
                        }

                        insertarLineaPedido(
                            portal, usuario, pedido, linea_pedido)

                    pedido = ultimoPedido(self.request)

                    pedido_serializado = WebPedidosSerializer(pedido).data

                    return Response(pedido_serializado, status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_400_BAD_REQUEST)

     # generar linea de pedido desde informe.
    @action(detail=False, methods=['post'])
    def insertalineasinforme(self, request):
        portal = self.request.session['portal']
        usuario = self.request.user

        if request.query_params.get("informe") is not None:

            if request.data is not None and request.data['filtros'] is not None:

                lineas = request.data['filtros']
                pedido = ultimoPedido(self.request)
                has_errors = False
                v_errores = 0

                for linea in lineas:

                    if Articulo.objects.filter(
                            codigo_empresa=portal['codigo_empresa'], codigo_articulo=linea['codigo_articulo']).exists():

                        articulo = Articulo.objects.get(
                            codigo_empresa=portal['codigo_empresa'], codigo_articulo=linea['codigo_articulo'])

                        if not EcomFormasEnvioTarifas.objects.filter(codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], articulo=articulo.codigo_articulo).exists():

                            # No se procesan lineas que sean Regalos R
                            if linea['tipo_linea'] == 'N':
                                linea_pedido = {
                                    'articulo': articulo.codigo_articulo,
                                    'descripcion': articulo.descrip_comercial,
                                    'precio_venta': "",
                                    'observaciones': "",
                                    'estado_linea': "B",
                                    'cantidad_pedida': linea['cantidad'],
                                    'presentacion_pedido': linea['presentacion'],
                                    'tipo_linea': portal['tipo_linea_pedidos'],
                                    'sub_pres': "",
                                    'sub_pres_cant': "",
                                    'sub_pres_fc': "",
                                    'presentacion_escogida': "",
                                    'pres_fc': "",
                                }

                                try:
                                    insertarLineaPedido(
                                        portal, usuario, pedido, linea_pedido, True)
                                except Exception:
                                    if len(lineas) == 1:
                                        return Response("Error insertando alguna de las lineas al pedido.", status=status.HTTP_400_BAD_REQUEST)
                                    else:
                                        has_errors = True
                                        v_errores = v_errores + 1
                                        logger.error(
                                            "Error insertando alguna de las lineas al pedido. Codigo_articulo: " + linea['codigo_articulo'])
                        else:
                            if len(lineas) == 1:
                                return Response("No es posible añadir lineas de portes al pedido.", status=status.HTTP_400_BAD_REQUEST)
                            else:
                                v_errores = v_errores + 1
                    else:
                        logger.error(
                            "No se ha encontrado el articulo " + linea['codigo_articulo'])
                        v_errores = v_errores + 1
                        has_errors = True

                pedido = ultimoPedido(self.request)

                pedido_serializado = WebPedidosSerializer(pedido).data

                # 100% errores
                if has_errors is True and v_errores == len(lineas):
                    return Response(data="No se han podido insertar las lineas.", status=status.HTTP_400_BAD_REQUEST)

                # Falla alguna
                elif has_errors is True and v_errores < len(lineas):
                    return Response(pedido_serializado, status=status.HTTP_202_ACCEPTED)

                else:  # Todas bien
                    return Response(pedido_serializado, status=status.HTTP_201_CREATED)

            return Response(data="Error recuperando datos de las lineas.", status=status.HTTP_400_BAD_REQUEST)

        return Response(data="Error recuperando datos del informe.", status=status.HTTP_400_BAD_REQUEST)


class WebPedidosLinViewSet(viewsets.ModelViewSet):
    queryset = WebPedidosLin.objects.all()
    permission_classes = [
        permisos.AllowSemiPrivate
    ]

    serializer_class = WebPedidosLinSerializer

    def list(self, request):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):

        registraActividad(self.request, 'pedidos', 'linea')

        pedido = ultimoPedido(self.request)

        portal = self.request.session['portal']
        usuario = self.request.user

        if pedido.estado_pedido == 'A':
            if request.query_params.get("actualizar") == 'S':
                try:
                    insertarLineaPedido(
                        portal, usuario, pedido, self.request.data, False)
                except Exception as e:
                    return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                if usuario.n_lineas_max_por_pedido is None or (usuario.n_lineas_max_por_pedido is not None and WebPedidosLin.objects.filter(id_pedido=pedido.id_pedido).aggregate(Count('numero_linea'))['numero_linea__count'] <= usuario.n_lineas_max_por_pedido):

                    try:
                        insertarLineaPedido(
                            portal, usuario, pedido, self.request.data, True)
                    except Exception as e:
                        return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                else:
                    return Response('No tienes permitido añadir más líneas al pedido', status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response('El pedido actual no está abierto, no puede modificarse, puede eliminarlo abriendo uno nuevo en el resumen', status=status.HTTP_400_BAD_REQUEST)

        pedido = ultimoPedido(self.request)

        pedido_serializado = WebPedidosSerializer(pedido).data

        return Response(pedido_serializado, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):

        pedido = ultimoPedido(self.request)
        portal = self.request.session['portal']
        usuario = self.request.user

        if pedido.estado_pedido == 'A':

            linea = WebPedidosLin.objects.get(pk=kwargs['pk'])

            if pedido.id_pedido == linea.id_pedido.pk:
                if linea.tipo_articulo != 'R' and linea.tipo_articulo != 'F' and linea.tipo_articulo != 'T':
                    try:
                        #### borramos los regalos asociados a esa linea si los tiene####
                        if WebPedidosLin.objects.filter(id_pedido=pedido.id_pedido, numero_linea_origen=linea.numero_linea).exclude(
                                numero_linea=F('numero_linea_origen')).exists() == True:
                            WebPedidosLin.objects.filter(id_pedido=pedido.id_pedido, numero_linea_origen=linea.numero_linea).exclude(
                                numero_linea=F('numero_linea_origen')).delete()

                        #### BORRADO NORMAL DE LA LINEA####
                        instance = self.get_object()
                        self.perform_destroy(instance)
                    except Http404:
                        pass

                    pedido = ultimoPedido(self.request)

                    pedido_recalculado = recalcularPedidoGrupos(
                        portal, usuario, pedido)

                    pedido_serializado = WebPedidosSerializer(
                        pedido_recalculado).data

                    return Response(pedido_serializado, status=status.HTTP_200_OK)
                else:
                    return Response("Esta línea no puede ser eliminada", status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response('El pedido actual no está abierto, no puede modificarse, puede eliminarlo abriendo uno nuevo en el resumen', status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def createmany(self, request, *args, **kwargs):

        registraActividad(self.request, 'pedidos', 'lineas')

        pedido = ultimoPedido(self.request)
        portal = self.request.session['portal']
        usuario = self.request.user

        if pedido.estado_pedido == 'A':
            for linea in request.data['lineas']:

                try:
                    insertarLineaPedido(portal, usuario, pedido, linea)
                except Exception as e:
                    return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response('El pedido actual no está abierto, no puede modificarse, puede eliminarlo abriendo uno nuevo en el resumen', status=status.HTTP_400_BAD_REQUEST)

        pedido = ultimoPedido(self.request)

        pedido_serializado = WebPedidosSerializer(pedido).data

        return Response(pedido_serializado, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def getDatosLineas(self, request, *args, **kwargs):

        pedido = ultimoPedido(self.request)
        portal = self.request.session['portal']

        usuario = self.request.user
        articulos = []

        if WebPedidosLin.objects.filter(id_pedido=pedido.id_pedido).exists():

            lineas = WebPedidosLin.objects.filter(id_pedido=pedido.id_pedido)

            for linea in lineas:
                if Articulo.objects.filter(codigo_empresa=portal['codigo_empresa'], codigo_articulo=linea.articulo).exists():
                    articulo = Articulo.objects.get(
                        codigo_empresa=portal['codigo_empresa'], codigo_articulo=linea.articulo)
                    articulos.append({'codigo_articulo': articulo.codigo_articulo,
                                      'codigo_empresa': articulo.codigo_empresa,
                                      'codigo_familia': articulo.codigo_familia,
                                      'codigo_estad2': articulo.codigo_estad2,
                                      'codigo_estad3': articulo.codigo_estad3,
                                      'codigo_estad4': articulo.codigo_estad4,
                                      'codigo_estad5': articulo.codigo_estad5,
                                      'codigo_estad6': articulo.codigo_estad6,
                                      'codigo_estad7': articulo.codigo_estad7,
                                      'codigo_estad8': articulo.codigo_estad8,
                                      'codigo_estad9': articulo.codigo_estad9,
                                      'codigo_estad10': articulo.codigo_estad10,
                                      'descrip_comercial': articulo.descrip_comercial,
                                      'descrip_reducida': articulo.descrip_reducida,
                                      'descrip_tecnica': articulo.descrip_tecnica,
                                      'descrip_compra': articulo.descrip_compra,
                                      'orden': articulo.orden,
                                      'unidad_codigo1': articulo.unidad_codigo1,
                                      'codigo_estad11': articulo.codigo_estad11,
                                      'codigo_estad12': articulo.codigo_estad12,
                                      'codigo_estad13': articulo.codigo_estad13,
                                      'codigo_estad14': articulo.codigo_estad14,
                                      'codigo_estad15': articulo.codigo_estad15,
                                      'codigo_estad16': articulo.codigo_estad16,
                                      'codigo_estad17': articulo.codigo_estad17,
                                      'codigo_estad18': articulo.codigo_estad18,
                                      'codigo_estad19': articulo.codigo_estad19,
                                      'codigo_estad20': articulo.codigo_estad20,
                                      'presentacion_web': articulo.presentacion_web,
                                      'tipo_material': articulo.tipo_material,
                                      'reservado_alfa_3': articulo.reservado_alfa_3,
                                      'partida_arancelaria': articulo.partida_arancelaria,
                                      'tipo_cadena_logistica': articulo.tipo_cadena_logistica,
                                      'reservado_number_1': articulo.reservado_number_1,
                                      'reservado_number_2': articulo.reservado_number_2,
                                      'cliente_elaboracion': articulo.cliente_elaboracion,
                                      'alfa3_fao': articulo.alfa3_fao,
                                      'residuo': articulo.residuo,
                                      'cantidad_minima': articulo.cantidad_minima,
                                      'cantidad_maxima': articulo.cantidad_maxima,
                                      'multiplo': articulo.multiplo,
                                      'peso_neto': articulo.peso_neto,
                                      'controlar_stock': articulo.controlar_stock,
                                      'codigo_familia_d': articulo.codigo_familia_d,
                                      'codigo_estad2_d': articulo.codigo_estad2_d,
                                      'codigo_estad3_d': articulo.codigo_estad3_d,
                                      'codigo_estad4_d': articulo.codigo_estad4_d,
                                      'codigo_estad5_d': articulo.codigo_estad5_d,
                                      'codigo_estad6_d': articulo.codigo_estad6_d,
                                      'codigo_estad7_d': articulo.codigo_estad7_d,
                                      'codigo_estad8_d': articulo.codigo_estad8_d,
                                      'codigo_estad9_d': articulo.codigo_estad9_d,
                                      'codigo_estad10_d': articulo.codigo_estad10_d,
                                      'codigo_estad11_d': articulo.codigo_estad11_d,
                                      'codigo_estad12_d': articulo.codigo_estad12_d,
                                      'codigo_estad13_d': articulo.codigo_estad13_d,
                                      'codigo_estad14_d': articulo.codigo_estad14_d,
                                      'codigo_estad15_d': articulo.codigo_estad15_d,
                                      'codigo_estad16_d': articulo.codigo_estad16_d,
                                      'codigo_estad17_d': articulo.codigo_estad17_d,
                                      'codigo_estad18_d': articulo.codigo_estad18_d,
                                      'codigo_estad19_d': articulo.codigo_estad19_d,
                                      'codigo_estad20_d': articulo.codigo_estad20_d,
                                      'd_alfa3_fao': articulo.d_alfa3_fao,
                                      'unidad_codigo2': articulo.unidad_codigo2,
                                      'd_unidad_codigo2': articulo.d_unidad_codigo2,
                                      'unidad_precio_venta': articulo.unidad_precio_venta,
                                      'codigo_sinonimo': articulo.codigo_sinonimo,
                                      'reservado_alfa_1': articulo.reservado_alfa_1,
                                      'reservado_alfa_2': articulo.reservado_alfa_2,
                                      'reservado_alfa_4': articulo.reservado_alfa_4,
                                      'fecha_baja': articulo.fecha_baja,
                                      'codigo_situacion': articulo.codigo_situacion,
                                      'tipo_carnet_profesional': articulo.tipo_carnet_profesional,
                                      'tipo': articulo.tipo,
                                      'numero_receta': articulo.numero_receta})

            if len(articulos) != 0:
                return Response(articulos, status=status.HTTP_201_CREATED)
            else:
                logger.error('El pedido no tiene lineas')
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class IntegraPedidoViewSet(viewsets.ViewSet):
    serializer_class = IntegraPedidoSerializer
    permission_classes = [
        permisos.AllowPrivate
    ]

    def list(self, request):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def create(self, request):

        registraActividad(self.request, 'pedidos', 'pedido')

        portal = self.request.session['portal']
        usuario = self.request.user

        if portal['codigo_cliente'] == usuario.codigo_cliente:
            return Response('No tienes permisos para finalizar el pedido, haz login', status=status.HTTP_401_UNAUTHORIZED)

        if usuario.activar_pedidos == 'N':
            return Response('No tienes permisos para finalizar el pedido, habla con tu administrador', status=status.HTTP_403_FORBIDDEN)

        endpoint = '/V1/B2B/ORDERS/NEW'

        pedido_activo = ultimoPedido(self.request)

        pedido_activo_dict = WebPedidosSerializer(pedido_activo).data

        pedido_recibido = request.data['pedido']

        for linea in pedido_activo_dict['lineas']:
            linea.pop('id', None)
            linea.pop('numero_linea', None)
            linea.pop('numero_linea_origen', None)

        for linea in pedido_recibido['lineas']:
            linea.pop('id', None)
            linea.pop('numero_linea', None)
            linea.pop('numero_linea_origen', None)

            if 'datos_articulo' in linea and linea['datos_articulo'] is not None:
                linea.pop('datos_articulo', None)

        if pedido_activo_dict['lineas'] != pedido_recibido['lineas']:
            pedido_serializado = WebPedidosSerializer(pedido_activo).data
            return Response(pedido_serializado,
                            status=status.HTTP_400_BAD_REQUEST)

        if 'forma_envio' in request.data and 'forma_envio' in request.data['forma_envio']:
            pedido_activo.forma_envio = request.data['forma_envio']['forma_envio']

        if 'almacen' in request.data['almacen_recogida']:
            pedido_activo.almacen = request.data['almacen_recogida']['almacen']
            pedido_activo.domicilio_envio = None
            pedido_activo.transportista = None

        elif 'almacen' in request.data['ruta']:
            pedido_activo.almacen = request.data['ruta']['almacen']
            pedido_activo.domicilio_envio = request.data['ruta']['numero_direccion']
            pedido_activo.transportista = None

        elif 'numero_direccion' in request.data['domicilio']:
            pedido_activo.domicilio_envio = request.data['domicilio']['numero_direccion']
            pedido_activo.transportista = request.data['domicilio']['agencia_envio']
            pedido_activo.almacen = usuario.codigo_almacen

            if portal['activar_almacenes_x_provincia'] == 'S':
                domicilio_envio = DomiciliosEnvio.objects.get(empresa=portal['codigo_empresa'], codigo_cliente=usuario.codigo_cliente,
                                                              numero_direccion=pedido_activo.domicilio_envio)
                codigo_estado = domicilio_envio.estado
                codigo_provincia = domicilio_envio.provincia

                if EcomAlmacenesProvincias.objects.filter(empresa=portal['codigo_empresa'],
                                                          portal=portal['codigo_portal'],
                                                          estado=codigo_estado,
                                                          provincia=codigo_provincia).exists():

                    ahora = datetime.date.today()

                    almacen_provincia = EcomAlmacenesProvincias.objects.filter(Q(fecha_baja__isnull=True) | Q(fecha_baja__gte=ahora)).get(empresa=portal['codigo_empresa'],
                                                                                                                                          portal=portal[
                        'codigo_portal'],
                        estado=codigo_estado,
                        provincia=codigo_provincia)
                    pedido_activo.almacen = almacen_provincia.almacen
                else:
                    if usuario.codigo_almacen is not None:
                        pedido_activo.almacen = usuario.codigo_almacen
                    else:
                        pedido_activo.almacen = portal['codigo_almacen']
        if 'fecha_entrega' in request.data and request.data['fecha_entrega'] != "":
            pedido_activo.fecha_entrega = datetime.datetime.strptime(
                request.data['fecha_entrega'], "%Y-%m-%dT%H:%M:%S.%fZ")

        if 'forma_pago' in request.data and 'codigo_forma_pago_web' in request.data['forma_pago']:
            pedido_activo.forma_pago = request.data['forma_pago']['codigo_forma_pago_web']

        if 'observaciones' in request.data and request.data['observaciones'] != "":
            pedido_activo.observaciones = request.data['observaciones']

        if 'persona_pedido' in request.data and request.data['persona_pedido'] != "":
            pedido_activo.persona_pedido = request.data['persona_pedido']

        if 'pedido_cliente' in request.data and request.data['pedido_cliente'] != "":
            pedido_activo.pedido_cliente = request.data['pedido_cliente']

        if 'domicilio_envio_mod' in request.data:
            pedido_activo.nombre_dom_envio = request.data['domicilio_envio_mod']['nombre_dom_envio']
            pedido_activo.direccion_dom_envio = request.data[
                'domicilio_envio_mod']['direccion_dom_envio']
            pedido_activo.localidad_dom_envio = request.data[
                'domicilio_envio_mod']['localidad_dom_envio']
            pedido_activo.estado_dom_envio = request.data['domicilio_envio_mod']['estado_dom_envio']
            pedido_activo.provincia_dom_envio = request.data[
                'domicilio_envio_mod']['provincia_dom_envio']
            pedido_activo.cod_postal_dom_envio = request.data[
                'domicilio_envio_mod']['cod_postal_dom_envio']
            pedido_activo.tipo_portes_dom_envio = request.data[
                'domicilio_envio_mod']['tipo_portes_dom_envio']

        if 'email_pedido' in request.data and request.data['email_pedido'] != "":
            pedido_activo.email = request.data['email_pedido']

        if 'transportista' in request.data:
            if 'codigo_rapido' in request.data['transportista'] and request.data['transportista']['codigo_rapido'] != "":
                pedido_activo.transportista = request.data['transportista']['codigo_rapido']

        pedido_activo.fecha_valor = datetime.date.today()

        if pedido_activo.estado_pedido == "P":
            pedido_activo.estado_pedido = "A"

        pedido_activo.save()

        if WebPedidosLin.objects.filter(id_pedido=pedido_activo.id_pedido).exists():

            try:
                calculaPortes(portal, usuario, pedido_activo)
            except Exception:
                pedido_serializado = WebPedidosSerializer(pedido_activo).data
                return Response(pedido_serializado, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        lineas_set = WebPedidosLin.objects.filter(
            id_pedido=pedido_activo.id_pedido)

        portal = self.request.session['portal']

        pedido = procesa_pedido(
            portal['codigo_portal'], self.request.user.usuario_web, pedido_activo)  # , request.data['domicilio'], request.data['observaciones'], request.data['forma_envio'])  # (pedido_set[0])

        lineas = []
        for linea in lineas_set:
            lineas.append(procesa_linea(linea))

        pedido.update({'lineas': lineas})

        body = json.dumps(
            pedido,
            sort_keys=False,
            indent=None,
            use_decimal=True,
            default=fecha_encoder
        )

        try:
            respuesta = comunica_lisa(
                endpoint=endpoint, body=body, portal=portal, usuario=usuario)
        except Exception as e:
            logger.error("La peticion a lisa: " + endpoint +
                         " ha fallado, excepcion: " + str(e))

            pedido_serializado = WebPedidosSerializer(pedido_activo).data
            return Response(pedido_serializado, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # SI SE GENERA UN PRESUPUESTO ENTONCES LISA DEVUELVE NUMERO_PEDIDO Y NUMERO_SERIE COMO list Y VICEVERSA
        # ESTAS COMPROBACIONES SON PARA LIMPIAR ESOS list Y GUARDAR ESOS VALORES A NULL

        if 'pedido' in respuesta:
            pedido = respuesta['pedido']

            pedido_activo.numero_pedido = pedido['cabecera']['numero_pedido']
            pedido_activo.numero_serie = pedido['cabecera']['numero_serie']
            pedido_activo.ejercicio = pedido['cabecera']['ejercicio']
            pedido_activo.importe_cobrado = float(
                pedido['cabecera']['liquido_pedido'].replace(',', '.'))
            pedido_activo.status_pedido = pedido['cabecera']['status_pedido']
            pedido_activo.domicilio_cobro = pedido['cabecera'][
                'domicilio_cobro'] if 'domicilio_cobro' in pedido['cabecera'] else None
            pedido_activo.id_pedido_libra = pedido['id_pedido_libra']
            pedido_activo.divisa = pedido['cabecera']['divisa'] if 'divisa' in pedido[
                'cabecera'] and pedido['cabecera']['divisa'] is not None else None

        if 'presupuesto' in respuesta:
            pedido = respuesta['presupuesto']

            pedido_activo.numero_pres = pedido['cabecera']['numero_pres']
            pedido_activo.numero_serie_pres = pedido['cabecera']['numero_serie']
            pedido_activo.ejercicio = pedido['cabecera']['ejercicio']
            pedido_activo.importe_cobrado = pedido['cabecera']['liquido_pres']
            pedido_activo.status_pres = pedido['cabecera']['status_pres']
            pedido_activo.domicilio_cobro = pedido['cabecera'][
                'domicilio_cobro'] if 'domicilio_cobro' in pedido['cabecera'] else None
            pedido_activo.id_pedido_libra = pedido['id_pedido_libra']
            pedido_activo.divisa = pedido['cabecera']['divisa'] if 'divisa' in pedido[
                'cabecera'] and pedido['cabecera']['divisa'] is not None else None

        # si hay pedido y presupuesto simultáneo, el importe cobrado es el del pedido
        if 'presupuesto' in respuesta and 'pedido' in respuesta:
            pedido = respuesta['pedido']
            pedido_activo.importe_cobrado = pedido['cabecera']['liquido_pedido']
            pedido_activo.divisa = pedido['cabecera']['divisa']

        if 'presupuesto' not in respuesta and 'pedido' not in respuesta:
            logger.error(
                "La integracion ha fallado, respuesta lisa: "+str(respuesta))
            Response("El procesado del pedido ha fallado, por favor contacte con soporte",
                     status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if FormasPago.objects.filter(codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal']).exists():
            # el portal tiene formas de pago
            if pedido_activo.forma_pago is not None:
                # comprobar que el pedido tenga forma de pago asignada

                forma_pago = FormasPago.objects.get(
                    codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], codigo_forma_pago_web=pedido_activo.forma_pago)

                # si el portal controla riesgo, verficamos que la forma de pago sea adecuada
                if (portal["control_riesgo"] is not None and portal["control_riesgo"] == 'S'):
                    try:
                        cliente_riesgo = comprobarRiesgo(
                            portal, usuario, usuario.codigo_cliente, usuario.centro_contable)
                    except Exception as e:
                        logger.error("La peticion a lisa: " + endpoint +
                                     " ha fallado, excepcion: " + str(e))
                        return Response("Se ha producido un error, por favor, inténtelo más tarde", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    if (cliente_riesgo == 'S' and forma_pago.gestion_riesgo == 'RN') or (cliente_riesgo == 'N' and forma_pago.gestion_riesgo == 'RS'):
                        logger.error(
                            "La forma de pago tiene que ser acorde al riesgo del cliente: "+str(respuesta))
                        return Response("La forma de pago tiene que ser acorde al riesgo del cliente",
                                        status=status.HTTP_400_BAD_REQUEST)

                if forma_pago.pasarela is not None:  # si la forma de pago tiene pasarela asignada, pedido a pendiente de pago
                    pedido_activo.estado_pedido = 'P'
                else:
                    pedido_activo.estado_pedido = 'D'
            else:
                if (usuario.permitir_pago_acordado is not None and usuario.permitir_pago_acordado != 'S'):
                    return Response("Debe elegir una forma de pago", status=status.HTTP_400_BAD_REQUEST)
                else:
                    pedido_activo.estado_pedido = 'D'
        else:
            pedido_activo.estado_pedido = 'D'

        pedido_activo.save()

        if pedido_activo.estado_pedido == 'D':
            if portal['alerta_fin_pedido'] is not None:
                enviarAlerta(codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], usuario_web=usuario.usuario_web, numero_alerta=portal['alerta_fin_pedido'], email_to=usuario.email_usuario_web,
                             varchar01=portal['codigo_empresa'], varchar02=portal['codigo_portal'], varchar03=pedido_activo.numero_serie, varchar04=pedido_activo.organizacion_comercial, varchar05=pedido_activo.numero_serie_pres, portal=portal, usuario=usuario, number01=pedido_activo.ejercicio,
                             number02=pedido_activo.numero_pedido, number03=pedido_activo.numero_pres, number04="", number05="", date01="", date02="", date03="", date04="", date05="")

        pedido_serializado = WebPedidosSerializer(pedido_activo).data

        return Response(pedido_serializado, status=status.HTTP_200_OK)


class ActualizaPedidoViewSet(viewsets.ViewSet):
    permission_classes = [
        permisos.AllowSemiPrivate
    ]

    def create(self, request):

        portal = self.request.session['portal']
        usuario = self.request.user
        pedido_activo = ultimoPedido(self.request)

        if 'forma_envio' in request.data and 'forma_envio' in request.data['forma_envio']:
            pedido_activo.forma_envio = request.data['forma_envio']['forma_envio']

        if 'almacen' in request.data['almacen_recogida']:
            pedido_activo.almacen = request.data['almacen_recogida']['almacen']
            pedido_activo.domicilio_envio = None
            pedido_activo.transportista = None
        elif 'almacen' in request.data['ruta']:
            pedido_activo.almacen = request.data['ruta']['almacen']
            pedido_activo.domicilio_envio = request.data['ruta']['numero_direccion']
            pedido_activo.transportista = None
        elif 'numero_direccion' in request.data['domicilio']:
            pedido_activo.domicilio_envio = request.data['domicilio']['numero_direccion']
            pedido_activo.transportista = request.data['domicilio']['agencia_envio']
            pedido_activo.almacen = usuario.codigo_almacen

            if portal['activar_almacenes_x_provincia'] == 'S':
                domicilio_envio = DomiciliosEnvio.objects.get(empresa=portal['codigo_empresa'], codigo_cliente=usuario.codigo_cliente,
                                                              numero_direccion=pedido_activo.domicilio_envio)
                codigo_estado = domicilio_envio.estado
                codigo_provincia = domicilio_envio.provincia

                ahora = datetime.date.today()

                if EcomAlmacenesProvincias.objects.filter(Q(fecha_baja__isnull=True) | Q(fecha_baja__gte=ahora)).filter(empresa=portal['codigo_empresa'],
                                                                                                                        portal=portal[
                                                                                                                            'codigo_portal'],
                                                                                                                        estado=codigo_estado,
                                                                                                                        provincia=codigo_provincia).exists():

                    almacen_provincia = EcomAlmacenesProvincias.objects.filter(Q(fecha_baja__isnull=True) | Q(fecha_baja__gte=ahora)).get(empresa=portal['codigo_empresa'],
                                                                                                                                          portal=portal[
                                                                                                                                              'codigo_portal'],
                                                                                                                                          estado=codigo_estado,
                                                                                                                                          provincia=codigo_provincia)
                    pedido_activo.almacen = almacen_provincia.almacen

        if 'tipo_pedido' in request.data['tipo_pedido']:
            pedido_activo.tipo_pedido = request.data['tipo_pedido']['tipo_pedido']

        if 'fecha_entrega' in request.data and request.data['fecha_entrega'] != "":
            pedido_activo.fecha_entrega = request.data['fecha_entrega']

        if 'observaciones' in request.data and request.data['observaciones'] != "":
            pedido_activo.observaciones = request.data['observaciones']

        if 'persona_pedido' in request.data and request.data['persona_pedido'] != "":
            pedido_activo.persona_pedido = request.data['persona_pedido']

        if 'pedido_cliente' in request.data and request.data['pedido_cliente'] != "":
            pedido_activo.pedido_cliente = request.data['pedido_cliente']

        if 'domicilio_envio_mod' in request.data:
            pedido_activo.nombre_dom_envio = request.data['domicilio_envio_mod']['nombre_dom_envio']
            pedido_activo.direccion_dom_envio = request.data[
                'domicilio_envio_mod']['direccion_dom_envio']
            pedido_activo.localidad_dom_envio = request.data[
                'domicilio_envio_mod']['localidad_dom_envio']
            pedido_activo.estado_dom_envio = request.data['domicilio_envio_mod']['estado_dom_envio']
            pedido_activo.provincia_dom_envio = request.data[
                'domicilio_envio_mod']['provincia_dom_envio']
            pedido_activo.cod_postal_dom_envio = request.data[
                'domicilio_envio_mod']['cod_postal_dom_envio']
            pedido_activo.tipo_portes_dom_envio = request.data[
                'domicilio_envio_mod']['tipo_portes_dom_envio']

        if 'email_pedido' in request.data and request.data['email_pedido'] != "":
            pedido_activo.email = request.data['email_pedido']

        if 'transportista' in request.data:
            if 'codigo_rapido' in request.data['transportista'] and request.data['transportista']['codigo_rapido'] != "":
                pedido_activo.transportista = request.data['transportista']['codigo_rapido']

        if 'forma_pago' in request.data and 'codigo_forma_pago_web' in request.data['forma_pago']:
            pedido_activo.forma_pago = request.data['forma_pago']['codigo_forma_pago_web']

        pedido_activo.save()

        pedido = recalcularPedidoGrupos(portal, usuario, pedido_activo)

        pedido_serializado = WebPedidosSerializer(pedido).data

        return Response(pedido_serializado, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def cierrapedido(self, request, *args, **kwargs):
        portal = self.request.session['portal']
        usuario = self.request.user

        pedido = request.data['pedido']

        pedido_web = WebPedidos.objects.get(
            codigo_empresa=portal['codigo_empresa'], codigo_cliente=usuario.codigo_cliente, id_pedido=pedido['id_pedido'])

        pedido_web.estado_pedido = 'D'

        pedido_web.save()

        if portal.alerta_fin_pedido is not None:
            enviarAlerta(codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], usuario_web=usuario.usuario_web, numero_alerta=portal['alerta_fin_pedido'], email_to=usuario.email_usuario_web,
                         varchar01=portal['codigo_empresa'], varchar02=portal['codigo_portal'], varchar03=pedido_web.numero_serie, varchar04=pedido_web.organizacion_comercial, varchar05=pedido_web.numero_serie_pres, portal=portal, usuario=usuario, number01=pedido_web.ejercicio,
                         number02=pedido_web.numero_pedido, number03=pedido_web.numero_pres, number04="", number05="", date01="", date02="", date03="", date04="", date05="")

        pedido_serializado = WebPedidosSerializer(pedido_web).data

        return Response(pedido_serializado, status=status.HTTP_201_CREATED)


class TiposPedidoVtaViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        permisos.AllowSemiPrivate
    ]

    serializer_class = TiposPedidoVtaSerializer

    def get_queryset(self):
        portal = self.request.session['portal']
        usuario = self.request.user

        permisos = EcomUsuarioWebPermisos.objects.filter(
            codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], usuario_web=usuario.usuario_web, tipo_pedido__isnull=False)

        tipos_pedido = TiposPedidoVta.objects.filter(
            codigo_empresa=portal['codigo_empresa'], organizacion_comercial=portal['organizacion_comercial'], tipo_pedido__in=permisos.values('tipo_pedido'))

        return tipos_pedido


class TextosVentasViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        portal = self.request.session['portal']
        return TextosVentas.objects.filter(codigo_empresa=portal['codigo_empresa'])

    permission_classes = [
        permisos.AllowCatalog
    ]

    serializer_class = TextosVentasSerializer

    def list(self, request):

        if request.query_params.get('organizacion_comercial') is not None and request.query_params.get('idioma') is not None and request.query_params.get('presupuesto') is not None:
            organizacion_comercial = request.query_params.get(
                'organizacion_comercial')
            presupuesto = request.query_params.get(
                'presupuesto')

            idioma = request.query_params.get(
                'idioma')

            texto_ventas = self.get_queryset().filter(
                organizacion_comercial=organizacion_comercial,
                idioma=idioma,
                presupuesto=presupuesto)

            serializer = self.get_serializer(texto_ventas, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class DescuentosTramosHorariosClienteViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        portal = self.request.session['portal']
        usuario = self.request.user

        ahora = timezone.now()

        if usuario.organizacion_comercial is not None:
            organizacion_comercial = usuario.organizacion_comercial

        else:
            if portal['organizacion_comercial'] is not None:
                organizacion_comercial = portal['organizacion_comercial']

        if usuario.tipo_pedido is not None:
            tipo_pedido = usuario.tipo_pedido

        else:
            if portal['tipo_pedido'] is not None:
                tipo_pedido = portal['tipo_pedido']

        if DescuentosTramosHorariosCliente.objects.filter(
                codigo_empresa=portal['codigo_empresa'], organizacion_comercial=organizacion_comercial, tipo_pedido=tipo_pedido, cliente=usuario.codigo_cliente).exists():

            descuentos_aplicables = DescuentosTramosHorariosCliente.objects.filter(
                codigo_empresa=portal['codigo_empresa'], organizacion_comercial=organizacion_comercial, tipo_pedido=tipo_pedido, cliente=usuario.codigo_cliente, fecha_validez__lte=ahora)

            return descuentos_aplicables
        else:
            return DescuentosTramosHorariosCliente.objects.none()

    permission_classes = [
        permisos.AllowCatalog
    ]

    serializer_class = DescuentosTramosHorariosClienteSerializer


class EcomFormasEnvioTarifasViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        portal = self.request.session['portal']
        return EcomFormasEnvioTarifas.objects.filter(
            codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'])

    permission_classes = [permisos.AllowCatalog]
    serializer_class = EcomFormasEnvioTarifasSerializer

    def list(self, request):

        portal = self.request.session['portal']
        usuario = self.request.user
        pedido = ultimoPedido(self.request)

        if pedido.forma_envio is not None:

            domicilio_envio = DomiciliosEnvio.objects.none()

            if DomiciliosEnvio.objects.filter(empresa=portal['codigo_empresa'], codigo_cliente=usuario.codigo_cliente, numero_direccion=pedido.domicilio_envio).exists():

                domicilio_envio = DomiciliosEnvio.objects.get(
                    empresa=portal['codigo_empresa'], codigo_cliente=usuario.codigo_cliente, numero_direccion=pedido.domicilio_envio)

            estado = pedido.estado_dom_envio if pedido.estado_dom_envio is not None else domicilio_envio.estado
            provincia = pedido.provincia_dom_envio if pedido.provincia_dom_envio is not None else domicilio_envio.provincia

            tarifa_aplicable = self.get_queryset().filter(
                forma_envio=pedido.forma_envio,
                estado=estado,
                provincia=provincia)

            serializer = self.get_serializer(tarifa_aplicable, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response("Falta forma envio", status=status.HTTP_400_BAD_REQUEST)
