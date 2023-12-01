from decimal import *
from pedidos.models import EcomFormasEnvioTarifas
from portales.lisa import comunica_lisa
from .helpers import procesa_linea, procesa_pedido
from pedidos.models import WebPedidos, WebPedidosLin, Divisas
from django.db.models import Max
import datetime
import simplejson as json
import logging
from portales.enconders import fecha_encoder
from articulos.models import Articulo, EcomArticulosProvincias
from domicilios.models import DomiciliosEnvio
from .serializers import WebPedidosLinSerializer
from articulos.functions import calcula_precio_articulo, obtenerStock, calcula_precios_articulos, obtenerStocks
from django.db.models import Q

getcontext().prec = 4
logger = logging.getLogger("rad_logger")


def insertarLineaPedido(portal, usuario, pedido, datos_linea, sumar_cantidad_anterior=False):

    numero_linea = siguienteLinea(pedido.id_pedido)

    datos_linea['id_pedido'] = pedido.id_pedido
    datos_linea['numero_linea'] = numero_linea
    datos_linea['numero_linea_origen'] = datos_linea['numero_linea_origen'] if "numero_linea_origen" in datos_linea and datos_linea[
        'numero_linea_origen'] is not None and datos_linea['numero_linea_origen'] != "" else None
    datos_linea['tipo_linea'] = datos_linea['tipo_linea'] if 'tipo_linea' in datos_linea and datos_linea[
        'tipo_linea'] is not None and datos_linea['tipo_linea'] != "" else portal['tipo_linea_pedidos']

    ahora = datetime.date.today()

    if Articulo.objects.filter(codigo_empresa=portal['codigo_empresa'], codigo_articulo=datos_linea['articulo']).exists():

        # Recuperamos articulo
        articulo = Articulo.objects.get(
            codigo_articulo=datos_linea['articulo'], codigo_empresa=portal['codigo_empresa'])

        # Comprobamos si está activo
        if articulo.codigo_situacion is None or articulo.codigo_situacion != 'A':
            logger.error(
                'El articulo: ' + datos_linea['articulo'] + ' no está activo actualmente')
            raise Exception(
                'El articulo: ' + datos_linea['articulo'] + ' no está activo actualmente')

        # Comprobamos si el articulo ha expirado
        if not Articulo.objects.filter(Q(fecha_baja__isnull=True) | Q(fecha_baja__gte=ahora)).filter(codigo_empresa=portal['codigo_empresa'],
                                                                                                     codigo_articulo=articulo.codigo_articulo).exists():
            logger.error(
                'El articulo: ' + datos_linea['articulo'] + ' no está activo actualmente')
            raise Exception(
                'El articulo: ' + datos_linea['articulo'] + ' no está activo actualmente')

        # Comprobamos si se venden por provincias
        if portal['activar_articulos_provincia'] == 'S':

            if pedido.domicilio_envio is not None:

                domicilio_envio = DomiciliosEnvio.objects.get(empresa=portal['codigo_empresa'], codigo_cliente=usuario.codigo_cliente,
                                                              numero_direccion=pedido.domicilio_envio)
                codigo_estado = domicilio_envio.estado
                codigo_provincia = domicilio_envio.provincia

                if not EcomArticulosProvincias.objects.filter(Q(fecha_baja__isnull=True) | Q(fecha_baja__gte=ahora)).filter(empresa=portal['codigo_empresa'],
                                                                                                                            portal=portal[
                        'codigo_portal'],
                        estado=codigo_estado,
                        provincia=codigo_provincia,
                        articulo=articulo.codigo_articulo).exists():
                    logger.error(
                        'El articulo: ' + datos_linea['articulo'] + ' no está disponible en la dirección solicitada')
                    raise Exception(
                        'El articulo: ' + datos_linea['articulo'] + ' no está disponible en la dirección solicitada')

        # Comprobamos que existe cantidad
        if 'cantidad_pedida' in datos_linea:
            if float(datos_linea['cantidad_pedida']) <= 0:
                raise Exception(
                    'La cantidad pedida debe ser mayor que 0 ')
        else:
            raise Exception(
                'Error obteniendo la cantidad de la linea, contacte con su administrador')

        # Comprobamos que cumple las condiciones del articulo
        if articulo.cantidad_minima is not None:

            if float(datos_linea['cantidad_pedida']) < articulo.cantidad_minima:
                raise Exception(
                    'La cantidad pedida: ' + str(datos_linea['cantidad_pedida']) + ', no llega a la cantidad mínima: ' + str(articulo.cantidad_minima))

        if articulo.cantidad_maxima is not None:

            if float(datos_linea['cantidad_pedida']) > articulo.cantidad_maxima:
                raise Exception(
                    'La cantidad pedida: ' + str(datos_linea['cantidad_pedida']) + ', excede la cantidad máxima: ' + str(articulo.cantidad_maxima))

        if articulo.multiplo is not None:

            if float(datos_linea['cantidad_pedida']) % articulo.multiplo != 0:
                raise Exception(
                    'La cantidad pedida: ' + str(datos_linea['cantidad_pedida']) + ', debe ser un múltiplo de: ' + str(articulo.multiplo))

        # Calculamos el stock si es necesario
        if portal['controlar_stock'] == 'S' and datos_linea['tipo_linea'] == 'P' and articulo.controlar_stock != 'N' and ('tipo_articulo' not in datos_linea or datos_linea['tipo_articulo'] not in ['T', 'F']):
            if usuario.presentacion_defecto is not None:
                presentacion = usuario.presentacion_defecto
            else:
                if portal['presentacion_defecto'] is not None:
                    presentacion = portal['presentacion_defecto']
                else:
                    presentacion = articulo.presentacion_web

            if pedido.almacen is not None:

                codigo_almacen = pedido.almacen
            else:

                codigo_almacen = usuario.codigo_almacen if usuario.codigo_almacen is not None else portal[
                    'codigo_almacen']

            tipo_situacion = ""

            try:
                stock = obtenerStock(
                    portal, usuario, articulo.codigo_articulo, presentacion, codigo_almacen, tipo_situacion)
            except Exception as e:
                logger.error(
                    "La peticion de stock ha fallado, excepcion: " + str(e))
                raise Exception(
                    'Se ha producido un error durante la comprobación de stock')

            if stock['stocks']['total_cantidad_presentacion'] == 0 or int(float(stock['stocks']['total_cantidad_presentacion'])) < int(float(datos_linea['cantidad_pedida'])):
                raise Exception("No hay stock disponible en estos momentos, disponible: " +
                                str(int(float(stock['stocks']['total_cantidad_presentacion']))))

        try:
            informacion_precio = calcula_precio_articulo(
                portal, usuario, pedido.domicilio_envio, articulo.codigo_articulo, datos_linea['cantidad_pedida'])
        except Exception as e:
            logger.error(
                "La peticion del precio ha fallado, excepcion: " + str(e))
            raise Exception(
                'Se ha producido un error durante la comprobación del precio')

        # Seteamos los valores de la linea
        datos_linea['estado_linea'] = datos_linea['estado_linea'] if 'estado_linea' in datos_linea and datos_linea['estado_linea'] != "" else "B"
        datos_linea['id_articulo'] = articulo.id
        datos_linea['observaciones'] = datos_linea['observaciones'] if 'observaciones' in datos_linea and datos_linea['observaciones'] != "" else ""
        datos_linea['sub_pres'] = datos_linea['sub_pres'] if 'sub_pres' in datos_linea and datos_linea['sub_pres'] != "" else None
        datos_linea['sub_pres_cant'] = datos_linea['sub_pres_cant'] if 'sub_pres_cant' in datos_linea and datos_linea['sub_pres_cant'] != "" else None
        datos_linea['sub_pres_fc'] = datos_linea['sub_pres_fc'] if 'sub_pres_fc' in datos_linea and datos_linea['sub_pres_fc'] != "" else None
        datos_linea['pres_fc'] = datos_linea['pres_fc'] if 'pres_fc' in datos_linea and datos_linea['pres_fc'] != "" else None
        datos_linea['presentacion_escogida'] = datos_linea['presentacion_escogida'] if 'presentacion_escogida' in datos_linea and datos_linea['presentacion_escogida'] != "" else None
        datos_linea['precio_manual'] = datos_linea['precio_manual'] if 'precio_manual' in datos_linea and datos_linea['precio_manual'] is not None and datos_linea[
            'precio_manual'] != "" else informacion_precio['precio_manual'] if 'precio_manual' in informacion_precio else None
        datos_linea['clave_actuacion'] = informacion_precio['clave_actuacion'] if 'clave_actuacion' in informacion_precio else None

        if datos_linea['precio_venta'] == 0 and datos_linea['tipo_linea'] != "R" and ('tipo_articulo' not in datos_linea or datos_linea['tipo_articulo'] != "F"):
            raise Exception(
                'No se permiten líneas con precio 0')

        # Comprobamos si la linea es de catalogo
        datos_linea['catalogo'] = "S" if articulo.tipo is not None and articulo.tipo == "C" else "N"

        # Comprobamos si la linea esta pendiente de validación (Carnet)
        if 'valida_carnet' in datos_linea:  # Parametro control carnet
            # S - Carnet valido, no se necesita verificacion
            # N - Linea de verificacion
            if datos_linea['valida_carnet'] == 'N':
                datos_linea['estado_linea'] = "C"

            # Eliminamos el atributo de la linea para evitar fallo serializer
            datos_linea.pop('valida_carnet')

        # Comprobamos si la linea esta pendiente de validación (Receta)
        if 'valida_receta' in datos_linea:  # Parametro control receta
            # N - No debería llegar aquí (Error Front)
            # M, M1, M2, M3 - Se ha enviado mensaje informativo y la linea debe verificarse
            # S - No se necesita verificacion (Usuario Autorizado)

            if datos_linea['valida_receta'] in ('M', 'M1', 'M2', 'M3'):
                # Receta adjunta digitalmente
                if datos_linea['valida_receta'] == 'M':
                    if datos_linea['estado_linea'] == 'C':
                        datos_linea['estado_linea'] = 'C0' # Pdte: Carnet con receta adjunta / o mayorista sin receta
                    else:
                        datos_linea['estado_linea'] = 'AX'

                # No dispone de receta
                if datos_linea['valida_receta'] == 'M1':
                    if datos_linea['estado_linea'] == 'C':
                        datos_linea['estado_linea'] = 'C1' # Pdte: Carnet sin receta 
                    else:
                        datos_linea['estado_linea'] = 'A1'

                # Dispone receta digital
                if datos_linea['valida_receta'] == 'M2':
                    if datos_linea['estado_linea'] == 'C':
                        datos_linea['estado_linea'] = 'C2' # Pdte: Carnet indica Receta Electronica
                    else:
                        datos_linea['estado_linea'] = 'A2'
                
                # Dispone receta en papel
                if datos_linea['valida_receta'] == 'M3':
                    if datos_linea['estado_linea'] == 'C':
                        datos_linea['estado_linea'] = 'C3' # Pdte: Carnet indica Receta Papel
                    else:
                        datos_linea['estado_linea'] = 'A3'

            # Eliminamos el atributo de la linea para evitar fallo serializer
            datos_linea.pop('valida_receta')

        serializer = WebPedidosLinSerializer(
            data=datos_linea, context={'request': portal})

        if serializer.is_valid():
            if WebPedidosLin.objects.filter(id_pedido=pedido.id_pedido, id_articulo=articulo.id, tipo_linea=datos_linea['tipo_linea']).exists() == True:

                # obtenemos la linea insertada anteriormente
                linea_anterior = WebPedidosLin.objects.get(
                    id_pedido=pedido.id_pedido, id_articulo=articulo.id, tipo_linea=datos_linea['tipo_linea'])

                # borramos todas las lineas que tengan como origen la linea antigua(regalos)
                WebPedidosLin.objects.filter(
                    id_pedido=pedido.id_pedido, numero_linea_origen=linea_anterior.numero_linea).delete()

                if sumar_cantidad_anterior:
                    datos_linea['cantidad_pedida'] = Decimal(datos_linea['cantidad_pedida']) + \
                        linea_anterior.cantidad_pedida
                    serializer = WebPedidosLinSerializer(data=datos_linea)
                    if not serializer.is_valid():
                        logger.error("Error validando linea: " +
                                     str(datos_linea))
                        raise Exception('Error insertando linea')

                linea_anterior.delete()

            serializer.save()

            # Calculamos Regalos y residuos si la linea no es de presupuesto
            if datos_linea['tipo_linea'] != 'O':
                try:
                    # OBTENCION Y GUARDADO DE REGALOS ASOCIADOS A LA LINEA
                    añadeRegalos(portal, usuario,
                                 pedido, datos_linea)
                except Exception as e:
                    logger.error(
                        "La peticion de regalos ha fallado, excepcion: " + str(e))
                    raise Exception(
                        'Se ha producido un error durante la petición de regalos')

                if articulo.residuo is not None:
                    try:
                        inserta_linea_residuo(
                            portal, usuario, pedido, numero_linea, datos_linea)
                    except Exception as e:
                        logger.error(
                            "La inserción de residuo ha fallado, excepcion: " + str(e))
                        raise Exception(
                            'La inserción de residuo ha fallado')
        else:
            logger.error(
                "Error validando linea: " + str(datos_linea))
            raise Exception('Error insertando linea')
    else:
        logger.error(
            "El artículo indicado no existe: " + datos_linea['articulo'])
        raise Exception(
            'El artículo indicado no existe: ' + datos_linea['articulo'])


def inserta_linea_residuo(portal, usuario, pedido, numero_linea_padre, linea_insertada):

    endpoint = '/V1/B2B/ORDERS/RESIDUOS'

    data = {
        'codigo_empresa': portal['codigo_empresa'],
        'codigo_portal': portal['codigo_portal'],
        'usuario_web': usuario.usuario_web,
        'codigo_articulo': linea_insertada['articulo'],
        'cantidad_pedida': linea_insertada['cantidad_pedida'],
        'presentacion': linea_insertada['presentacion_pedido']
    }

    body = json.dumps(
        data,
        sort_keys=False,
        indent=None,
        use_decimal=True,
        default=fecha_encoder
    )

    try:
        respuesta = comunica_lisa(
            endpoint=endpoint, body=body, cache_seconds=0, portal=portal, usuario=usuario)
    except Exception as e:
        logger.error("La peticion a lisa: " + endpoint +
                     " ha fallado, excepcion: " + str(e))
        raise Exception(
            'Se ha producido un error durante la petición de residuos')

    if respuesta is not None and 'codigo_articulo' in respuesta and respuesta['codigo_articulo'] is not None:
        if Articulo.objects.filter(codigo_empresa=portal['codigo_empresa'], codigo_articulo=respuesta['codigo_articulo']).exists():

            articulo = Articulo.objects.get(
                codigo_articulo=respuesta['codigo_articulo'], codigo_empresa=portal['codigo_empresa'])

            linea_residuo = dict()

            linea_residuo['articulo'] = respuesta['codigo_articulo']
            linea_residuo['descripcion'] = articulo.descrip_comercial
            linea_residuo['precio_venta'] = float(
                respuesta['precio'])  # se sobrescribirá
            linea_residuo['observaciones'] = ""
            linea_residuo['estado_linea'] = "B"
            linea_residuo['cantidad_pedida'] = respuesta['cantidad']
            linea_residuo['presentacion_pedido'] = respuesta['presentacion']
            linea_residuo['tipo_linea'] = linea_insertada['tipo_linea']
            linea_residuo['id_pedido'] = pedido.id_pedido
            linea_residuo['id_articulo'] = articulo.id
            linea_residuo['numero_linea_origen'] = numero_linea_padre
            # T = TRASH, articulos que son residuos
            linea_residuo['tipo_articulo'] = 'T'
            linea_residuo['precio_manual'] = 'S'

            insertarLineaPedido(portal, usuario, pedido, linea_residuo)

        else:
            raise Exception("El artículo no existe")
    else:
        logger.error("La respuesta está mal formada: " + str(respuesta))
        raise Exception("Respuesta mal formada")


def recalcularPedido(portal, usuario, pedido):

    pedido_recalculado = WebPedidos.objects.get(id_pedido=pedido.id_pedido)

    if pedido_recalculado.almacen != usuario.codigo_almacen:
        pedido_recalculado.almacen = usuario.codigo_almacen
        pedido_recalculado.save()

    if WebPedidosLin.objects.filter(id_pedido=pedido.id_pedido).exists():

        # borramos los articulos de residuos que serán recalculados
        if WebPedidosLin.objects.filter(
                id_pedido=pedido.id_pedido, tipo_articulo='T').exists():
            WebPedidosLin.objects.filter(
                id_pedido=pedido.id_pedido, tipo_articulo='T').delete()

        # eliminamos los regalos que serán recalculados
        if WebPedidosLin.objects.filter(
                id_pedido=pedido.id_pedido, tipo_linea='R').exists():
            WebPedidosLin.objects.filter(
                id_pedido=pedido.id_pedido, tipo_linea='R').delete()

        # borramos los articulos de fletes que serán recalculados
        if WebPedidosLin.objects.filter(
                id_pedido=pedido.id_pedido, tipo_articulo='F').exists():
            WebPedidosLin.objects.filter(
                id_pedido=pedido.id_pedido, tipo_articulo='F').delete()

        lineas = WebPedidosLin.objects.filter(
            id_pedido=pedido.id_pedido)

        for linea in lineas:
            # Comprobamos que no existan lineas duplicadas
            if WebPedidosLin.objects.filter(id_pedido=pedido.id_pedido, articulo=linea.articulo, tipo_linea=linea.tipo_linea).count() > 1:
                WebPedidosLin.objects.filter(
                    id_pedido=pedido.id_pedido, articulo=linea.articulo, numero_linea=linea.numero_linea).delete()
                linea.delete()

            if Articulo.objects.filter(codigo_empresa=portal['codigo_empresa'], codigo_articulo=linea.articulo).exists():

                articulo = Articulo.objects.get(
                    codigo_empresa=portal['codigo_empresa'], codigo_articulo=linea.articulo)

                if usuario.presentacion_defecto is not None:
                    presentacion = usuario.presentacion_defecto
                else:
                    if portal['presentacion_defecto'] is not None:
                        presentacion = portal['presentacion_defecto']
                    else:
                        presentacion = articulo.presentacion_web

                datos_linea = {
                    'articulo': linea.articulo,
                    'descripcion': articulo.descrip_comercial,
                    'precio_venta': linea.precio_venta,
                    'estado_linea': linea.estado_linea,
                    'cantidad_pedida': linea.cantidad_pedida,
                    'presentacion_pedido': presentacion,
                    'tipo_linea': linea.tipo_linea,
                    'sub_pres': linea.sub_pres,
                    'sub_pres_cant': linea.sub_pres_cant,
                    'sub_pres_fc': linea.sub_pres_fc,
                    'pres_fc': linea.pres_fc,
                    'presentacion_escogida': linea.presentacion_escogida,
                    'observaciones': linea.observaciones
                }

                try:
                    insertarLineaPedido(
                        portal, usuario, pedido_recalculado, datos_linea)
                except Exception as e:
                    logger.error(
                        "Error insertando linea: " + str(e))
                    if WebPedidosLin.objects.filter(id_pedido=pedido_recalculado.id_pedido, numero_linea=linea.numero_linea).exists():
                        WebPedidosLin.objects.filter(
                            id_pedido=pedido_recalculado.id_pedido, numero_linea=linea.numero_linea).delete()
            else:
                # el articulo ya no existe
                linea.delete()

        if lineas.count() > 0:
            try:
                calculaPortes(portal, usuario, pedido_recalculado)
            except Exception as e:
                logger.error(
                    "Error calculando portes: " + str(e))

    return pedido_recalculado


def ultimoPedido(data):

    pedido_recuperado = None

    if data.query_params.get('id_pedido_seleccionado') is not None and data.query_params.get('id_pedido_seleccionado') != "":
        pedido_recuperado = WebPedidos.objects.get(
            id_pedido=data.query_params.get('id_pedido_seleccionado'))

        if pedido_recuperado.almacen != data.user.codigo_almacen:
            pedido_recuperado.almacen = data.user.codigo_almacen
            pedido_recuperado.save()
    else:
        if data.session['portal']['codigo_cliente'] is None or data.session['portal']['codigo_cliente'] == "":
            # portal privado
            existe_pedido_abierto = WebPedidos.objects.filter(
                codigo_empresa=data.user.codigo_empresa, codigo_cliente=data.user.codigo_cliente, estado_pedido__in=['A', 'P']).exists()

            if not existe_pedido_abierto:

                pedido = WebPedidos(
                    codigo_empresa=data.user.codigo_empresa, codigo_cliente=data.user.codigo_cliente, estado_pedido='A', origen_pedido='WEB',
                    organizacion_comercial=data.user.organizacion_comercial, almacen=data.user.codigo_almacen, tipo_pedido=data.user.tipo_pedido)

                pedido.save()

            else:
                pedido = WebPedidos.objects.filter(codigo_empresa=data.user.codigo_empresa,
                                                   codigo_cliente=data.user.codigo_cliente,
                                                   estado_pedido__in=['A', 'P']).order_by('-id_pedido')[:1].get()

                if pedido.almacen != data.user.codigo_almacen:
                    pedido.almacen = data.user.codigo_almacen
                    pedido.save()

            pedido_recuperado = pedido
        else:
            # portal publico
            hash_usuario_anonimo = data.query_params.get('inv')
            if data.user.codigo_cliente == data.session['portal']['codigo_cliente']:
                # usuario anonimo
                existe_pedido_abierto = WebPedidos.objects.filter(
                    codigo_empresa=data.user.codigo_empresa, codigo_cliente=data.user.codigo_cliente, estado_pedido='A', hash_usuario=hash_usuario_anonimo).exists()

                if not existe_pedido_abierto:

                    pedido = WebPedidos(
                        codigo_empresa=data.user.codigo_empresa, codigo_cliente=data.user.codigo_cliente, estado_pedido='A', origen_pedido='WEB',
                        organizacion_comercial=data.user.organizacion_comercial, almacen=data.user.codigo_almacen, tipo_pedido=data.user.tipo_pedido,
                        hash_usuario=hash_usuario_anonimo)

                    pedido.save()

                else:
                    pedido = WebPedidos.objects.filter(codigo_empresa=data.user.codigo_empresa,
                                                       codigo_cliente=data.user.codigo_cliente,
                                                       estado_pedido='A', hash_usuario=hash_usuario_anonimo).order_by('-id_pedido')[:1].get()

                    if pedido.almacen != data.user.codigo_almacen:
                        pedido.almacen = data.user.codigo_almacen
                        pedido.save()

                pedido_recuperado = pedido
            else:
                # usuario real logueado

                existe_pedido_abierto_propio_pendiente = WebPedidos.objects.filter(
                    codigo_empresa=data.user.codigo_empresa, codigo_cliente=data.user.codigo_cliente, estado_pedido='P').exists()

                if existe_pedido_abierto_propio_pendiente:  # si el usuario tiene un pedido pendiente de pago, da igual lo que haya hecho, se devuelve ese pedido para que lo pague
                    pedido_recuperado = WebPedidos.objects.get(
                        codigo_empresa=data.user.codigo_empresa, codigo_cliente=data.user.codigo_cliente, estado_pedido='P')

                    if pedido_recuperado.almacen != data.user.codigo_almacen:
                        pedido_recuperado.almacen = data.user.codigo_almacen
                        pedido_recuperado.save()
                else:

                    existe_pedido_abierto_propio = WebPedidos.objects.filter(
                        codigo_empresa=data.user.codigo_empresa, codigo_cliente=data.user.codigo_cliente, estado_pedido='A').exists()

                    existe_pedido_abierto_anonimo = WebPedidos.objects.filter(
                        codigo_empresa=data.user.codigo_empresa, codigo_cliente=data.session['portal']['codigo_cliente'], estado_pedido='A', hash_usuario=hash_usuario_anonimo).exists()

                    if existe_pedido_abierto_anonimo:

                        pedido_anonimo = WebPedidos.objects.filter(
                            codigo_empresa=data.user.codigo_empresa, codigo_cliente=data.session['portal']['codigo_cliente'], estado_pedido='A', hash_usuario=hash_usuario_anonimo).order_by('-id_pedido')[:1].get()

                        # he metido lineas al pedido sin haber logueado,mantenemos este
                        if WebPedidosLin.objects.filter(id_pedido=pedido_anonimo.id_pedido).exists():

                            if existe_pedido_abierto_propio:  # borramos los pedidos abiertos del usuario
                                pedido_propio = WebPedidos.objects.filter(
                                    codigo_empresa=data.user.codigo_empresa, codigo_cliente=data.user.codigo_cliente, estado_pedido='A').order_by('-id_pedido')[:1].get()

                                pedido_propio.delete()

                            # pedido_anonimo.update(
                            #     codigo_cliente=data.user.codigo_cliente, hash_usuario=None)  # asignamos el pedido anonimo al cliente,eliminando el hash
                            pedido_anonimo.codigo_cliente = data.user.codigo_cliente
                            pedido_anonimo.almacen = data.user.codigo_almacen
                            pedido_anonimo.organizacion_comercial = data.user.organizacion_comercial
                            pedido_anonimo.tipo_pedido = data.user.tipo_pedido
                            pedido_anonimo.hash_usuario = None
                            if pedido_anonimo.domicilio_envio is not None:
                                pedido_anonimo.domicilio_envio = 1
                            pedido_anonimo.save()
                            pedido_recuperado = pedido_anonimo

                        else:  # el pedido anonimo no tiene lineas, no hace falta recuperarlo, buscamos si tiene uno propio
                            if existe_pedido_abierto_propio:  # si tiene pedido propio abierto, lo devuelve
                                pedido_propio = WebPedidos.objects.filter(
                                    codigo_empresa=data.user.codigo_empresa, codigo_cliente=data.user.codigo_cliente, estado_pedido='A').order_by('-id_pedido')[:1].get()

                                pedido_anonimo.delete()

                                pedido_recuperado = pedido_propio

                            else:  # actualizamos el pedido anonimo y lo devolvemos
                                # pedido_anonimo.update(
                                #     codigo_cliente=data.user.codigo_cliente, hash_usuario=None)  # asignamos el pedido anonimo al cliente,eliminando el hash

                                pedido_anonimo.codigo_cliente = data.user.codigo_cliente
                                pedido_anonimo.almacen = data.user.codigo_almacen
                                pedido_anonimo.organizacion_comercial = data.user.organizacion_comercial
                                pedido_anonimo.tipo_pedido = data.user.tipo_pedido
                                pedido_anonimo.hash_usuario = None
                                if pedido_anonimo.domicilio_envio is not None:
                                    pedido_anonimo.domicilio_envio = 1

                                pedido_anonimo.save()
                                pedido_recuperado = pedido_anonimo
                    elif existe_pedido_abierto_propio:
                        pedido_propio = WebPedidos.objects.filter(
                            codigo_empresa=data.user.codigo_empresa, codigo_cliente=data.user.codigo_cliente, estado_pedido='A').order_by('-id_pedido')[:1].get()

                        if pedido_propio.almacen != data.user.codigo_almacen:
                            pedido_propio.almacen = data.user.codigo_almacen
                            pedido_propio.save()

                        pedido_recuperado = pedido_propio

                    else:

                        pedido = WebPedidos(
                            codigo_empresa=data.user.codigo_empresa, codigo_cliente=data.user.codigo_cliente, estado_pedido='A', origen_pedido='WEB',
                            organizacion_comercial=data.user.organizacion_comercial, almacen=data.user.codigo_almacen, tipo_pedido=data.user.tipo_pedido)

                        pedido.save()

                        pedido_recuperado = pedido

    if data.query_params.get('recalcular') is not None and data.query_params.get('recalcular') == 'S':
        return recalcularPedidoGrupos(data.session['portal'], data.user, pedido_recuperado)
    else:
        return pedido_recuperado


def siguienteLinea(id_pedido):
    lineas = WebPedidosLin.objects.filter(id_pedido=id_pedido)
    num_linea = lineas.aggregate(Max('numero_linea'))
    if num_linea['numero_linea__max'] is None:
        return 1
    return (num_linea['numero_linea__max'] + 1)


def añadeRegalos(portal, usuario, pedido, linea):
    # llamar a lisa obtener regalos y por cada uno meterlo como linea
    endpoint = '/V1/B2B/ORDERS/OFFERS'

    data = {
        'codigo_empresa': portal['codigo_empresa'],
        'codigo_portal': portal['codigo_portal'],
        'usuario_web': usuario.usuario_web,
        'articulo': linea['articulo'],
        'cantidad_pedida': linea['cantidad_pedida']
    }

    body = json.dumps(
        data,
        sort_keys=False,
        indent=None,
        use_decimal=True,
        default=fecha_encoder
    )

    try:
        respuesta = comunica_lisa(
            endpoint=endpoint, body=body, cache_seconds=1800, portal=portal, usuario=usuario)
    except Exception as e:
        logger.error("La peticion a lisa: " + endpoint +
                     " ha fallado, excepcion: " + str(e))
        raise Exception(
            'Se ha producido un error durante la petición de regalos')

    if respuesta['REGALOS'] is not None:

        if 'REGALO' in respuesta['REGALOS']:
            regalo = respuesta['REGALOS']['REGALO']
            respuesta['REGALOS'] = list()
            respuesta['REGALOS'].append(regalo)

        if isinstance(respuesta['REGALOS'], list) and len(respuesta['REGALOS']) > 0:

            for regalo in respuesta['REGALOS']:

                articulo = Articulo.objects.get(
                    codigo_empresa=portal['codigo_empresa'], codigo_articulo=regalo['ARTICULO'])

                linea_regalo = dict()
                linea_regalo['articulo'] = regalo['ARTICULO']
                linea_regalo['descripcion'] = articulo.descrip_comercial
                linea_regalo['precio_venta'] = float(
                    0.0)  # se sobrescribirá
                linea_regalo['observaciones'] = ""
                linea_regalo['estado_linea'] = "B"
                linea_regalo['cantidad_pedida'] = regalo['CANTIDAD']
                linea_regalo['presentacion_pedido'] = regalo['PRESENTACION'] if "REGALO" in regalo and regalo[
                    'PRESENTACION'] is not None else articulo.presentacion_web
                linea_regalo['tipo_linea'] = 'R'
                linea_regalo['id_pedido'] = pedido.id_pedido
                linea_regalo['id_articulo'] = articulo.id
                linea_regalo['numero_linea_origen'] = linea['numero_linea']
                # T = TRASH, articulos que son residuos
                linea_regalo['tipo_articulo'] = 'R'
                linea_regalo['precio_manual'] = 'S'

                insertarLineaPedido(portal, usuario, pedido, linea_regalo)


def calculaPortes(portal, usuario, pedido_activo):
    endpoint = '/V1/B2B/ORDERS/CALCULAPORTES'

    pedido = WebPedidos.objects.get(id_pedido=pedido_activo.id_pedido)

    if WebPedidosLin.objects.filter(
            id_pedido=pedido.id_pedido, tipo_articulo='F').exists():

        WebPedidosLin.objects.filter(
            id_pedido=pedido.id_pedido, tipo_articulo='F').delete()

    pedido_serializado = procesa_pedido(
        portal['codigo_portal'], usuario.usuario_web, pedido)  # , request.data['domicilio'], request.data['observaciones'], request.data['forma_envio'])  # (pedido_set[0])

    lineas_set = WebPedidosLin.objects.filter(
        id_pedido=pedido.id_pedido, tipo_linea='P')

    lineas = []
    for linea in lineas_set:
        lineas.append(procesa_linea(linea))

    if len(lineas) > 0:
        pedido_serializado.update({'lineas': lineas})

        body = json.dumps(
            pedido_serializado,
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
            raise Exception(
                "Se ha producido un error, por favor, inténtelo más tarde")

        if 'tipo_portes' in respuesta:
            tipo_portes = respuesta['tipo_portes']

            if tipo_portes == 'ARTICULO':
                articulo_portes = respuesta['portes']['articulo']
                # presentacion_articulo_portes = respuesta['portes']['presentacion']
                importe_portes = respuesta['portes']['importe_portes']

                articulo = Articulo.objects.get(
                    codigo_empresa=portal['codigo_empresa'], codigo_articulo=articulo_portes)

                numero_linea_flete = siguienteLinea(pedido.id_pedido)

                linea_flete = {
                    'articulo': articulo_portes,
                    'descripcion': articulo.descrip_comercial,
                    'precio_venta': Decimal(importe_portes),
                    'observaciones': "",
                    'estado_linea': "B",
                    'cantidad_pedida': Decimal(1),
                    'presentacion_pedido': articulo.presentacion_web,
                    'tipo_linea': portal['tipo_linea_pedidos'],
                    'id_pedido': pedido.id_pedido,
                    'numero_linea': Decimal(numero_linea_flete),
                    'id_articulo': articulo.id,
                    'numero_linea_origen': None,
                    'tipo_articulo': 'F',
                    'precio_manual': 'S'
                }
                serializer = WebPedidosLinSerializer(data=linea_flete)

                if serializer.is_valid(raise_exception=True):
                    serializer.save()
            elif tipo_portes == 'SINPORTES':
                None
            else:
                logger.error("Tipo de portes no reconocido")
                raise Exception("Tipo de portes no reconocido")
        else:
            logger.error("La respuesta de lisa: " + endpoint +
                         " no cumple el formato")
            raise Exception("La respuesta de lisa: " + endpoint +
                            " no cumple el formato")


def comprobarRiesgo(portal, usuario, cliente, centro_contable):
    endpoint = '/V1/B2B/USER/RISK'

    body = {'empresa': usuario.codigo_empresa,
            'codigo_portal': portal['codigo_portal'],
            'cliente': cliente,
            'usuario_web': usuario.usuario_web,
            'centro_contable': centro_contable
            }

    try:
        respuesta_lisa = comunica_lisa(
            endpoint=endpoint, body=body, cache_seconds=0, portal=portal, usuario=usuario)

        if respuesta_lisa['existe_riesgo'] is not None:
            if not isinstance(respuesta_lisa['existe_riesgo'], list):
                existe_riesgo = respuesta_lisa['existe_riesgo']
                return existe_riesgo

        return 'S'
    except Exception as e:
        logger.error("La peticion a lisa: " + endpoint +
                     " ha fallado, excepcion: " + str(e))
        raise Exception("La petición de riesgo ha fallado")


def getDivisaISO(codigo):

    if Divisas.objects.filter(codigo=codigo).exists():
        divisa = Divisas.objects.get(codigo=codigo)

    if divisa is not None and divisa.cod_iso4217a is not None:
        return divisa.cod_iso4217a
    else:
        logger.error("No existe la divisa con codigo: " + codigo)
        raise Exception("La conversión de divisa ha fallado")


def recalcularPedidoGrupos(portal, usuario, pedido):

    pedido_recalculado = WebPedidos.objects.get(id_pedido=pedido.id_pedido)

    # Comprobamos que el almacen del pedido coincide con el del usuario
    if pedido_recalculado.almacen != usuario.codigo_almacen:
        pedido_recalculado.almacen = usuario.codigo_almacen
        pedido_recalculado.save()

    if WebPedidosLin.objects.filter(id_pedido=pedido.id_pedido).exists():

        # Borramos los articulos de residuos que serán recalculados
        if WebPedidosLin.objects.filter(
                id_pedido=pedido.id_pedido, tipo_articulo='T').exists():
            WebPedidosLin.objects.filter(
                id_pedido=pedido.id_pedido, tipo_articulo='T').delete()

        # Eliminamos los regalos que serán recalculados
        if WebPedidosLin.objects.filter(
                id_pedido=pedido.id_pedido, tipo_linea='R').exists():
            WebPedidosLin.objects.filter(
                id_pedido=pedido.id_pedido, tipo_linea='R').delete()

        # Borramos los articulos de fletes que serán recalculados
        if WebPedidosLin.objects.filter(
                id_pedido=pedido.id_pedido, tipo_articulo='F').exists():
            WebPedidosLin.objects.filter(
                id_pedido=pedido.id_pedido, tipo_articulo='F').delete()

        lineas = WebPedidosLin.objects.filter(
            id_pedido=pedido.id_pedido)

        # Insertamos las lineas del pedido
        try:
            insertarLineasPedido(
                portal, usuario, pedido_recalculado, lineas, False)
        except Exception as e:
            logger.error(
                "Error insertando lineas: " + str(e))

        # Calculamos portes si existen lineas
        if lineas.count() > 0:
            try:
                calculaPortes(portal, usuario, pedido_recalculado)
            except Exception as e:
                logger.error(
                    "Error calculando portes: " + str(e))

    return pedido_recalculado


def insertarLineasPedido(portal, usuario, pedido, lineas, sumar_cantidad_anterior=False):
    articulos_stock = []
    articulos_precios = []
    datos_lineas = []
    numero_linea = 0

    ahora = datetime.date.today()

    for linea in lineas:

        # Comprobamos si existe una linea duplicada (Mismo, articulo y tipo de linea)
        if WebPedidosLin.objects.filter(id_pedido=pedido.id_pedido, articulo=linea.articulo, tipo_linea=linea.tipo_linea).count() > 1:
            linea.delete()
            # Si se borra la linea se salta el resto de codigo
            continue

        # Comprobamos si el articulo existe en la BD
        if Articulo.objects.filter(codigo_empresa=portal['codigo_empresa'], codigo_articulo=linea.articulo).exists():

            articulo = Articulo.objects.get(
                codigo_empresa=portal['codigo_empresa'], codigo_articulo=linea.articulo)

            # Comprobamos si el articulo está activo
            if hasattr(articulo, 'codigo_situacion') and articulo.codigo_situacion is not None and articulo.codigo_situacion != 'A':
                logger.error(
                    'El articulo: ' + articulo.codigo_articulo + ' no está activo')
                raise Exception(
                    'El articulo: ' + articulo.codigo_articulo + ' no está activo')

            # Comprobamos que el articulo no haya expirado
            if not Articulo.objects.filter(Q(fecha_baja__isnull=True) | Q(fecha_baja__gte=ahora)).filter(codigo_empresa=portal['codigo_empresa'],
                                                                                                         codigo_articulo=articulo.codigo_articulo).exists():
                logger.error(
                    'El articulo: ' + articulo.codigo_articulo + ' ha expirado, fecha_baja superada')
                raise Exception(
                    'El articulo: ' + articulo.codigo_articulo + ' ha expirado, no se encuentra activo')

            # Comprobamos que el articulo esté disponible
            if portal['activar_articulos_provincia'] == 'S':

                if pedido.domicilio_envio is not None:

                    domicilio_envio = DomiciliosEnvio.objects.get(empresa=portal['codigo_empresa'], codigo_cliente=usuario.codigo_cliente,
                                                                  numero_direccion=pedido.domicilio_envio)
                    codigo_estado = domicilio_envio.estado
                    codigo_provincia = domicilio_envio.provincia

                    if not EcomArticulosProvincias.objects.filter(Q(fecha_baja__isnull=True) | Q(fecha_baja__gte=ahora)).filter(empresa=portal['codigo_empresa'],
                                                                                                                                portal=portal[
                                                                                                                                    'codigo_portal'],
                                                                                                                                estado=codigo_estado,
                                                                                                                                provincia=codigo_provincia,
                                                                                                                                articulo=articulo.codigo_articulo).exists():

                        logger.error(
                            'El articulo: ' + articulo.codigo_articulo + ' no está disponible en la dirección solicitada')
                        raise Exception(
                            'El articulo: ' + articulo.codigo_articulo + ' no está disponible en la dirección solicitada')

            # Comprobamos que la linea tiene cantidad y es mayor que 0
            if not hasattr(linea, 'cantidad_pedida') or (hasattr(linea, 'cantidad_pedida') and (linea.cantidad_pedida is None or linea.cantidad_pedida <= 0)):
                raise Exception(
                    'La cantidad pedida no puede ser menor o igual a 0')

            # Comprobamos que la linea cumple las condiciones del articulo
            if articulo.cantidad_minima is not None:
                if float(linea.cantidad_pedida) < articulo.cantidad_minima:
                    raise Exception(
                        'La cantidad pedida: ' + str(linea.cantidad_pedida) + ', no llega a la cantidad mínima: ' + str(articulo.cantidad_minima))

            if articulo.cantidad_maxima is not None:
                if float(linea.cantidad_pedida) > articulo.cantidad_maxima:
                    raise Exception(
                        'La cantidad pedida: ' + str(linea.cantidad_pedida) + ', excede la cantidad máxima: ' + str(articulo.cantidad_maxima))

            if articulo.multiplo is not None:
                if float(linea.cantidad_pedida) % articulo.multiplo != 0:
                    raise Exception(
                        'La cantidad pedida: ' + str(linea.cantidad_pedida) + ', debe ser un múltiplo de: ' + str(articulo.multiplo))

            # Creamos el objeto con los datos basicos
            datos_linea = {
                'id_pedido': pedido.id_pedido,
                'id_articulo': articulo.id,
                'articulo': linea.articulo,
                'descripcion': articulo.descrip_comercial,
                'precio_venta': linea.precio_venta,
                'estado_linea': linea.estado_linea,
                'cantidad_pedida': linea.cantidad_pedida,
                'presentacion_pedido': articulo.presentacion_web,
                'observaciones': linea.observaciones,
            }
            # Añadimos otros atributos
            datos_linea['tipo_articulo'] = linea.tipo_articulo if hasattr(
                linea, 'tipo_articulo') and linea.tipo_articulo is not None and linea.tipo_articulo != "" else None
            datos_linea['numero_linea_origen'] = linea.numero_linea_origen if hasattr(
                linea, 'numero_linea_origen') and linea.numero_linea_origen is not None and linea.numero_linea_origen != "" else None
            datos_linea['tipo_linea'] = linea.tipo_linea if hasattr(
                linea, 'tipo_linea') and linea.tipo_linea is not None and linea.tipo_linea != "" else portal['tipo_linea_pedidos']
            datos_linea['sub_pres'] = linea.sub_pres if hasattr(
                linea, 'sub_pres') and linea.sub_pres is not None and linea.sub_pres != "" else None
            datos_linea['sub_pres_cant'] = linea.sub_pres_cant if hasattr(
                linea, 'sub_pres_cant') and linea.sub_pres_cant is not None and linea.sub_pres_cant != "" else None
            datos_linea['sub_pres_fc'] = linea.sub_pres_fc if hasattr(
                linea, 'sub_pres_fc') and linea.sub_pres_fc is not linea.sub_pres_fc != "" else None
            datos_linea['pres_fc'] = linea.pres_fc if hasattr(
                linea, 'pres_fc') and linea.pres_fc is not None and linea.pres_fc != "" else None
            datos_linea['presentacion_escogida'] = linea.presentacion_escogida if hasattr(
                linea, 'presentacion_escogida') and linea.presentacion_escogida is not None and linea.presentacion_escogida != "" else None

            # Comprobamos si se necesita calcular el stock de la linea
            if portal['controlar_stock'] == 'S' and datos_linea['tipo_linea'] == 'P' and articulo.controlar_stock != 'N' and ('tipo_articulo' not in datos_linea or datos_linea['tipo_articulo'] not in ['T', 'F']):
                # Seteamos variables a usar
                presentacion = articulo.presentacion_web
                tipo_situacion = ""

                if pedido.almacen is not None:
                    codigo_almacen = pedido.almacen
                else:
                    codigo_almacen = usuario.codigo_almacen if usuario.codigo_almacen is not None else portal[
                        'codigo_almacen']

                # Creamos objeto_stock y lo añadimos a array_stock
                articulo_stock = {'codigo_articulo': datos_linea['articulo'],
                                  'presentacion': presentacion,
                                  'codigo_almacen': codigo_almacen,
                                  'situacion': tipo_situacion}
                articulos_stock.append(articulo_stock)

            # Creamos objeto_precio y lo añadimos a array_precio
            articulo_precio = {'codigo_articulo': datos_linea['articulo'],
                               'cantidad': datos_linea['cantidad_pedida']}
            articulos_precios.append(articulo_precio)

            # Añadimos los datos de la linea a array de lineas
            datos_lineas.append(datos_linea)

        else:
            logger.error(
                "El artículo indicado no existe: " + datos_linea['articulo'])
            raise Exception(
                'El artículo indicado no existe: ' + datos_linea['articulo'])

    # Calculamos el stock
    if portal['controlar_stock'] == 'S':

        if (len(articulos_stock) > 0):
            try:
                stocks_obtenidos = obtenerStocks(
                    portal, usuario, articulos_stock)
            except Exception as e:
                logger.error(
                    "La peticion de stocks ha fallado, excepcion: " + str(e))
                raise Exception(
                    'Se ha producido un error durante la comprobación de stocks')
        else:
            logger.error(
                "No hay articulos en el array de articulos_stock, no se pueden obtener los mismos.")

    # Calculamos los precios
    if (len(articulos_precios) > 0):
        precios_calculados = calcula_precios_articulos(
            portal, usuario, pedido.domicilio_envio, articulos_precios)
    else:
        logger.error(
            "No hay articulos en el array de articulos_precios, no se pueden obtener los mismos.")

    # Recorremos las lineas regeneradas
    for datos_linea in datos_lineas:

        datos_linea['numero_linea'] = siguienteLinea(pedido.id_pedido)

        # Recuperamos el articulo de la linea
        if Articulo.objects.filter(codigo_empresa=portal['codigo_empresa'], codigo_articulo=datos_linea['articulo']).exists():

            articulo = Articulo.objects.get(
                codigo_empresa=portal['codigo_empresa'], codigo_articulo=datos_linea['articulo'])

            informacion_precio = []

            # Recuperamos el precio calculado correspondiente a la linea
            if precios_calculados is not None and len(precios_calculados) > 0:

                if precios_calculados['articulos'] is not None and len(precios_calculados['articulos']) > 0:
                    for precio in precios_calculados['articulos']:

                        if 'codigo_articulo' in precio and precio['codigo_articulo'] == datos_linea['articulo']:

                            informacion_precio = precio

            # Recuperamos el stock calculado correspondiente a la linea
            if portal['controlar_stock'] == 'S':
                if (len(articulos_stock) > 0):
                    if stocks_obtenidos is not None and len(stocks_obtenidos) > 0:
                        for stock in stocks_obtenidos:
                            if stock['codigo_articulo'] == datos_linea['articulo']:
                                stock_calculado = stock
                                if stock_calculado['stock'] != 'S' and (stock_calculado['stock'] == 0 or int(float(stock_calculado['stock'])) < int(datos_linea['cantidad_pedida'])):
                                    raise Exception("No hay stock disponible en estos momentos, disponible: " +
                                                    str(int(float(stock['stock']))))

            # Seteamos el resto de valores necesario para la linea
            datos_linea['precio_manual'] = datos_linea['precio_manual'] if 'precio_manual' in datos_linea and datos_linea['precio_manual'] is not None and datos_linea[
                'precio_manual'] != "" else informacion_precio['precio_manual'] if 'precio_manual' in informacion_precio else None
            if datos_linea['tipo_articulo'] != 'T' and datos_linea['tipo_articulo'] != 'R' and 'precio_neto' in informacion_precio and 'cantidad_precio' in informacion_precio:
                round(float(informacion_precio['precio_neto']) /
                      float(informacion_precio['cantidad_precio']), 4)

            datos_linea['clave_actuacion'] = informacion_precio['clave_actuacion'] if 'clave_actuacion' in informacion_precio else None

            if datos_linea['precio_venta'] == 0 and datos_linea['tipo_linea'] != "R" and (datos_linea['tipo_articulo'] is None or datos_linea['tipo_articulo'] != "F"):
                raise Exception('No se permiten líneas con precio 0')

            datos_linea['cantidad_pedida'] = float(
                str(datos_linea['cantidad_pedida']))

            serializer = WebPedidosLinSerializer(data=datos_linea)

            if serializer.is_valid():
                if WebPedidosLin.objects.filter(id_pedido=pedido.id_pedido, id_articulo=articulo.id, tipo_linea=datos_linea['tipo_linea']).exists() == True:

                    # Obtenemos la linea insertada anteriormente
                    linea_anterior = WebPedidosLin.objects.get(
                        id_pedido=pedido.id_pedido, id_articulo=articulo.id, tipo_linea=datos_linea['tipo_linea'])

                    # Borramos todas las lineas que tengan como origen la linea antigua(regalos)
                    WebPedidosLin.objects.filter(
                        id_pedido=pedido.id_pedido, numero_linea_origen=linea_anterior.numero_linea).delete()

                    if sumar_cantidad_anterior:
                        datos_linea['cantidad_pedida'] = Decimal(
                            datos_linea['cantidad_pedida'] + linea_anterior.cantidad_pedida)
                        serializer = WebPedidosLinSerializer(data=datos_linea)
                        if not serializer.is_valid():
                            logger.error("Error validando linea: " +
                                         str(datos_linea)+", error: "+str(serializer.errors))
                            raise Exception(
                                'Error insertando linea, error: '+str(serializer.errors))
                    else:
                        datos_linea['cantidad_pedida'] = float(
                            str(datos_linea['cantidad_pedida']))

                    linea_anterior.delete()

                serializer.save()

                # Si no es linea de presupuesto, calculamos regalos y residuos
                if datos_linea['tipo_linea'] != 'O':

                    try:
                        # OBTENCION Y GUARDADO DE REGALOS ASOCIADOS A LA LINEA
                        añadeRegalos(portal, usuario,
                                     pedido, datos_linea)
                    except Exception as e:
                        logger.error(
                            "La peticion de regalos ha fallado, excepcion: " + str(e))
                        raise Exception(
                            'Se ha producido un error durante la petición de regalos')

                    if articulo.residuo is not None:
                        try:
                            inserta_linea_residuo(
                                portal, usuario, pedido, datos_linea['numero_linea'], datos_linea)
                        except Exception as e:
                            logger.error(
                                "La inserción de residuo ha fallado, excepcion: " + str(e))
                            raise Exception(
                                'La inserción de residuo ha fallado')
            else:
                logger.error("Error validando linea: " +
                             str(datos_linea)+", error: "+str(serializer.errors))
                raise Exception('Error insertando linea')

        else:
            logger.error(
                "El artículo indicado no existe: " + datos_linea['articulo'])
            raise Exception(
                'El artículo indicado no existe: ' + datos_linea['articulo'])
