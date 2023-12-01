from array import array
from ast import For
from functools import reduce
from portales.lisa import comunica_lisa
from articulos.models import Familia, Filtro, ArticulosDescripcionWeb, EcomPalabrasClave, CodigoBarras, ArticulosEquivalentes, \
    Articulo, ArticulosFamilias, FiltroClaveEstadistica, ValoresClavesArt, ArticulosClavesEstadisticas, DetalleListaReferencias, \
    PesoPalabrasBusqueda
from usuarios.models import EcomUsuarioWeb
from articulos.serializers import FamiliaSerializer, FiltroSerializer, FiltroClaveEstadisticaSerializer, ValoresClavesArtSerializer
from django.db.models import OuterRef, Exists, Q
from usuarios.models import ClientesParametros
from portales.enconders import fecha_encoder
from portal.models import EcomFamiliasXTipoCliente
import simplejson as json
from django.conf import settings
import logging
from operator import and_

logger = logging.getLogger("rad_logger")


def obtener_filtros_aplicables_padres(codigo_empresa, estadistico, codigo_familia, inspeccionados):
    lista_filtros = []

    if Familia.objects.filter(
            codigo_empresa=codigo_empresa, numero_tabla=estadistico, codigo_familia=codigo_familia).exists():

        familia = Familia.objects.get(
            codigo_empresa=codigo_empresa, numero_tabla=estadistico, codigo_familia=codigo_familia)

        if familia.codigo_padre is not None and familia.codigo_padre not in inspeccionados:

            padre = Familia.objects.get(
                codigo_empresa=codigo_empresa, numero_tabla=estadistico, codigo_familia=familia.codigo_padre)

            inspeccionados.append(padre.codigo_familia)

            lista_filtros.append(padre.codigo_familia)

            if padre.codigo_padre is not None:
                lista_filtros.extend(obtener_filtros_aplicables_padres(
                    codigo_empresa, estadistico, padre.codigo_padre, inspeccionados))

    return lista_filtros


def obtener_filtros_aplicables(portal, articulos):
    filtros_aplicables = list()
    filtros_disponibles = Filtro.objects.filter(codigo_empresa=portal['codigo_empresa'],
                                                codigo_portal=portal['codigo_portal'])

    for filtro in filtros_disponibles:

        lista_familias_filtro = list()

        estadistico = filtro.estadistico

        campo = "codigo_estad"+str(estadistico)

        if estadistico == 1:
            familias_disp = list(articulos.values_list(
                "codigo_familia", flat=True))
        else:
            familias_disp = list(articulos.values_list(
                campo, flat=True))

        familias_disp = list(filter(None, familias_disp))

        familias_disp = list(set(familias_disp))

        if len(familias_disp) > 0:

            inspeccionados = list()

            for familia_disp in familias_disp:

                lista_familias_filtro.extend(obtener_filtros_aplicables_padres(
                    portal['codigo_empresa'], estadistico, familia_disp, inspeccionados))

            lista_familias_filtro.extend(familias_disp)

            filtroDict = FiltroSerializer(filtro).data
            filtroDict['familias'] = lista_familias_filtro
            filtros_aplicables.append(filtroDict)

    return filtros_aplicables

def obtener_filtros_claves_aplicables(portal, articulos):
    filtros_aplicables = list()
    filtros_disponibles = FiltroClaveEstadistica.objects.filter(codigo_empresa=portal['codigo_empresa'],
                                                                codigo_portal=portal['codigo_portal'])

    for filtro in filtros_disponibles:

        clave_estadistica = filtro.clave_estadistica

        lista_articulos = list(articulos.values_list(
            "codigo_articulo", flat=True))

        valores_claves_disponibles = ArticulosClavesEstadisticas.objects.filter(
            empresa=portal['codigo_empresa'], codigo_articulo__in=lista_articulos, clave=clave_estadistica).values_list(
                "valor_clave", flat=True)

        valores_claves_disponibles = list(
            filter(None, valores_claves_disponibles))

        valores_claves_disponibles = list(set(valores_claves_disponibles))

        if len(valores_claves_disponibles) > 0:
            filtroDict = FiltroClaveEstadisticaSerializer(filtro).data
            filtroDict['claves'] = valores_claves_disponibles
            filtros_aplicables.append(filtroDict)

    return filtros_aplicables

def generarMigas(estadistico, arbol_familias, familia_articulo):
    migas = list()
    for familia in arbol_familias:
        if familia['codigo_familia'] == familia_articulo:
            migas.append({'familia': familia['codigo_familia'],
                          'descripcion': familia['descripcion'],
                          'estadistico': estadistico})
            if familia['codigo_padre'] is not None:
                migas.extend(generarMigas(estadistico,
                                          arbol_familias, familia['codigo_padre']))
            break

    return migas

# Devuelve arbol "completo" de familias
def getArbolFamilias(portal, numeroTabla, familias, codigoFamilia, nivelInicio, nivelFin, nivelActual):
    
    if nivelActual is None:
        nivelActual = 0

    familias_filtradas = familiasHijas(
        portal, numeroTabla,familias, codigoFamilia, nivelInicio, nivelFin, nivelActual)

    return familias_filtradas

# Devuelve diccionario de familias
def familiasHijas(codigoEmpresa, numeroTabla, familias, codigoFamilia, nivelInicio, nivelFin, nivelActual):

    famHijas = None
    listaFamilias = []
    nivelActual = nivelActual + 1

    if familias is None:
        familias = Familia.objects.get_queryset()
    
    if codigoFamilia == "":
        famHijas = familias.filter(codigo_empresa=codigoEmpresa,
                                               numero_tabla=numeroTabla,
                                               codigo_padre=None).order_by("orden")
    else:
        famHijas = familias.filter(codigo_empresa=codigoEmpresa,
                                               numero_tabla=numeroTabla,
                                               codigo_padre=codigoFamilia).order_by("orden")
    
    # Si no se nos requiere un nivel en concreto
    if nivelInicio is None and nivelFin is None:
        for familia in famHijas:
            if familia.ultimo_nivel != 'S':
                for f in familiasHijas(codigoEmpresa, numeroTabla, familias, familia.codigo_familia,nivelInicio, nivelFin, nivelActual):
                    # Recuperamos datos de las hijas
                    familiaDiccionario = FamiliaSerializer(f).data
                    familiaDiccionario['nivel'] = nivelActual+1
                    listaFamilias.append(familiaDiccionario)
            # Guardamos datos del padre
            familiaDiccionario = FamiliaSerializer(familia).data
            familiaDiccionario['nivel'] = nivelActual
            listaFamilias.append(familiaDiccionario)

    else: # Para obtener filtros estadísticos para una o varias familias en concreto
        for familia in famHijas:
            if(nivelActual >= nivelInicio and nivelActual <= nivelFin):
                familiaDiccionario = FamiliaSerializer(familia).data
                familiaDiccionario['nivel'] = nivelActual
                listaFamilias.append(familiaDiccionario)

            if(nivelActual <= nivelFin):
                listaFamilias.extend(getArbolFamilias(
                        codigoEmpresa, numeroTabla, None, familia.codigo_familia, nivelInicio, nivelFin, nivelActual))

    return listaFamilias
# Devuelve lista de codigos de familias
def listaFamiliaHijas(codigoEmpresa, numeroTabla, codigoFamilia=""):

    famHijas = None
    lista_familias = []

    if codigoFamilia == "":
        famHijas = Familia.objects.filter(codigo_empresa=codigoEmpresa,
                                               numero_tabla=numeroTabla,
                                               codigo_padre=None).order_by("orden")
    else:
        famHijas = Familia.objects.filter(codigo_empresa=codigoEmpresa,
                                               numero_tabla=numeroTabla,
                                               codigo_padre=codigoFamilia).order_by("orden")
    for familia in famHijas:
        if familia.ultimo_nivel != 'S':
            for f in listaFamiliaHijas(codigoEmpresa, numeroTabla, familia.codigo_familia):
                lista_familias.append(f)

        lista_familias.append(familia.codigo_familia)

    return lista_familias

def clavesHijas(codigoEmpresa, clave, valor_clave=""):

    clavesHijas = None

    if valor_clave == "":
        clavesHijas = ValoresClavesArt.objects.filter(empresa=codigoEmpresa,
                                                      clave=clave,
                                                      valor_padre=None).order_by("orden")
    else:
        clavesHijas = ValoresClavesArt.objects.filter(empresa=codigoEmpresa,
                                                      clave=clave,
                                                      valor_padre=valor_clave).order_by("orden")

    return clavesHijas


def getClavesEstadisticas(codigo_empresa, clave_estadistica, valor_clave="", nivelInicio=0, nivelFin=5):
    listaClaves = []

    claves = clavesHijas(codigo_empresa, clave_estadistica, valor_clave)

    nivelInicio = nivelInicio + 1

    if(nivelInicio <= nivelFin):

        for clave in claves:
            claveDiccionario = ValoresClavesArtSerializer(clave).data
            claveDiccionario['nivel'] = nivelInicio
            listaClaves.append(claveDiccionario)
            listaClaves.extend(getClavesEstadisticas(
                codigo_empresa, clave_estadistica, clave.valor_clave, nivelInicio, nivelFin))

    return listaClaves


def calcula_precio_articulo(portal, usuario, domicilio_envio, codigo_articulo, cantidad_pedida):
    endpoint = '/V1/B2B/PRODUCTS/PRICE'

    org_comercial = usuario.organizacion_comercial if usuario.organizacion_comercial is not None else portal[
        'organizacion_comercial']
    codigo_cliente = usuario.codigo_cliente if usuario.codigo_cliente is not None else portal[
        'codigo_cliente']
    codigo_almacen = usuario.codigo_almacen if usuario.codigo_almacen is not None else portal[
        'codigo_almacen']

    body = {'codigo_empresa': usuario.codigo_empresa,  # '013',
            'codigo_portal': portal['codigo_portal'],
            'codigo_articulo': codigo_articulo,
            'cantidad_pedida': cantidad_pedida,
            'usuario_web': usuario.usuario_web,  # 'PT45672311',
            'org_comercial': org_comercial,  # '0',
            'cliente': codigo_cliente,  # '0000',
            'fecha': None,  # datetime.today().strftime('%Y-%m-%d'),
            'almacen': codigo_almacen,  # '01',
            'tipo_pedido': usuario.tipo_pedido,
            'domicilio_envio': domicilio_envio
            }

    try:
        respuesta_lisa = comunica_lisa(
            endpoint=endpoint, body=body, cache_seconds=1800, portal=portal, usuario=usuario)
    except ConnectionError as e:
        logger.error("La peticion a lisa: " + endpoint +
                     " ha fallado, excepcion: " + str(e))
        raise Exception("La peticion a lisa: " + endpoint +
                        " ha fallado, excepcion: " + str(e))
    except Exception as e:
        logger.error("La peticion a lisa: " + endpoint +
                     " ha fallado, excepcion: " + str(e))
        raise Exception("La peticion a lisa: " + endpoint +
                        " ha fallado, excepcion: " + str(e))

    return respuesta_lisa


def calcula_precios_articulos(portal, usuario, domicilio_envio, articulos_cantidades):
    endpoint = '/V1/B2B/PRODUCTS/PRICES'
    articulos_procesados = []

    org_comercial = usuario.organizacion_comercial if usuario.organizacion_comercial is not None else portal[
        'organizacion_comercial']
    codigo_cliente = usuario.codigo_cliente if usuario.codigo_cliente is not None else portal[
        'codigo_cliente']
    codigo_almacen = usuario.codigo_almacen if usuario.codigo_almacen is not None else portal[
        'codigo_almacen']

    for articulo in articulos_cantidades:
        articulo_procesado = {'codigo_empresa': usuario.codigo_empresa,  # '013',
                              'codigo_portal': portal['codigo_portal'],
                              'codigo_articulo': articulo['codigo_articulo'],
                              'cantidad_pedida': articulo['cantidad'],
                              'usuario_web': usuario.usuario_web,  # 'PT45672311',
                              'org_comercial': org_comercial,  # '0',
                              'cliente': codigo_cliente,  # '0000',
                              'fecha':  None,  # datetime.today().strftime('%Y-%m-%d'),
                              'almacen': codigo_almacen,  # '01',
                              'tipo_pedido': usuario.tipo_pedido,
                              'domicilio_envio': domicilio_envio
                              }
        articulos_procesados.append(articulo_procesado)

    body = json.dumps(
        articulos_procesados,
        sort_keys=False,
        indent=None,
        use_decimal=True,
        default=fecha_encoder
    )

    try:
        respuesta_lisa = comunica_lisa(
            endpoint=endpoint, body=body, cache_seconds=1800, portal=portal, usuario=usuario)

    except ConnectionError as e:
        logger.error("La conexion a lisa: " + endpoint +
                     " ha fallado, excepcion: " + str(e))
        raise Exception("La conexion a lisa: " + endpoint +
                        " ha fallado, excepcion: " + str(e))
    except Exception as e:
        logger.error("La peticion a lisa: " + endpoint +
                     " ha fallado, excepcion: " + str(e))
        raise Exception("La peticion a lisa: " + endpoint +
                        " ha fallado, excepcion: " + str(e))

    return respuesta_lisa


def obtenerStock(portal, usuario, codigo_articulo, presentacion, almacen, situacion):
    endpoint = '/V1/B2B/PRODUCTS/QTY'

    body = {'codigo_empresa': usuario.codigo_empresa,
            'codigo_portal': portal['codigo_portal'],
            'codigo_articulo': codigo_articulo,
            'usuario_web': usuario.usuario_web,
            'codigo_almacen': almacen,
            'presentacion': presentacion,
            'tipo_situacion': situacion
            }

    try:
        respuesta_lisa = comunica_lisa(
            endpoint=endpoint, body=body, cache_seconds=0, portal=portal, usuario=usuario)

        if 'stock' in respuesta_lisa['stocks'] and isinstance(respuesta_lisa['stocks']['stock'], dict):
            stock = respuesta_lisa['stocks']['stock']
            respuesta_lisa['stocks']['stock'] = list()
            respuesta_lisa['stocks']['stock'].append(stock)

    except Exception as e:
        logger.error("La peticion a lisa: " + endpoint +
                     " ha fallado, excepcion: " + str(e))
        raise Exception("La petición de stock ha fallado")
    return respuesta_lisa


def obtenerStocks(portal, usuario, articulos_stock):
    endpoint = '/V1/B2B/PRODUCTS/QTYS'
    articulos_procesados = []
    respuesta_procesada = []

    for articulo in articulos_stock:

        if Articulo.objects.filter(codigo_empresa=portal['codigo_empresa'], codigo_articulo=articulo['codigo_articulo']).exists():
            articulo_detalle = Articulo.objects.get(
                codigo_empresa=portal['codigo_empresa'], codigo_articulo=articulo['codigo_articulo'])
        else:
            logger.error("No se ha podido recuperar el articulo: " +
                         articulo['codigo_articulo'])

        if (articulo_detalle.controlar_stock != 'N'):

            presentacion = articulo['presentacion'] if 'presentacion' in articulo and articulo[
                'presentacion'] is not None and articulo['presentacion'] != "" else articulo_detalle.presentacion_web

            codigo_almacen = articulo['codigo_almacen'] if 'codigo_almacen' in articulo and articulo['codigo_almacen'] is not None else ""

            situacion = articulo['situacion'] if 'situacion' in articulo and articulo['situacion'] is not None else ""

            articulo_procesado = {'codigo_empresa': usuario.codigo_empresa,
                                  'codigo_portal': portal['codigo_portal'],
                                  'codigo_articulo': articulo['codigo_articulo'],
                                  'usuario_web': usuario.usuario_web,
                                  'codigo_almacen': codigo_almacen,
                                  'presentacion': presentacion,
                                  'tipo_situacion': situacion
                                  }

            articulos_procesados.append(articulo_procesado)
        else:
            # Si el articulo no controla stock lo añadimos directamente
            articulo_procesado = {'codigo_articulo': articulo['codigo_articulo'],
                                  'stock': 'S',
                                  'texto_stock': ""
                                  }
            respuesta_procesada.append(articulo_procesado)

    body = json.dumps(
        articulos_procesados,
        sort_keys=False,
        indent=None,
        use_decimal=True,
        default=fecha_encoder
    )
    try:
        respuesta_lisa = comunica_lisa(
            endpoint=endpoint, body=body, cache_seconds=0, portal=portal, usuario=usuario)

        if isinstance(respuesta_lisa['articulos'], list):
            for articulo in respuesta_lisa['articulos']:
                articulo_procesado = {
                    'codigo_articulo': articulo['codigo_articulo'],
                    'stock': articulo['stocks']['total_cantidad_presentacion'],
                    'texto_stock': articulo['stocks']['texto_stock']}

                respuesta_procesada.append(articulo_procesado)
        else:
            articulo_procesado = {
                'codigo_articulo': respuesta_lisa['articulos']['articulo']['codigo_articulo'],
                'stock': respuesta_lisa['articulos']['articulo']['stocks']['total_cantidad_presentacion'],
                'texto_stock': respuesta_lisa['articulos']['articulo']['stocks']['texto_stock']}

            respuesta_procesada.append(articulo_procesado)

    except ConnectionError as e:
        logger.error("La conexion a lisa: " + endpoint +
                     " ha fallado, excepcion: " + str(e))
        raise Exception("La conexion a lisa: " + endpoint +
                        " ha fallado, excepcion: " + str(e))
    except Exception as e:
        logger.error("La peticion a lisa: " + endpoint +
                     " ha fallado, excepcion: " + str(e))
        raise Exception("La peticion a lisa: " + endpoint +
                        " ha fallado, excepcion: " + str(e))

    return respuesta_procesada


def buscarArticulos(portal, usuario, articulos_completos, busqueda=None, filtros=None, avanzada="N", codigo_articulo=None, descripcion=None, palabras_clave=None, codigo_barras=None, equivalentes=None, referencia_cliente=None, codigo_sinonimo=None):

    codigoEmpresa = portal['codigo_empresa']

    lista_rfcas = ""

    if ClientesParametros.objects.filter(
            empresa=portal['codigo_empresa'], codigo_cliente=usuario.codigo_cliente).exists():

        parametros_cliente = ClientesParametros.objects.get(
            empresa=portal['codigo_empresa'], codigo_cliente=usuario.codigo_cliente)

        lista_rfcas = parametros_cliente.lista_rfcas

    articulos = articulos_completos

    articulos_fam_multiples = Articulo.objects.none()

    if filtros is not None:

        for filtro in filtros:

            if filtro['tipo'] == "estad":
                estadistico = int(filtro['estadistico'])

                campo = 'codigo_estad'+str(estadistico) # Valor empleado para todos los estadisticos != 1

                familias_hijas = listaFamiliaHijas(
                    portal['codigo_empresa'], estadistico, filtro['familia'])

                # filtramos el conjunto original por cada filtro aplicado que no sea padre(acumulativos)
                if len(familias_hijas) == 0:
                    if estadistico == 1:
                        articulos = articulos.filter(
                            codigo_familia=filtro['familia']
                        )
                    else:
                        articulos = articulos.filter(Q(**{"%s" % campo: filtro['familia'] }))
                
                # el filtro aplicado es padre, obtenemos los artículos de todos sus hijos, filtramos el conjunto original por los codigos de artículo presentes entodos los hijos
                else:
                    articulos_unidos = Articulo.objects.none()
                    # unico valor distinto de norma
                    if estadistico == 1:
                            articulos_hija = articulos_completos.filter(
                                codigo_familia__in=familias_hijas
                            )
                    else :
                        articulos_hija = articulos_completos.filter(Q(**{"%s__in" % campo: familias_hijas }))

                    articulos_unidos = articulos_unidos.union(
                            articulos_hija)

                    if len(articulos_unidos) > 0:
                        # Exist no puede ir después de Union, forzados a usar In
                        articulos = articulos.filter(
                            codigo_articulo__in=articulos_unidos.values("codigo_articulo"))
                    else:
                        articulos = Articulo.objects.none()

                articulos_fam_multiples = articulos_completos.filter(codigo_empresa=codigoEmpresa).filter(Exists(ArticulosFamilias.objects.filter(
                    codigo_empresa=codigoEmpresa, numero_tabla=estadistico, codigo_familia=filtro['familia'], codigo_articulo=OuterRef("codigo_articulo"))))
            else:
                if filtro['tipo'] == "clave":
                    clave_estadistica = filtro['estadistico']
                    valor_clave = filtro['familia']

                    claves_hijas = clavesHijas(
                        codigoEmpresa, clave_estadistica, valor_clave)

                    # filtramos el conjunto original por cada filtro aplicado que no sea padre(acumulativos)
                    if len(claves_hijas) == 0:
                        articulos = articulos.filter(Exists(ArticulosClavesEstadisticas.objects.filter(
                            empresa=portal['codigo_empresa'], clave=clave_estadistica, valor_clave=valor_clave, codigo_articulo=OuterRef("codigo_articulo")))
                        )

                    else:  # es una clave padre
                        articulos_unidos = Articulo.objects.none()

                        for hija in claves_hijas:  # obtenemos los artículos para cada clave hija
                            articulos_hija = articulos_completos.filter(Exists(ArticulosClavesEstadisticas.objects.filter(
                                empresa=portal['codigo_empresa'], clave=hija.clave, valor_clave=hija.valor_clave, codigo_articulo=OuterRef("codigo_articulo")))
                            )
                            articulos_unidos = articulos_unidos.union(
                                articulos_hija)
                        if len(articulos_unidos) > 0:
                            articulos = articulos.filter(
                                codigo_articulo__in=articulos_unidos.values("codigo_articulo"))
                        else:
                            articulos = Articulo.objects.none()

                else:  # filtros de un tipo no aceptado, devolvemos vacío
                    articulos = Articulo.objects.none()

    if avanzada == 'N':
        if busqueda is not None and busqueda != '':

            # Permitir utilizar más de una palabra en la búsqueda por palabras clave
            ecom_palabras_clave = reduce(and_, [Q(Exists(EcomPalabrasClave.objects.filter(codigo_empresa=portal['codigo_empresa'],
                                         codigo_portal=portal['codigo_portal'], palabra_clave__icontains=b, codigo_articulo=OuterRef('codigo_articulo')))) for b in busqueda.split()])

            articulos_palabra = articulos_completos.filter(
                Q(codigo_articulo=busqueda) |
                Q(codigo_sinonimo=busqueda) |
                Q(descrip_comercial__icontains=busqueda) |
                Q(Exists(ArticulosDescripcionWeb.objects.filter(
                    codigo_empresa=portal['codigo_empresa'], idioma=portal['idioma']).extra(where=["match(descripcion_web,descripcion_web_ampliada,descripcion_grupo,descripcion_web_reducida) against (%s IN boolean  MODE)"], params=[procesar_texto_busqueda(portal, busqueda)]).filter(codigo_articulo=OuterRef("codigo_articulo")))) |
                ecom_palabras_clave |
                Q(Exists(CodigoBarras.objects.filter(
                    codigo_empresa=portal['codigo_empresa'], numero_barras=busqueda, codigo_articulo=OuterRef('codigo_articulo')))) |
                Q(Exists(ArticulosEquivalentes.objects.filter(
                    codigo_empresa=portal['codigo_empresa'], codigo_articulo=busqueda, codigo_articulo_equ=OuterRef('codigo_articulo')))) |
                Q(Exists(DetalleListaReferencias.objects.filter(
                    empresa=portal['codigo_empresa'], codigo_lista=lista_rfcas, codigo_subreferencia=busqueda, codigo_articulo=OuterRef('codigo_articulo'))))
            )

            # filtramos el conjunto con los filtros aplicados por el codigo de los articulos que cumplen la busqueda por palabra si esta existe
            articulos = articulos.filter(
                Exists(articulos_palabra.filter(codigo_articulo=OuterRef("codigo_articulo"))))

            articulos_fam_multiples = articulos_fam_multiples.filter(
                Exists(articulos_palabra.filter(codigo_articulo=OuterRef("codigo_articulo"))))
    else:
        articulos_palabra = articulos_completos

        if codigo_articulo is not None and codigo_articulo != "":
            articulos_palabra = articulos_palabra.filter(
                codigo_articulo=codigo_articulo)

        if codigo_sinonimo is not None and codigo_sinonimo != "":
            articulos_palabra = articulos_palabra.filter(
                codigo_sinonimo=codigo_sinonimo)

        if descripcion is not None and descripcion != "":

            descripciones = ArticulosDescripcionWeb.objects.filter(codigo_empresa=portal['codigo_empresa'], idioma=portal['idioma']).extra(
                where=["match(descripcion_web,descripcion_web_ampliada,descripcion_grupo,descripcion_web_reducida) against (%s IN boolean  MODE)"], params=[procesar_texto_busqueda(portal, descripcion)])[:settings.REST_FRAMEWORK['PAGE_SIZE']]

            descripciones_lista = list(
                descripciones.values_list('codigo_articulo', flat=True))

            articulos_palabra = articulos_palabra.filter(Q(descrip_comercial__icontains=descripcion) |
                                                         Q(codigo_articulo__in=descripciones_lista))

        if palabras_clave is not None and len(palabras_clave) > 0:
            articulos_palabra = articulos_palabra.filter(
                Exists(EcomPalabrasClave.objects.filter(
                    codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], palabra_clave__in=palabras_clave, codigo_articulo=OuterRef('codigo_articulo'))))

        if codigo_barras is not None and codigo_barras != "":
            articulos_palabra = articulos_palabra.filter(Exists(CodigoBarras.objects.filter(
                codigo_empresa=portal['codigo_empresa'], numero_barras=codigo_barras, codigo_articulo=OuterRef('codigo_articulo'))))

        if referencia_cliente is not None and referencia_cliente != "":
            articulos_palabra = articulos_palabra.filter(Exists(DetalleListaReferencias.objects.filter(
                empresa=portal['codigo_empresa'], codigo_lista=lista_rfcas, codigo_subreferencia=referencia_cliente, codigo_articulo=OuterRef('codigo_articulo'))))

        if equivalentes is not None and equivalentes != "" and equivalentes == "S":

            articulos_palabra = articulos_completos.filter(Exists(ArticulosEquivalentes.objects.filter(
                codigo_empresa=portal['codigo_empresa'], codigo_articulo__in=articulos_palabra.values('codigo_articulo'), codigo_articulo_equ=OuterRef('codigo_articulo'))))

        # filtramos el conjunto con los filtros aplicados por el codigo de los articulos que cumplen la busqueda por palabra si esta existe
        articulos = articulos.filter(
            Exists(articulos_palabra.filter(codigo_articulo=OuterRef("codigo_articulo"))))

        articulos_fam_multiples = articulos_fam_multiples.filter(
            Exists(articulos_palabra.filter(codigo_articulo=OuterRef("codigo_articulo"))))

    articulos = articulos.union(articulos_fam_multiples)

    # ordenamos por defecto con el campo orden de la tabla
    articulos = articulos.order_by('orden')

    return articulos


def calcula_ofertas_multiples(portal, usuario, codigo_articulo, codigo_cliente, presentacion):
    endpoint = '/V1/B2B/GETOFERTAS'

    body = {'codigo_empresa': usuario.codigo_empresa,  # '013',
            'codigo_portal': portal['codigo_portal'],
            'usuario_web': usuario.usuario_web,
            'articulo': codigo_articulo,
            'cliente': codigo_cliente,  # 'PT45672311',
            'presentacion': presentacion,
            }

    try:
        respuesta_lisa = comunica_lisa(endpoint, body, 1800)
    except ConnectionError as e:
        logger.error("La peticion a lisa: " + endpoint +
                     " ha fallado, excepcion: " + str(e))
        raise Exception("La peticion a lisa: " + endpoint +
                        " ha fallado, excepcion: " + str(e))
    except Exception as e:
        logger.error("La peticion a lisa: " + endpoint +
                     " ha fallado, excepcion: " + str(e))
        raise Exception("La peticion a lisa: " + endpoint +
                        " ha fallado, excepcion: " + str(e))

    if respuesta_lisa['ofertas'] is not None:
        if 'oferta' in respuesta_lisa['ofertas']:
            oferta = respuesta_lisa['ofertas']['oferta']
            respuesta_lisa['ofertas'] = list()
            respuesta_lisa['ofertas'].append(oferta)

    return respuesta_lisa


def procesar_texto_busqueda(portal, texto):
    prep_pron = ["a", "ante", "bajo", "cabe", "con", "contra", "de", "desde", "en", "entre", "hacia", "hasta",
                 "para", "por", "según", "segun", "sin", "so", "sobre", "tras", "el", "la", "los", "las", "le", "les", "y"]

    palabras_positivas = list(PesoPalabrasBusqueda.objects.filter(
        codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], peso="positivo").values_list('palabra', flat=True))
    palabras_negativas = list(PesoPalabrasBusqueda.objects.filter(
        codigo_empresa=portal['codigo_empresa'], codigo_portal=portal['codigo_portal'], peso="negativo").values_list('palabra', flat=True))

    texto_palabras = texto.split(' ')
    palabras_filtradas = [
        palabra for palabra in texto_palabras if palabra not in prep_pron]

    texto = ""

    for palabra in palabras_filtradas:
        if palabra in palabras_positivas:
            texto = texto + " +(>"+palabra + "*) "
        elif palabra in palabras_negativas:
            texto = texto + " +(<"+palabra + "*) "
        else:
            texto = texto + " +"+palabra + "* "

    return texto
