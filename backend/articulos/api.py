import os.path
import base64
from django.http import HttpResponseNotFound
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.decorators import action
from usuarios.models import AgentesClientes, ClientesParametros
from articulos.models import Articulo, Familia, ArticulosImagenesGaleria, Filtro, EcomArticulosPortales, \
    EcomArticulosRelacionados, ArticulosEquivalentes, EcomFamiliasPortales, CodigoBarras, \
    EcomArtAgrupHijos, EcomArtAgrupCond, EcomArticulosProvincias, ArticulosDoc, ArticulosAux, EcomSubPresentaciones,\
    FamiliasImagenes, CadenaLogistica, Presentaciones, PresenArticulo, FiltroClaveEstadistica, ArticulosDescripcionWeb, \
    ValoresClavesArt, ClavesEstadisticasArt, ArticulosClavesEstadisticas, EcomArtAgrup, AlmacenesArticulos, DetalleListaReferencias
from domicilios.models import DomiciliosEnvio
from .serializers import ArticuloSerializer, CadenaLogisticaSerializer, ClavesEstadisticasArtSerializer, PrecioSerializer, FamiliaSerializer, ImagenSerializer, \
    GaleriaSerializer, FiltroSerializer, CodigosBarrasSerializer, EcomArtAgrupHijosSerializer, EcomArtAgrupCondSerializer,\
    ArticulosDocSerializer, ArticulosAuxSerializer, EcomSubPresentacionesSerializer,\
    FamiliasImagenesSerializer, PresentacionesSerializer, PresenArticuloSerializer, FiltroClaveEstadisticaSerializer, \
    ValoresClavesArtSerializer, ArticulosClavesEstadisticasSerializer, OfertasMultiplesSerializer, DetalleListaReferenciasSerializer
from rest_framework import filters, pagination, viewsets, status
from datetime import datetime
from usuarios import permisos
from .functions import buscarArticulos, calcula_precio_articulo, calcula_precios_articulos, generarMigas, obtener_filtros_aplicables, \
    getArbolFamilias, obtenerStock, getClavesEstadisticas, obtener_filtros_claves_aplicables, calcula_ofertas_multiples, obtenerStocks, listaFamiliaHijas

import datetime
from django.db.models import OuterRef, Exists, Q
from portales.lisa import comunica_lisa
from portal.functions import registraActividad
from usuarios.models import EcomUsuarioWeb
from portal.models import EcomSesiones, EcomSesionesAccion, EcomSesionesAccionParams, EcomFamiliasXTipoCliente
from pedidos.models import Divisas
import logging
from request_logging.decorators import no_logging

logger = logging.getLogger("rad_logger")


class ArticuloViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = [
        permisos.AllowCatalog
    ]

    def get_queryset(self):
        portal = self.request.session['portal']
        usuario = self.request.user

        articulos = Articulo.objects.filter(codigo_empresa=portal['codigo_empresa']).exclude(
            Exists(EcomArtAgrupHijos.objects.filter(codigo_empresa=portal['codigo_empresa'],
                                                    codigo_portal=portal['codigo_portal'],
                                                    codigo_articulo=OuterRef('codigo_articulo'))))

        articulos = articulos.exclude(Q(tipo_material='T') & ~Q(Exists(EcomArtAgrup.objects.filter(codigo_empresa=portal['codigo_empresa'],
                                                                                                   codigo_portal=portal['codigo_portal'], codigo_articulo=OuterRef('codigo_articulo')))))

        if portal['activar_articulos_provincia'] == 'S':
            usuario = self.request.user

            numero_domicilio_envio = None

            if self.request.GET.get('domicilio_envio') is not None:
                numero_domicilio_envio = self.request.GET.get(
                    'domicilio_envio')

            if numero_domicilio_envio is not None:

                domicilio_envio = DomiciliosEnvio.objects.get(empresa=portal['codigo_empresa'], codigo_cliente=usuario.codigo_cliente,
                                                              numero_direccion=numero_domicilio_envio)
                codigo_estado = domicilio_envio.estado
                codigo_provincia = domicilio_envio.provincia

                ahora = datetime.date.today()

                articulos = articulos.filter(
                    Exists(EcomArticulosProvincias.objects.filter(Q(fecha_baja__isnull=True) | Q(fecha_baja__gte=ahora)).filter(empresa=portal['codigo_empresa'],
                                                                                                                                portal=portal[
                        'codigo_portal'],
                        estado=codigo_estado,
                        provincia=codigo_provincia,
                        articulo=OuterRef('codigo_articulo'))))

        if portal['activar_articulos_almacen'] == 'S':
            articulos = articulos.filter(Exists(AlmacenesArticulos.objects.filter(
                codigo_empresa=portal['codigo_empresa'], codigo_almacen=usuario.codigo_almacen, codigo_articulo=OuterRef('codigo_articulo'), bloqueo_ventas='N')))

        if portal['familias_x_tipo_cliente'] == 'S':
            if portal['codigo_estadistico_familias'] == 1:
                familia_articulo = 'codigo_familia'
            else:
                familia_articulo = 'codigo_estad' + \
                    str(portal['codigo_estadistico_familias'])

            ecom_fam = EcomFamiliasXTipoCliente.objects.filter(
                codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], tipo_cliente=usuario.tipo_cliente)

            lista_familias = []

            for fam in ecom_fam:
                lista_familias.append(fam.codigo_familia)
                if fam.familia_completa == 'S':
                    for f in listaFamiliaHijas(portal['codigo_empresa'], fam.numero_tabla, fam.codigo_familia):
                        lista_familias.append(f)

            articulos = articulos.filter(
                Q(**{"%s__in" % familia_articulo: lista_familias}))

        return articulos

    serializer_class = ArticuloSerializer

    pagination_class = LimitOffsetPagination

    def retrieve(self, request, pk=None):

        registraActividad(self.request, 'articulos', 'busqueda')

        articulos_original = self.get_queryset()

        if pk is not None:

            if articulos_original.filter(codigo_articulo=pk).exists():
                articulo = articulos_original.get(codigo_articulo=pk)
                articulo_serializado = self.get_serializer(articulo).data
                return Response(articulo_serializado)
            else:
                if articulos_original.filter(id=pk).exists():
                    articulo = articulos_original.get(id=pk)
                    articulo_serializado = self.get_serializer(articulo).data
                    return Response(articulo_serializado)
                else:
                    return Response(status=status.HTTP_404_NOT_FOUND)

    def list(self, request):

        registraActividad(self.request, 'articulos', 'busqueda')

        portal = self.request.session['portal']
        usuario = self.request.user
        articulos = self.get_queryset()  # todos los artículos
        busqueda = None
        filtros = None
        avanzada = "N"
        codigo_articulo = None
        descripcion = None
        palabras_clave = None
        codigo_barras = None
        equivalentes = None
        referencia_cliente = None
        codigo_sinonimo = None

        if self.request.GET.get('search') is not None and self.request.GET.get('search') != "":
            busqueda = self.request.GET.get('search')

        if self.request.GET.get('avanzada') is not None and self.request.GET.get('avanzada') != "":
            avanzada = self.request.GET.get('avanzada')

        if self.request.GET.get('codigo_articulo') is not None and self.request.GET.get('codigo_articulo') != "":
            codigo_articulo = self.request.GET.get('codigo_articulo')

        if self.request.GET.get('descripcion') is not None and self.request.GET.get('descripcion') != "":
            descripcion = self.request.GET.get('descripcion')

        if self.request.GET.get('palabras_clave') is not None and self.request.GET.get('palabras_clave') != "":
            palabras_clave = self.request.GET.get(
                'palabras_clave').split("-")

        if self.request.GET.get('codigo_barras') is not None and self.request.GET.get('codigo_barras') != "":
            codigo_barras = self.request.GET.get('codigo_barras')

        if self.request.GET.get('equivalentes') is not None and self.request.GET.get('equivalentes') != "":
            equivalentes = self.request.GET.get('equivalentes')

        if self.request.GET.get('referencia_cliente') is not None and self.request.GET.get('referencia_cliente') != "":
            referencia_cliente = self.request.GET.get(
                'referencia_cliente')

        if self.request.GET.get('codigo_sinonimo') is not None and self.request.GET.get('codigo_sinonimo') != "":
            codigo_sinonimo = self.request.GET.get(
                'codigo_sinonimo')
        if self.request.GET.get('limit') is not None:
            limit = self.request.GET.get(
                'limit')
        else:
            limit = 12

        articulos = buscarArticulos(
            portal=portal, usuario=usuario, articulos_completos=articulos, busqueda=busqueda, filtros=filtros, avanzada=avanzada, codigo_articulo=codigo_articulo,
            descripcion=descripcion, palabras_clave=palabras_clave, codigo_barras=codigo_barras, equivalentes=equivalentes, referencia_cliente=referencia_cliente, codigo_sinonimo=codigo_sinonimo)

        if self.request.GET.get('order') is not None:
            if self.request.GET.get('order') == 'codigo':
                articulos = articulos.order_by('codigo_articulo')
            elif self.request.GET.get('order') == 'descripcion':
                articulos = articulos.order_by('descrip_comercial')

        filtros_aplicables = obtener_filtros_aplicables(portal, articulos)

        filtros_claves_aplicables = obtener_filtros_claves_aplicables(
            portal, articulos)

        pagination.PageNumberPagination.page_size = limit
        page = self.paginate_queryset(articulos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)

            response = self.get_paginated_response(serializer.data)

            response.data["filtros_aplicables"] = filtros_aplicables
            response.data["filtros_claves_aplicables"] = filtros_claves_aplicables
            return response

        serializer = self.get_serializer(articulos, many=True)

        return Response({"results": serializer.data, "filtros_aplicables": filtros_aplicables, "filtros_claves_aplicables": filtros_claves_aplicables})

    @ action(detail=False, methods=['post'])
    def listByFamily(self, request):

        registraActividad(self.request, 'articulos', 'busqueda')

        portal = self.request.session['portal']
        usuario = self.request.user
        articulos = self.get_queryset()  # todos los artículos
        busqueda = None
        filtros = None
        avanzada = "N"
        codigo_articulo = None
        descripcion = None
        palabras_clave = None
        codigo_barras = None
        equivalentes = None
        referencia_cliente = None
        codigo_sinonimo = None

        if request.query_params.get('search') is not None and request.query_params.get('search') != "":
            busqueda = request.query_params.get('search')

        if request.query_params.get('avanzada') is not None and request.query_params.get('avanzada') != "":
            avanzada = request.query_params.get('avanzada')

        if request.query_params.get('codigo_articulo') is not None and request.query_params.get('codigo_articulo') != "":
            codigo_articulo = request.query_params.get('codigo_articulo')

        if request.query_params.get('descripcion') is not None and request.query_params.get('descripcion') != "":
            descripcion = request.query_params.get('descripcion')

        if request.query_params.get('palabras_clave') is not None and request.query_params.get('palabras_clave') != "":
            palabras_clave = request.query_params.get(
                'palabras_clave').split("-")

        if request.query_params.get('codigo_barras') is not None and request.query_params.get('codigo_barras') != "":
            codigo_barras = request.query_params.get('codigo_barras')

        if request.query_params.get('equivalentes') is not None and request.query_params.get('equivalentes') != "":
            equivalentes = request.query_params.get('equivalentes')

        if request.query_params.get('referencia_cliente') is not None and request.query_params.get('referencia_cliente') != "":
            referencia_cliente = request.query_params.get(
                'referencia_cliente')

        if request.query_params.get('codigo_sinonimo') is not None and request.query_params.get('codigo_sinonimo') != "":
            codigo_sinonimo = request.query_params.get(
                'codigo_sinonimo')

        if 'filtros' in request.data:
            filtros = request.data['filtros']

        articulos = buscarArticulos(
            portal=portal, usuario=usuario, articulos_completos=articulos, busqueda=busqueda, filtros=filtros, avanzada=avanzada, codigo_articulo=codigo_articulo,
            descripcion=descripcion, palabras_clave=palabras_clave, codigo_barras=codigo_barras, equivalentes=equivalentes, referencia_cliente=referencia_cliente, codigo_sinonimo=codigo_sinonimo)

        if request.query_params.get('order') is not None:
            # si se solicita un orden concreto, ordenamos los artículos por el
            if request.query_params.get('order') == 'codigo':
                articulos = articulos.order_by('codigo_articulo')
            elif request.query_params.get('order') == 'descripcion':
                articulos = articulos.order_by('descrip_comercial')

        filtros_aplicables = obtener_filtros_aplicables(portal, articulos)

        filtros_claves_aplicables = obtener_filtros_claves_aplicables(
            portal, articulos)

        # paginamos el resultado, ya se controla de forma transparente el numero de artículos por pagina indicado en el parametro limit
        page = self.paginate_queryset(articulos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)

            response = self.get_paginated_response(serializer.data)

            response.data["filtros_aplicables"] = filtros_aplicables
            response.data["filtros_claves_aplicables"] = filtros_claves_aplicables
            return response

        serializer = self.get_serializer(articulos, many=True)

        return Response({"results": serializer.data, "filtros_aplicables": filtros_aplicables, "filtros_claves_aplicables": filtros_claves_aplicables})

    @action(detail=False, methods=['get'])
    def habitualCheckout(self, request):
        usuario = self.request.user
        portal = self.request.session['portal']

        endpoint = '/V1/B2B/PRODUCTS/HABITUAL'
        body = {'codigo_empresa': usuario.codigo_empresa,
                'codigo_portal': portal['codigo_portal'],
                'usuario_web': usuario.usuario_web
                }

        try:
            respuesta = comunica_lisa(
                endpoint=endpoint, body=body, portal=portal, usuario=usuario)
        except ConnectionError as e:
            logger.error("La peticion a lisa: " + endpoint +
                         " ha fallado, excepcion: " + str(e))
            return Response("No se ha podido obtener los artículos pedidos habitualmente", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error("La peticion a lisa: " + endpoint +
                         " ha fallado, excepcion: " + str(e))
            return Response("No se ha podido obtener los artículos pedidos habitualmente", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        lista_codigos = []

        if 'ARTICULOS' in respuesta and respuesta['ARTICULOS'] is not None:
            if isinstance(respuesta['ARTICULOS'], list):
                for arti in respuesta["ARTICULOS"]:
                    if arti["CODIGO_ARTICULO"] not in lista_codigos:
                        lista_codigos.append(arti["CODIGO_ARTICULO"])
            else:
                if respuesta["ARTICULOS"]['ARTICULO']["CODIGO_ARTICULO"] not in lista_codigos:
                    lista_codigos.append(
                        respuesta["ARTICULOS"]['ARTICULO']["CODIGO_ARTICULO"])

        articulos = self.get_queryset().filter(codigo_empresa=usuario.codigo_empresa,
                                               codigo_articulo__in=lista_codigos)

        page = self.paginate_queryset(articulos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(articulos, many=True)

        return Response({"results": serializer.data})

    @action(detail=False, methods=['get'])
    def descripcion(self, request):
        portal = self.request.session['portal']

        if self.request.GET.get('articulo') is not None:
            codigo_articulo = self.request.GET.get('articulo')
            articulo = Articulo.objects.get(
                codigo_empresa=portal['codigo_empresa'], codigo_articulo=codigo_articulo)

            articulo_serializado = self.get_serializer(
                articulo, many=False).data

            descripciones = {
                "codigo_articulo": codigo_articulo,
                "descrip_comercial": articulo_serializado['descrip_comercial'],
                "descrip_reducida": articulo_serializado['descrip_reducida'],
                "descrip_tecnica": articulo_serializado['descrip_tecnica'],
                "descrip_compra": articulo_serializado['descrip_compra'],
            }

            return Response(descripciones)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def ofertas(self, request):
        portal = self.request.session['portal']

        ofertas = EcomArticulosPortales.objects.filter(
            codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], oferta='S', activo='S').values('codigo_articulo')

        articulos = self.get_queryset().filter(codigo_articulo__in=ofertas)

        ofertas_familias = EcomFamiliasPortales.objects.filter(
            codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], oferta='S')

        for oferta_familia in ofertas_familias:
            estadistico = int(oferta_familia.numero_tabla)
            if estadistico == 1:
                articulos_fam = self.get_queryset().filter(
                    codigo_familia=oferta_familia.codigo_familia
                )
            else:
                campo = 'codigo_estad'+str(estadistico)
                articulos_fam = self.get_queryset().filter(
                    Q(**{"%s" % campo: oferta_familia.codigo_familia}))

            if len(articulos_fam) > 0:
                articulos = articulos.union(articulos_fam)

        page = self.paginate_queryset(articulos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(articulos, many=True)

        return Response({"results": serializer.data})

    @action(detail=False, methods=['get'])
    def novedades(self, request):
        portal = self.request.session['portal']

        novedades = EcomArticulosPortales.objects.filter(
            codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], novedad='S', activo='S')

        lista_codigos = []
        hoy = datetime.date.today()
        for novedad in novedades:  # solo novedades vigentes
            if novedad.numero_dias_novedad is not None and novedad.novedad_fecha_desde is not None and novedad.novedad_fecha_desde <= hoy and hoy <= novedad.novedad_fecha_desde + datetime.timedelta(days=novedad.numero_dias_novedad):
                lista_codigos.append(novedad.codigo_articulo)

        articulos = self.get_queryset().filter(
            codigo_articulo__in=lista_codigos)

        novedades_familias = EcomFamiliasPortales.objects.filter(
            codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], novedad='S')

        for novedad_familia in novedades_familias:
            if novedad_familia.numero_dias_novedad is not None and novedad_familia.novedad_fecha_desde is not None and novedad_familia.novedad_fecha_desde <= hoy and hoy <= novedad_familia.novedad_fecha_desde + datetime.timedelta(days=novedad_familia.numero_dias_novedad):
                estadistico = int(novedad_familia.numero_tabla)
                if estadistico == 1:
                    articulos_fam = self.get_queryset().filter(
                        codigo_familia=novedad_familia.codigo_familia
                    )
                else:
                    campo = 'codigo_estad'+str(estadistico)
                    articulos_fam = self.get_queryset().filter(
                        Q(**{"%s" % campo: novedad_familia.codigo_familia}))

                if len(articulos_fam) > 0:
                    articulos = articulos.union(articulos_fam)

        page = self.paginate_queryset(articulos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(articulos, many=True)

        return Response({"results": serializer.data})

    @action(detail=False, methods=['get'])
    def relacionados(self, request):
        portal = self.request.session['portal']

        if request.query_params.get('id_articulo') is not None:

            id_articulo = request.query_params.get('id_articulo')

            articulo = Articulo.objects.none()

            if Articulo.objects.filter(codigo_empresa=portal['codigo_empresa'], id=id_articulo).exists():
                articulo = Articulo.objects.get(
                    codigo_empresa=portal['codigo_empresa'], id=id_articulo)
            elif Articulo.objects.filter(codigo_empresa=portal['codigo_empresa'], codigo_articulo=id_articulo).exists():
                articulo = Articulo.objects.get(
                    codigo_empresa=portal['codigo_empresa'], codigo_articulo=id_articulo)
            else:
                return Response("El artículo indicado no existe", status=status.HTTP_400_BAD_REQUEST)

            relacionados = EcomArticulosRelacionados.objects.filter(
                codigo_empresa=portal['codigo_empresa'], codigo_articulo=articulo.codigo_articulo)

            articulos = self.get_queryset().filter(
                codigo_articulo__in=relacionados.values("codigo_articulo_relacionado"))

            page = self.paginate_queryset(articulos)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(articulos, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response("Falta el identificador del artículo", status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def equivalentes(self, request):
        portal = self.request.session['portal']

        if request.query_params.get('codigo_articulo') is not None:

            codigo_articulo = request.query_params.get('codigo_articulo')

            articulo = Articulo.objects.none()

            if Articulo.objects.filter(codigo_empresa=portal['codigo_empresa'], id=codigo_articulo).exists():
                articulo = Articulo.objects.get(
                    codigo_empresa=portal['codigo_empresa'], id=codigo_articulo)
            elif Articulo.objects.filter(codigo_empresa=portal['codigo_empresa'], codigo_articulo=codigo_articulo).exists():
                articulo = Articulo.objects.get(
                    codigo_empresa=portal['codigo_empresa'], codigo_articulo=codigo_articulo)
            else:
                return Response("El artículo indicado no existe", status=status.HTTP_400_BAD_REQUEST)

            articulos = self.get_queryset().filter(Exists(ArticulosEquivalentes.objects.filter(
                codigo_empresa=portal['codigo_empresa'], codigo_articulo=articulo.codigo_articulo, codigo_articulo_equ=OuterRef('codigo_articulo'))))

            page = self.paginate_queryset(articulos)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(articulos, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response("Falta el identificador del artículo", status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def migasArticulo(self, request):
        portal = self.request.session['portal']

        if request.query_params.get('articulo') is not None:

            id_articulo = request.query_params.get('articulo')

            articulos = self.get_queryset()

            if articulos.filter(codigo_articulo=id_articulo).exists():
                articulo = articulos.get(codigo_articulo=id_articulo)
            else:
                if articulos.filter(id=id_articulo).exists():
                    articulo = articulos.get(id=id_articulo)
                else:
                    return Response(status=status.HTTP_404_NOT_FOUND)

            familia_articulo = ''

            if portal['codigo_estadistico_familias'] == 1:
                familia_articulo = articulo.codigo_familia
            else:
                campo = 'codigo_estad' + \
                    str(portal['codigo_estadistico_familias'])
                diccionario_art = articulo.__dict__
                familia_articulo = diccionario_art[campo]

            arbol_familias = getArbolFamilias(
                portal['codigo_empresa'],  portal['codigo_estadistico_familias'], None, "", nivelInicio=None, nivelFin=None, nivelActual=None)

            migas = list()
            migas = generarMigas(
                portal['codigo_estadistico_familias'], arbol_familias, familia_articulo)

            return Response({"migas": migas})
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def listbyagente(self, request):

        registraActividad(self.request, 'articulos', 'busqueda')

        portal = self.request.session['portal']
        usuario = self.request.user
        articulos = self.get_queryset()  # todos los artículos
        busqueda = None
        filtros = None

        if request.query_params.get('search') is not None:
            busqueda = request.query_params.get('search')

        if 'filtros' in request.data:
            filtros = request.data['filtros']

        articulos_busqueda = buscarArticulos(
            portal, usuario, articulos, busqueda, filtros)

        articulos = Articulo.objects.filter(
            codigo_empresa=portal['codigo_empresa'], codigo_articulo__in=articulos_busqueda.values("codigo_articulo"))

        if usuario.agente is not None:
            clientes_agente = AgentesClientes.objects.filter(
                empresa=portal['codigo_empresa'], agente=usuario.agente)

            articulos = articulos.filter(Q(cliente_elaboracion__isnull=True) | (Q(cliente_elaboracion__isnull=False) & Q(
                cliente_elaboracion__in=clientes_agente.values("codigo_cliente"))))

        else:
            articulos = articulos.filter(cliente_elaboracion__isnull=True)

        if request.query_params.get('order') is not None:
            # si se solicita un orden concreto, ordenamos los artículos por el
            if request.query_params.get('order') == 'codigo':
                articulos = articulos.order_by('codigo_articulo')
            elif request.query_params.get('order') == 'descripcion':
                articulos = articulos.order_by('descrip_comercial')

        filtros_aplicables = obtener_filtros_aplicables(portal, articulos)

        filtros_claves_aplicables = obtener_filtros_claves_aplicables(
            portal, articulos)

        # paginamos el resultado, ya se controla de forma transparente el numero de artículos por pagina indicado en el parametro limit
        page = self.paginate_queryset(articulos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)

            response = self.get_paginated_response(serializer.data)

            response.data["filtros_aplicables"] = filtros_aplicables
            response.data["filtros_claves_aplicables"] = filtros_claves_aplicables
            return response

        serializer = self.get_serializer(articulos, many=True)

        return Response({"results": serializer.data, "filtros_aplicables": filtros_aplicables, "filtros_claves_aplicables": filtros_claves_aplicables})


class GaleriaViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        permisos.AllowCatalog
    ]

    def get_queryset(self):
        portal = self.request.session['portal']
        return ArticulosImagenesGaleria.objects.filter(empresa=portal['codigo_empresa'], imagen_web='S')

    serializer_class = GaleriaSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['=articulo']


class PrecioViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        permisos.AllowSemiPrivate
    ]
    serializer_class = PrecioSerializer

    def list(self, request):

        if request.query_params.get('codigo_articulo') is not None:

            codigo_articulo = request.query_params.get('codigo_articulo')

            cantidad_pedida = request.query_params.get('cant') if request.query_params.get(
                'cant') is not None and request.query_params.get('cant') != "" else 1

            domicilio_envio = request.query_params.get('domicilio_envio') if request.query_params.get(
                'domicilio_envio') is not None and request.query_params.get('domicilio_envio') != "" else ""

            usuario = self.request.user
            portal = self.request.session['portal']

            try:
                precio = calcula_precio_articulo(
                    portal, usuario, domicilio_envio, codigo_articulo, cantidad_pedida)

            except Exception as e:
                logger.error("La peticion del precio ha fallado: " + str(e))
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Comprobamos si el precio trae informacion de la divisa para recuperar el resto de info
            if precio['divisa_precio'] is not None and precio['divisa_precio'] != "":
                if Divisas.objects.filter(codigo=precio['divisa_precio']).exists():
                    divisa = Divisas.objects.get(
                        codigo=precio['divisa_precio'])

                    # Añadimos los informacion de la divisa al precio
                    precio['decimales_significativos'] = divisa.decimales_significativos
                    precio['decimales_precios'] = divisa.decimales_precios
                    precio['decimales_pvp'] = divisa.decimales_pvp

            return Response(precio)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def getPrecios(self, request):
        if request.data['articulos_cantidades'] is not None:
            usuario = self.request.user
            portal = self.request.session['portal']
            articulos_cantidades = request.data['articulos_cantidades']

            if articulos_cantidades is not None and len(articulos_cantidades) > 0:
                domicilio_envio = request.query_params.get('domicilio_envio') if request.query_params.get(
                    'domicilio_envio') is not None and request.query_params.get('domicilio_envio') != None else None

                try:
                    precios = calcula_precios_articulos(
                        portal, usuario, domicilio_envio, articulos_cantidades)
                except Exception as e:
                    logger.error(
                        "La peticion de precios ha fallado: " + str(e))
                    return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                # Comprobamos el contenido de precios en busca de articulos
                if ('articulos' in precios and len(precios['articulos']) > 0):
                    # Recorremos array
                    for articulo in precios['articulos']:
                        # Comprobamos si tienen la divisa cubierto
                        if articulo['divisa_precio'] is not None and articulo['divisa_precio'] != "":
                            if Divisas.objects.filter(codigo=articulo['divisa_precio']).exists():
                                divisa = Divisas.objects.get(
                                    codigo=articulo['divisa_precio'])
                                # Añadimos los informacion de la divisa al precio
                                articulo['decimales_significativos'] = divisa.decimales_significativos
                                articulo['decimales_precios'] = divisa.decimales_precios
                                articulo['decimales_pvp'] = divisa.decimales_pvp

                return Response(precios)
            else:
                return Response(status=status.HTTP_428_PRECONDITION_REQUIRED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ImagenViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        permisos.AllowCatalog
    ]
    serializer_class = GaleriaSerializer

    def get_queryset(self):
        portal = self.request.session['portal']
        return ArticulosImagenesGaleria.objects.filter(empresa=portal['codigo_empresa'], imagen_web='S')

    @no_logging()
    def list(self, request):

        if request.query_params.get('codigo_articulo') is not None and request.query_params.get('numero_imagen') is not None and request.query_params.get('principal') is not None:

            codigo_articulo = request.query_params.get('codigo_articulo')
            numero_imagen = request.query_params.get('numero_imagen')
            principal = request.query_params.get('principal')

            imagenes = self.get_queryset()

            if principal == 'S':
                if not imagenes.filter(articulo=codigo_articulo, principal='S').exists():
                    return HttpResponseNotFound('<h1>No hay imágenes para este artículo</h1>')

                datos_imagen = imagenes.filter(
                    articulo=codigo_articulo, principal='S').order_by('numero_imagen')[:1].get()

            else:
                if not imagenes.filter(articulo=codigo_articulo, numero_imagen=numero_imagen).exists():
                    return HttpResponseNotFound('<h1>No hay imágenes para este artículo</h1>')

                datos_imagen = imagenes.get(
                    articulo=codigo_articulo, numero_imagen=numero_imagen)

            if request.query_params.get('subidas') != 'S':
                return Response(base64.b64encode(datos_imagen.imagen))
            else:
                return Response({"articulo_referencia": datos_imagen.articulo_referencia, "extension": datos_imagen.extension})

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class DescargarImagenes(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        permisos.AllowCatalog
    ]
    serializer_class = ImagenSerializer

    def list(self, request):

        # Si no existe la imagen en local, descargo todas las del artículo por Lisa

        codigo_articulo = request.query_params.get('codigo_articulo')
        portal = self.request.session['portal']
        usuario = self.request.user

        directorio_actual = os.getcwd()
        directorio_portal = os.path.join(
            portal['codigo_empresa'] + '_' + portal['codigo_portal'], 'imagenes_articulos')
        directorio_final = os.path.join(directorio_actual, directorio_portal)

        if not os.path.exists(directorio_final):
            os.makedirs(directorio_final)

        endpoint = 'V1/B2B/PRODUCTS/IMAGES'

        body = {'codigo_empresa': portal['codigo_empresa'],  # '013',
                'codigo_portal': portal['codigo_portal'],
                'codigo_articulo': codigo_articulo
                }

        try:
            json_object = comunica_lisa(
                endpoint=endpoint, body=body, cache_seconds=360, portal=portal, usuario=usuario)
        except ConnectionError as e:
            logger.error("La peticion a lisa: " + endpoint +
                         " ha fallado, excepcion: " + str(e))
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error("La peticion a lisa: " + endpoint +
                         " ha fallado, excepcion: " + str(e))
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if isinstance(json_object['imagenes_articulo'], list):
            for imagen in json_object['imagenes_articulo']:

                nombre = os.path.join(directorio_final, codigo_articulo +
                                      '_' + imagen['numero_imagen'] + '.' + imagen['extension'])

                with open(nombre, "wb") as fh:
                    fh.write(base64.b64decode(imagen['imagen']))
        else:
            nombre = os.path.join(directorio_final, codigo_articulo +
                                  '_' + json_object['imagenes_articulo']['imagen_articulo']['numero_imagen'] + '.' + json_object['imagenes_articulo']['imagen_articulo']['extension'])

            with open(nombre, "wb") as fh:
                fh.write(base64.b64decode(
                    json_object['imagenes_articulo']['imagen_articulo']['imagen']))

        return Response(r.json())


class FamiliaViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = [
        permisos.AllowCatalog
    ]

    serializer_class = FamiliaSerializer

    def get_queryset(self):

        portal = self.request.session['portal']
        usuario = self.request.user

        familias = Familia.objects.filter(
            codigo_empresa=portal['codigo_empresa'])

        # Si el portal filtra por tipo cliente
        if portal['familias_x_tipo_cliente'] == 'S':

            lista_familias = []
            # Obtenemos las familias para el cliente
            ecom_fam = EcomFamiliasXTipoCliente.objects.filter(
                codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], tipo_cliente=usuario.tipo_cliente)

            for fam in ecom_fam:
                lista_familias.append(fam.codigo_familia)
                # Si la familia está marcada como completa buscamos los hijos
                if fam.familia_completa == 'S':
                    for f in listaFamiliaHijas(portal['codigo_empresa'], fam.numero_tabla, fam.codigo_familia):
                        lista_familias.append(f)

            # Filtramos las familias cuyo codigo coincida
            familias = familias.filter(codigo_familia__in=lista_familias)

        return familias

    def list(self, request):

        portal = self.request.session['portal']
        familias = self.get_queryset()

        numeroTabla = portal['codigo_estadistico_familias']
        codigoFamilia = ""

        if request.query_params.get('estadistico') is not None:
            numeroTabla = request.query_params.get('estadistico')

        if request.query_params.get('nivel_inicio') is not None and request.query_params.get('nivel_fin') is not None:
            nivelInicio = int(request.query_params.get('nivel_inicio'))
            nivelFin = int(request.query_params.get('nivel_fin'))

            arbolFamilias = getArbolFamilias(
                portal['codigo_empresa'], numeroTabla, familias, codigoFamilia, nivelInicio, nivelFin, None)
        else:
            arbolFamilias = getArbolFamilias(
                portal['codigo_empresa'], numeroTabla, familias, codigoFamilia, None, None, None)

        return Response({"arbolFamilias": arbolFamilias})

    @action(detail=False, methods=['get'])
    def getfamilia(self, request):

        portal = self.request.session['portal']

        if request.query_params.get('estadistico') is not None and request.query_params.get('familia') is not None:

            estadistico = request.query_params.get('estadistico')
            codigo_familia = request.query_params.get('familia')

            if Familia.objects.filter(
                    codigo_empresa=portal['codigo_empresa'], numero_tabla=estadistico, codigo_familia=codigo_familia).exists():

                familia = Familia.objects.get(
                    codigo_empresa=portal['codigo_empresa'], numero_tabla=estadistico, codigo_familia=codigo_familia)

                serializer = self.get_serializer(familia, many=False)

                return Response(data=serializer.data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class FiltrosViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = [
        permisos.AllowCatalog
    ]

    serializer_class = FiltroSerializer

    def get_queryset(self):

        portal = self.request.session['portal']

        return Filtro.objects.filter(codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'])

    def list(self, request):

        portal = self.request.session['portal']
        listaFiltros = []
        listaFiltrosClaves = []

        filtros = self.get_queryset()

        filtros_claves_estadisticas = FiltroClaveEstadistica.objects.filter(
            codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'])

        for filtro in filtros:

            serializer = self.get_serializer(filtro)

            filtroDict = serializer.data

            nivel_inicio = filtroDict['desde_nivel'] if filtroDict['desde_nivel'] is not None else 1
            nivel_fin = filtroDict['hasta_nivel'] if filtroDict['hasta_nivel'] is not None else 1

            familiasFiltro = getArbolFamilias(
                portal['codigo_empresa'], filtroDict['estadistico'], None, "", nivel_inicio, nivel_fin, None)
            filtroDict['familias'] = familiasFiltro
            listaFiltros.append(filtroDict)

        for filtro_clave in filtros_claves_estadisticas:

            filtroClavDict = FiltroClaveEstadisticaSerializer(
                filtro_clave).data

            clavesFiltro = getClavesEstadisticas(codigo_empresa=portal['codigo_empresa'],
                                                 clave_estadistica=filtroClavDict['clave_estadistica'], valor_clave="", nivelInicio=0, nivelFin=1)
            filtroClavDict['claves'] = clavesFiltro
            listaFiltrosClaves.append(filtroClavDict)

        return Response({"filtros": listaFiltros, "filtros_claves": listaFiltrosClaves})


class EcomArtAgrupHijosViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = [
        permisos.AllowCatalog
    ]

    serializer_class = EcomArtAgrupHijosSerializer

    def get_queryset(self):
        portal = self.request.session['portal']
        codigo_padre = self.request.GET.get('articulo')
        return EcomArtAgrupHijos.objects.filter(codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], codigo_padre=codigo_padre)


class EcomArtAgrupCondViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = [
        permisos.AllowCatalog
    ]

    serializer_class = EcomArtAgrupCondSerializer

    def get_queryset(self):
        portal = self.request.session['portal']
        codigo_padre = self.request.GET.get('articulo')
        return EcomArtAgrupCond.objects.filter(codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], codigo_padre=codigo_padre).order_by('orden')


class StockViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        permisos.AllowSemiPrivate
    ]

    def list(self, request):

        if request.query_params.get('articulo') is not None:

            codigo_articulo = request.query_params.get('articulo')
            usuario = self.request.user
            portal = self.request.session['portal']

            articulo = Articulo.objects.get(
                codigo_empresa=portal['codigo_empresa'], codigo_articulo=codigo_articulo)

            if portal['controlar_stock'] == 'S' and articulo.controlar_stock != 'N':

                presentacion = request.query_params.get('presentacion') if request.query_params.get(
                    'presentacion') is not None and request.query_params.get('presentacion') != "" else articulo.presentacion_web

                codigo_almacen = request.query_params.get('almacen') if request.query_params.get(
                    'almacen') is not None else ""

                situacion = request.query_params.get('situacion') if request.query_params.get(
                    'situacion') is not None else ""

                if codigo_almacen == "":
                    codigo_almacen = usuario.codigo_almacen if usuario.codigo_almacen is not None else portal[
                        'codigo_almacen']

                try:
                    stock = obtenerStock(
                        portal, usuario, codigo_articulo, presentacion, codigo_almacen, situacion)
                except Exception as e:
                    logger.error(
                        "La peticion de stock ha fallado, excepcion: " + str(e))
                    return Response({'stock': 'N',
                                     'texto_stock': "NO DISPONIBLE"})
                else:
                    cantidad = 0
                    if 'stocks' in stock:
                        cantidad = stock['stocks']['total_cantidad_presentacion']
                        texto_stock = stock['stocks']['texto_stock']
                    else:
                        cantidad = 0
                        texto_stock = stock['stocks']['texto_stock']

                    if float(cantidad) > 0:
                        return Response({'stock': 'S',
                                         'texto_stock': texto_stock})
                    else:
                        return Response({'stock': 'N',
                                         'texto_stock': texto_stock})
            else:
                return Response({'stock': 'S',
                                 'texto_stock': ""})

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def cantidadStock(self, request):

        if request.query_params.get('articulo') is not None:

            codigo_articulo = request.query_params.get('articulo')
            usuario = self.request.user
            portal = self.request.session['portal']
            cantidad = 0

            articulo = Articulo.objects.get(
                codigo_empresa=portal['codigo_empresa'], codigo_articulo=codigo_articulo)

            if portal['controlar_stock'] == 'S' and articulo.controlar_stock != 'N':

                presentacion = request.query_params.get('presentacion') if request.query_params.get(
                    'presentacion') is not None and request.query_params.get('presentacion') != "" else articulo.presentacion_web

                codigo_almacen = request.query_params.get('almacen') if request.query_params.get(
                    'almacen') is not None else ""

                situacion = request.query_params.get('situacion') if request.query_params.get(
                    'situacion') is not None else ""

                if codigo_almacen == "":
                    codigo_almacen = usuario.codigo_almacen if usuario.codigo_almacen is not None else portal[
                        'codigo_almacen']

                try:
                    cantidad_stock = obtenerStock(
                        portal, usuario, codigo_articulo, presentacion, codigo_almacen, situacion)

                except Exception as e:
                    logger.error(
                        "La peticion de cantidad_stock ha fallado, excepcion: " + str(e))
                    return Response({'stock': cantidad,
                                     'texto_stock': "NO DISPONIBLE"})
                else:

                    cantidad = 0
                    if 'stocks' in cantidad_stock:
                        cantidad = cantidad_stock['stocks']['total_cantidad_presentacion']
                        texto_stock = cantidad_stock['stocks']['texto_stock']
                    else:
                        cantidad = 0
                        texto_stock = cantidad_stock['stocks']['texto_stock']

                return Response({'stock': cantidad,
                                 'texto_stock': texto_stock})

            else:
                return Response({'stock': 'S',
                                 'texto_stock': ""})

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def multipleStock(self, request):
        if request.data['articulos_stock'] is not None:

            usuario = self.request.user
            portal = self.request.session['portal']
            articulos_stock = request.data['articulos_stock']
            cantidad_stock = []

            if portal['controlar_stock'] == 'S':

                try:
                    cantidad_stock = obtenerStocks(
                        portal, usuario, articulos_stock)

                except Exception as e:
                    logger.error(
                        "La peticion de multiple_stock ha fallado, excepcion: " + str(e))

                    for articulo in articulos_stock:
                        articulo_procesado = {'codigo_articulo': articulo['codigo_articulo'],
                                              'stock': 'N',
                                              'texto_stock': "ERROR"
                                              }
                        cantidad_stock.append(articulo_procesado)

                    return Response(cantidad_stock, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    stock_procesado = []
                    for articulo in cantidad_stock:
                        if int(articulo['stock']) > 0:
                            stock = 'S'
                        else:
                            stock = 'N'

                        articulo_procesado = {
                            'codigo_articulo': articulo['codigo_articulo'],
                            'stock': stock,
                            'texto_stock': articulo['texto_stock']
                        }
                        stock_procesado.append(articulo_procesado)
                    return Response(stock_procesado, status=status.HTTP_200_OK)

            else:
                for articulo in articulos_stock:
                    articulo_procesado = {'codigo_articulo': articulo['codigo_articulo'],
                                          'stock': 'S',
                                          'texto_stock': "Disponible"
                                          }
                    cantidad_stock.append(articulo_procesado)

                return Response(cantidad_stock, status=status.HTTP_200_OK)

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def multipleStockCantidad(self, request):
        if request.data['articulos_stock'] is not None:

            usuario = self.request.user
            portal = self.request.session['portal']
            articulos_stock = request.data['articulos_stock']
            cantidad_stock = []

            if portal['controlar_stock'] == 'S':

                try:
                    cantidad_stock = obtenerStocks(
                        portal, usuario, articulos_stock)

                except Exception as e:
                    logger.error(
                        "La peticion de multiple_cantidad_stock ha fallado, excepcion: " + str(e))
                    for articulo in articulos_stock:
                        articulo_procesado = {'codigo_articulo': articulo['codigo_articulo'],
                                              'stock': -1,
                                              'texto_stock': "ERROR"
                                              }
                        cantidad_stock.append(articulo_procesado)

                    return Response(cantidad_stock, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    return Response(cantidad_stock, status=status.HTTP_200_OK)

            else:
                for articulo in articulos_stock:
                    articulo_procesado = {'codigo_articulo': articulo['codigo_articulo'],
                                          'stock': 'S',
                                          'texto_stock': ""
                                          }
                    cantidad_stock.append(articulo_procesado)

                return Response(cantidad_stock, status=status.HTTP_200_OK)

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ArticulosDocViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        permisos.AllowCatalog
    ]

    def get_queryset(self):
        portal = self.request.session['portal']
        return ArticulosDoc.objects.filter(codigo_empresa=portal['codigo_empresa'])

    serializer_class = ArticulosDocSerializer

    def list(self, request):

        if request.query_params.get('codigo_articulo') is not None:
            codigo_articulo = request.query_params.get('codigo_articulo')

            articulos_doc = self.get_queryset()

            articulos_doc = articulos_doc.filter(
                codigo_articulo=codigo_articulo)

            serializer = self.get_serializer(articulos_doc, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class ArticulosAuxViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        permisos.AllowCatalog
    ]

    def get_queryset(self):
        portal = self.request.session['portal']
        return ArticulosAux.objects.filter(codigo_empresa=portal['codigo_empresa'])

    serializer_class = ArticulosAuxSerializer

    def retrieve(self, request, pk=None):

        if pk is not None:

            articulos_aux = self.get_queryset()

            articulo_aux = None

            if articulos_aux.filter(codigo_articulo=pk).exists():
                articulo_aux = articulos_aux.get(codigo_articulo=pk)
            else:
                if articulos_aux.filter(id=pk).exists():
                    articulo_aux = articulos_aux.get(id=pk)

            if articulo_aux is not None:
                articulo_aux_serializado = self.get_serializer(
                    articulo_aux).data
            else:
                articulo_aux_serializado = {}

            return Response(articulo_aux_serializado, status=status.HTTP_200_OK)

        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def list(self, request):

        if request.query_params.get('codigo_articulo') is not None:
            codigo_articulo = request.query_params.get('codigo_articulo')

            articulos_aux = self.get_queryset()

            articulos_aux = articulos_aux.filter(
                codigo_articulo=codigo_articulo)

            serializer = self.get_serializer(articulos_aux, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class EcomSubPresentacionesViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        permisos.AllowCatalog
    ]

    def get_queryset(self):
        portal = self.request.session['portal']
        return EcomSubPresentaciones.objects.filter(codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'])

    serializer_class = EcomSubPresentacionesSerializer

    def list(self, request):

        if request.query_params.get('codigo_articulo') is not None:
            codigo_articulo = request.query_params.get('codigo_articulo')

            subpresentaciones = self.get_queryset()

            subpresentaciones = subpresentaciones.filter(
                codigo_articulo=codigo_articulo)

            serializer = self.get_serializer(subpresentaciones, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class FamiliasImagenesViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        permisos.AllowCatalog
    ]

    def get_queryset(self):
        portal = self.request.session['portal']
        usuario = self.request.user

        familias = FamiliasImagenes.objects.filter(
            codigo_empresa=portal['codigo_empresa'])

        # Si el portal filtra por tipo cliente
        if portal['familias_x_tipo_cliente'] == 'S':

            lista_familias = []
            # Obtenemos las familias para el cliente
            ecom_fam = EcomFamiliasXTipoCliente.objects.filter(
                codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], tipo_cliente=usuario.tipo_cliente)

            for fam in ecom_fam:
                lista_familias.append(fam.codigo_familia)
                # Si la familia está marcada como completa buscamos los hijos
                if fam.familia_completa == 'S':
                    for f in listaFamiliaHijas(portal['codigo_empresa'], fam.numero_tabla, fam.codigo_familia):
                        lista_familias.append(f)

            # Filtramos las familias cuyo codigo coincida
            familias = familias.filter(codigo_familia__in=lista_familias)

        return familias

    serializer_class = FamiliasImagenesSerializer

    def retrieve(self, request, pk=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):

        imagenes_familia = self.get_queryset()

        if request.query_params.get('estadistico') is not None and request.query_params.get('estadistico') != "":
            numero_tabla = request.query_params.get('estadistico')
            imagenes_familia = imagenes_familia.filter(
                numero_tabla=numero_tabla)

            if request.query_params.get('familia') is not None and request.query_params.get('familia') != "":
                codigo_familia = request.query_params.get('familia')
                imagenes_familia = imagenes_familia.filter(
                    codigo_familia=codigo_familia)

                if request.query_params.get('imagen') is not None and request.query_params.get('imagen') != "":
                    codigo_imagen = request.query_params.get('imagen')
                    imagenes_familia = imagenes_familia.filter(
                        codigo_imagen=codigo_imagen)

                if request.query_params.get('principal') is not None and request.query_params.get('principal') != "":
                    principal = request.query_params.get('principal')
                    imagenes_familia = imagenes_familia.filter(
                        imagen_principal=principal)

        serializer = self.get_serializer(imagenes_familia, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class CodigosBarrasViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        permisos.AllowCatalog
    ]

    def get_queryset(self):
        portal = self.request.session['portal']
        return CodigoBarras.objects.filter(codigo_empresa=portal['codigo_empresa'])

    serializer_class = CodigosBarrasSerializer

    def list(self, request):

        if request.query_params.get('articulo') is not None and request.query_params.get('sistema') is not None:
            codigo_articulo = request.query_params.get('articulo')
            sistema_cod_barras = request.query_params.get('sistema')

            codigos_barras = self.get_queryset().filter(
                codigo_sist_barra=sistema_cod_barras, codigo_articulo=codigo_articulo)

            serializer = self.get_serializer(codigos_barras, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class CadenaLogisticaViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        permisos.AllowCatalog
    ]

    def get_queryset(self):
        portal = self.request.session['portal']
        return CadenaLogistica.objects.filter(codigo_empresa=portal['codigo_empresa'])

    serializer_class = CadenaLogisticaSerializer

    def list(self, request):
        portal = self.request.session['portal']

        if request.query_params.get('articulo') is not None:

            if Articulo.objects.filter(codigo_empresa=portal['codigo_empresa'], codigo_articulo=request.query_params.get('articulo')).exists():

                articulo = Articulo.objects.get(
                    codigo_empresa=portal['codigo_empresa'], codigo_articulo=request.query_params.get('articulo'))
                codigo_articulo = articulo.codigo_articulo
                tipo_cadena_logistica = request.query_params.get('tipo') if request.query_params.get(
                    'tipo') is not None and request.query_params.get('tipo') != "" else articulo.tipo_cadena_logistica

                if self.get_queryset().filter(
                        tipo_cadena=tipo_cadena_logistica, codigo_articulo=codigo_articulo).exists():
                    cadena_logistica = self.get_queryset().get(
                        tipo_cadena=tipo_cadena_logistica, codigo_articulo=codigo_articulo)

                    serializer = self.get_serializer(
                        cadena_logistica, many=False)

                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response(status=status.HTTP_404_NOT_FOUND)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class PresentacionesViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = [
        permisos.AllowCatalog
    ]

    serializer_class = PresentacionesSerializer

    def get_queryset(self):

        return Presentaciones.objects.all()


class PresenArticuloViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = [
        permisos.AllowCatalog
    ]

    def get_queryset(self):
        portal = self.request.session['portal']
        return PresenArticulo.objects.filter(codigo_empresa=portal['codigo_empresa'])

    serializer_class = PresenArticuloSerializer

    def list(self, request):

        if request.query_params.get('articulo') is not None:
            codigo_articulo = request.query_params.get('articulo')

            presen_articulo = self.get_queryset().filter(
                codigo_articulo=codigo_articulo)

            serializer = self.get_serializer(presen_articulo, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class SugerenciasViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = [
        permisos.AllowCatalog
    ]

    @action(detail=False, methods=['get'])
    def busquedasrealizadas(self, request):
        portal = self.request.session['portal']
        usuario = self.request.user

        hoy = datetime.date.today()

        sesiones = EcomSesiones.objects.filter(
            codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'],
            usuario_web=usuario.usuario_web, fecha__gte=(hoy - datetime.timedelta(days=30))).order_by('-fecha')

        acciones = EcomSesionesAccion.objects.filter(
            codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], accion='busqueda',
            id_sesion__in=sesiones.values('id_sesion')).order_by('-fecha_accion')

        parametros = EcomSesionesAccionParams.objects.filter(
            codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'],
            id_accion__in=acciones.values('id_accion')).order_by('-id_accion')

        busquedas_palabra = parametros.filter(parametro='palabra')

        resultados = list(busquedas_palabra.values(
            "parametro", "valor"))

        resultados_filtrados = list()

        for resultado in resultados:
            resultados_filtrados.append(
                resultado) if resultado not in resultados_filtrados else None

        return Response(resultados_filtrados, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def autocompletado(self, request):

        portal = self.request.session['portal']

        if self.request.GET.get('busqueda') is not None:

            busqueda = self.request.GET.get('busqueda')

            articulos = Articulo.objects.filter(
                codigo_empresa=portal['codigo_empresa'], codigo_articulo__icontains=busqueda)

            descripciones = ArticulosDescripcionWeb.objects.filter(
                codigo_empresa=portal['codigo_empresa'], idioma=portal['idioma'], descripcion_web__icontains=busqueda)

            familias = Familia.objects.filter(
                codigo_empresa=portal['codigo_empresa'], descripcion__icontains=busqueda)

            familias = familias.filter(Q(numero_tabla=portal['codigo_estadistico_familias']) | Q(
                numero_tabla__in=Filtro.objects.filter(codigo_empresa=portal['codigo_empresa'],
                                                       codigo_portal=portal['codigo_portal']).values("estadistico")
            ))

            claves = ValoresClavesArt.objects.filter(
                empresa=portal['codigo_empresa'], nombre__icontains=busqueda).order_by("orden")

            claves = claves.filter(clave__in=FiltroClaveEstadistica.objects.filter(codigo_empresa=portal['codigo_empresa'],
                                                                                   codigo_portal=portal['codigo_portal']).values("clave_estadistica"))

            resultados = list()

            for articulo in articulos:
                resultados.append({'parametro': 'palabra',
                                   'valor': articulo.codigo_articulo})

            for descripcion in descripciones:
                resultados.append({'parametro': 'palabra',
                                   'valor': descripcion.descripcion_web})

            for familia in familias:
                resultados.append({'parametro': 'familia',
                                   'estadistico': familia.numero_tabla,
                                   'valor': familia.codigo_familia,
                                   'descripcion': familia.descripcion})
            for clave in claves:
                resultados.append({'parametro': 'clave_estadistica',
                                   'estadistico': clave.clave,
                                   'valor': clave.valor_clave,
                                   'descripcion': clave.nombre})

            return Response(resultados, status=status.HTTP_200_OK)

        else:
            return Response("Falta parámetro búsqueda", status=status.HTTP_400_BAD_REQUEST)


class ClavesEstadisticasArtViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = [
        permisos.AllowCatalog
    ]
    serializer_class = ClavesEstadisticasArtSerializer

    def get_queryset(self):
        portal = self.request.session['portal']
        return ClavesEstadisticasArt.objects.filter(empresa=portal['codigo_empresa'])

    def retrieve(self, request, pk=None):

        if pk is not None:

            claves_estadisticas = self.get_queryset()

            clave_estadistica = ClavesEstadisticasArt.objects.none()

            if claves_estadisticas.filter(clave=pk).exists():
                clave_estadistica = claves_estadisticas.get(clave=pk)
            else:
                if claves_estadisticas.filter(id=pk).exists():
                    clave_estadistica = claves_estadisticas.get(id=pk)
                else:
                    return Response(status=status.HTTP_404_NOT_FOUND)

            clave_estadistica_serializada = self.get_serializer(
                clave_estadistica).data
            valores = ValoresClavesArt.objects.filter(
                empresa=clave_estadistica_serializada['empresa'], clave=clave_estadistica_serializada['clave']).order_by("orden")

            valores_serializados = ValoresClavesArtSerializer(
                valores, many=True).data

            clave_estadistica_serializada['valores'] = valores_serializados

            return Response(clave_estadistica_serializada)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def list(self, request):

        claves_estadisticas = self.get_queryset()

        claves_estadisticas_serializadas = self.get_serializer(
            claves_estadisticas, many=True).data

        for clave_estadistica_serializada in claves_estadisticas_serializadas:

            valores = ValoresClavesArt.objects.filter(
                empresa=clave_estadistica_serializada['empresa'], clave=clave_estadistica_serializada['clave']).order_by("orden")

            valores_serializados = ValoresClavesArtSerializer(
                valores, many=True).data

            clave_estadistica_serializada['valores'] = valores_serializados

        return Response(claves_estadisticas_serializadas, status=status.HTTP_200_OK)


class ArticulosClavesEstadisticasViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = [
        permisos.AllowCatalog
    ]
    serializer_class = ArticulosClavesEstadisticasSerializer

    def get_queryset(self):
        portal = self.request.session['portal']
        return ArticulosClavesEstadisticas.objects.filter(empresa=portal['codigo_empresa'])

    def retrieve(self, request, pk=None):

        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def list(self, request):

        valores_claves_estadisticas_articulos = self.get_queryset()

        if self.request.GET.get('articulo') is not None:
            codigo_articulo = self.request.GET.get('articulo')
            valores_claves_estadisticas_articulos = valores_claves_estadisticas_articulos.filter(
                codigo_articulo=codigo_articulo)

            if self.request.GET.get('clave') is not None:
                clave = self.request.GET.get('clave')
                valores_claves_estadisticas_articulos = valores_claves_estadisticas_articulos.filter(
                    clave=clave)

            valores_claves_estadisticas_articulos_serializadas = self.get_serializer(
                valores_claves_estadisticas_articulos, many=True).data

            return Response(valores_claves_estadisticas_articulos_serializadas, status=status.HTTP_200_OK)
        else:
            return Response("Falta el código del artículo", status=status.HTTP_404_NOT_FOUND)


class OfertasMultiplesViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        permisos.AllowSemiPrivate
    ]
    serializer_class = OfertasMultiplesSerializer

    def list(self, request):

        if request.query_params.get('codigo_articulo') is not None:

            codigo_articulo = request.query_params.get('codigo_articulo')
            presentacion = request.query_params.get('presentacion')
            portal = self.request.session['portal']
            usuario = self.request.user
            codigo_cliente = usuario.codigo_cliente

            try:
                ofertasMultiples = calcula_ofertas_multiples(
                    portal, usuario, codigo_articulo, codigo_cliente, presentacion)

            except Exception as e:
                logger.error(
                    "La peticion de las ofertas ha fallado: " + str(e))
                return Response("La peticion de las ofertas ha fallado", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response(ofertasMultiples)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class DetalleListaReferenciasViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        permisos.AllowSemiPrivate
    ]
    serializer_class = DetalleListaReferenciasSerializer

    def get_queryset(self):
        portal = self.request.session['portal']

        return DetalleListaReferencias.objects.filter(empresa=portal['codigo_empresa'])

    def list(self, request):

        portal = self.request.session['portal']
        usuario = self.request.user

        if ClientesParametros.objects.filter(
                empresa=portal['codigo_empresa'], codigo_cliente=usuario.codigo_cliente).exists():

            parametros = ClientesParametros.objects.get(
                empresa=portal['codigo_empresa'], codigo_cliente=usuario.codigo_cliente)

            if parametros.lista_rfcas is not None:

                referencias = DetalleListaReferencias.objects.filter(
                    empresa=portal['codigo_empresa'], codigo_lista=parametros.lista_rfcas)

                serializer = self.get_serializer(referencias, many=True)

                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response("El cliente no tiene lista de referencias asignada", status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response("El cliente no tiene lista de referencias asignada", status=status.HTTP_400_BAD_REQUEST)


class StockAluminioViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        permisos.AllowSemiPrivate
    ]

    def list(self, request):
        if request.query_params.get('articulo') is not None:
            codigo_articulo = request.query_params.get('articulo')
            usuario = self.request.user
            portal = self.request.session['portal']
            if Articulo.objects.filter(codigo_empresa=portal['codigo_empresa'], codigo_articulo=codigo_articulo).exists():

                articulo = Articulo.objects.get(
                    codigo_empresa=portal['codigo_empresa'], codigo_articulo=codigo_articulo)
                if (portal['controlar_stock'] == 'S' or portal['controlar_stock'] == 'C') and articulo.controlar_stock != 'N':
                    presentacion = request.query_params.get('presentacion') if request.query_params.get(
                        'presentacion') is not None and request.query_params.get('presentacion') != "" else articulo.unidad_codigo1
                    codigo_almacen = request.query_params.get('almacen') if request.query_params.get(
                        'almacen') is not None else ""
                    situacion = request.query_params.get('situacion') if request.query_params.get(
                        'situacion') is not None else ""
                    if codigo_almacen == "" and portal['sector_empresa'] != 'AL':
                        codigo_almacen = usuario.codigo_almacen if usuario.codigo_almacen is not None else portal[
                            'codigo_almacen']
                    try:
                        stock = obtenerStock(
                            portal, usuario, codigo_articulo, presentacion, codigo_almacen, situacion)
                    except Exception as e:
                        logger.error(
                            "La peticion de stock ha fallado, excepcion: " + str(e))
                        return Response({'stock': 'N',
                                        'texto_stock': "NO DISPONIBLE"})
                    else:
                        cantidad = 0
                        if 'stocks' in stock:
                            cantidad = stock['stocks']['total_cantidad_presentacion']
                            texto_stock = stock['stocks']['texto_stock']
                        else:
                            cantidad = 0
                            texto_stock = stock['stocks']['texto_stock']
                        if float(cantidad) > 0:
                            if 'stock' in stock['stocks']:
                                return Response({'stock': 'S',
                                                'texto_stock': texto_stock,
                                                 'datos_stock': stock['stocks']['stock'],
                                                 'pedidos_pendientes': stock['stocks']['pedidos_pendientes']})
                            else:
                                return Response({'stock': 'S',
                                                'texto_stock': texto_stock})
                        else:
                            return Response({'stock': 'N',
                                            'texto_stock': texto_stock})
                else:
                    return Response({'stock': 'S',
                                    'texto_stock': ""})
            else:
                return Response("El articulo no existe en base de datos.", status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
