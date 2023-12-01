from django.db import models


class Articulo(models.Model):
    codigo_articulo = models.CharField(max_length=30)
    codigo_empresa = models.CharField(max_length=5)
    codigo_familia = models.CharField(max_length=15)
    codigo_estad2 = models.CharField(max_length=15, blank=True, null=True)
    codigo_estad3 = models.CharField(max_length=15, blank=True, null=True)
    codigo_estad4 = models.CharField(max_length=15, blank=True, null=True)
    codigo_estad5 = models.CharField(max_length=15, blank=True, null=True)
    codigo_estad6 = models.CharField(max_length=15, blank=True, null=True)
    codigo_estad7 = models.CharField(max_length=15, blank=True, null=True)
    codigo_estad8 = models.CharField(max_length=15, blank=True, null=True)
    codigo_estad9 = models.CharField(max_length=15, blank=True, null=True)
    codigo_estad10 = models.CharField(max_length=15, blank=True, null=True)
    descrip_comercial = models.CharField(max_length=500)
    descrip_reducida = models.CharField(max_length=14, blank=True, null=True)
    descrip_tecnica = models.CharField(max_length=500, blank=True, null=True)
    descrip_compra = models.CharField(max_length=500, blank=True, null=True)
    orden = models.IntegerField(blank=True, null=True)
    unidad_codigo1 = models.CharField(max_length=5, blank=True, null=True)
    codigo_estad11 = models.CharField(max_length=15, blank=True, null=True)
    codigo_estad12 = models.CharField(max_length=15, blank=True, null=True)
    codigo_estad13 = models.CharField(max_length=15, blank=True, null=True)
    codigo_estad14 = models.CharField(max_length=15, blank=True, null=True)
    codigo_estad15 = models.CharField(max_length=15, blank=True, null=True)
    codigo_estad16 = models.CharField(max_length=15, blank=True, null=True)
    codigo_estad17 = models.CharField(max_length=15, blank=True, null=True)
    codigo_estad18 = models.CharField(max_length=15, blank=True, null=True)
    codigo_estad19 = models.CharField(max_length=15, blank=True, null=True)
    codigo_estad20 = models.CharField(max_length=15, blank=True, null=True)
    presentacion_web = models.CharField(max_length=5, blank=True, null=True)
    tipo_material = models.CharField(max_length=1, blank=True, null=True)
    reservado_alfa_3 = models.CharField(max_length=50, blank=True, null=True)
    partida_arancelaria = models.CharField(
        max_length=30, blank=True, null=True)
    tipo_cadena_logistica = models.CharField(
        max_length=4, blank=True, null=True)
    reservado_number_1 = models.IntegerField(blank=True, null=True)
    reservado_number_2 = models.IntegerField(blank=True, null=True)
    cliente_elaboracion = models.CharField(
        max_length=15, blank=True, null=True)
    alfa3_fao = models.CharField(
        max_length=3, blank=True, null=True)
    residuo = models.CharField(max_length=30, blank=True, null=True)
    cantidad_minima = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    cantidad_maxima = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    multiplo = models.IntegerField(blank=True, null=True)
    peso_neto = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    controlar_stock = models.CharField(max_length=1, blank=True, null=True)
    codigo_familia_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad2_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad3_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad4_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad5_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad6_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad7_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad8_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad9_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad10_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad11_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad12_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad13_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad14_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad15_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad16_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad17_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad18_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad19_d = models.CharField(max_length=40, blank=True, null=True)
    codigo_estad20_d = models.CharField(max_length=40, blank=True, null=True)
    d_alfa3_fao = models.CharField(max_length=500, blank=True, null=True)
    unidad_codigo2 = models.CharField(max_length=5, blank=True, null=True)
    d_unidad_codigo2 = models.CharField(max_length=120, blank=True, null=True)
    unidad_precio_venta = models.IntegerField(blank=True, null=True)
    codigo_sinonimo = models.CharField(max_length=30, blank=True, null=True)
    reservado_alfa_1 = models.CharField(max_length=50, blank=True, null=True)
    reservado_alfa_2 = models.CharField(max_length=50, blank=True, null=True)
    reservado_alfa_4 = models.CharField(max_length=50, blank=True, null=True)
    fecha_baja = models.DateField(blank=True, null=True)
    codigo_situacion = models.CharField(max_length=1, blank=True, null=True)
    tipo_carnet_profesional = models.CharField(
        max_length=5, blank=True, null=True)
    codigo_catalogo = models.CharField(max_length=4, blank=True, null=True)
    tipo = models.CharField(max_length=1, blank=True, null=True)
    rowid_lov = models.CharField(max_length=40, blank=True, null=True)
    numero_receta = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.descrip_comercial

    class Meta:
        db_table = "articulos"
        verbose_name_plural = "Articulos"
        unique_together = [['codigo_articulo', 'codigo_empresa']]
        indexes = [
            models.Index(fields=['codigo_articulo']),
            models.Index(fields=['codigo_familia', 'codigo_empresa']),
            models.Index(fields=['codigo_estad2', 'codigo_empresa']),
            models.Index(fields=['codigo_estad3', 'codigo_empresa']),
            models.Index(fields=['codigo_estad4', 'codigo_empresa']),
            models.Index(fields=['codigo_estad5', 'codigo_empresa']),
            models.Index(fields=['codigo_estad6', 'codigo_empresa']),
            models.Index(fields=['codigo_estad7', 'codigo_empresa']),
            models.Index(fields=['codigo_estad8', 'codigo_empresa']),
            models.Index(fields=['codigo_estad9', 'codigo_empresa']),
            models.Index(fields=['codigo_estad10', 'codigo_empresa']),
            models.Index(fields=['codigo_estad11', 'codigo_empresa']),
            models.Index(fields=['codigo_estad12', 'codigo_empresa']),
            models.Index(fields=['codigo_estad13', 'codigo_empresa']),
            models.Index(fields=['codigo_estad14', 'codigo_empresa']),
            models.Index(fields=['codigo_estad15', 'codigo_empresa']),
            models.Index(fields=['codigo_estad16', 'codigo_empresa']),
            models.Index(fields=['codigo_estad17', 'codigo_empresa']),
            models.Index(fields=['codigo_estad18', 'codigo_empresa']),
            models.Index(fields=['codigo_estad19', 'codigo_empresa']),
            models.Index(fields=['codigo_estad20', 'codigo_empresa']),
            models.Index(fields=['tipo_material']),
            models.Index(fields=['codigo_sinonimo']),
        ]


class Familia(models.Model):
    codigo_familia = models.CharField(max_length=30)
    numero_tabla = models.IntegerField()
    codigo_empresa = models.CharField(max_length=5)
    codigo_padre = models.CharField(max_length=15, blank=True, null=True)
    descripcion = models.CharField(max_length=40, blank=True, null=True)
    ultimo_nivel = models.CharField(max_length=1, blank=True, null=True)
    sufijo_contable = models.CharField(max_length=15, blank=True, null=True)
    tipo_impuesto = models.CharField(max_length=5, blank=True, null=True)
    valor_homologacion = models.IntegerField(blank=True, null=True)
    desc_abreviada = models.CharField(max_length=12, blank=True, null=True)
    agrupacion_packing_list = models.IntegerField(blank=True, null=True)
    control_disponibilidad = models.CharField(
        max_length=1, blank=True, null=True)
    sistema_reserva = models.IntegerField(blank=True, null=True)
    periodo_variacion_precios = models.CharField(
        max_length=1, blank=True, null=True)
    num_periodos_a_restar = models.IntegerField(blank=True, null=True)
    sufijo_contable2 = models.CharField(max_length=15, blank=True, null=True)
    reservado_number_1 = models.IntegerField(blank=True, null=True)
    reservado_number_2 = models.IntegerField(blank=True, null=True)
    farma_real_decreto = models.CharField(max_length=1, blank=True, null=True)
    reservado_alfa_1 = models.CharField(max_length=500, blank=True, null=True)
    reservado_alfa_2 = models.CharField(
        max_length=500, blank=True, null=True)
    reservado_alfa_3 = models.CharField(
        max_length=500, blank=True, null=True)
    reservado_alfa_4 = models.CharField(max_length=500, blank=True, null=True)
    presentacion_servicios_frio = models.CharField(
        max_length=5, blank=True, null=True)
    articulo_servicios_frio = models.CharField(
        max_length=30, blank=True, null=True)
    crmdepartamento = models.CharField(max_length=20, blank=True, null=True)
    intervalo = models.CharField(max_length=5, blank=True, null=True)
    orden = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.descripcion

    class Meta:
        db_table = "familias"
        verbose_name_plural = "Familias"
        unique_together = [
            ['codigo_familia', 'numero_tabla', 'codigo_empresa']]
        indexes = [
            models.Index(
                fields=['descripcion', 'codigo_empresa'])
        ]


class ArticulosImagenesGaleria(models.Model):
    empresa = models.CharField(max_length=5)
    articulo = models.CharField(max_length=30)
    numero_imagen = models.IntegerField(blank=False, null=False)
    principal = models.CharField(max_length=1, blank=True, null=True)
    fichero = models.CharField(max_length=100, blank=True, null=True)
    path = models.CharField(max_length=100, blank=True, null=True)
    extension = models.CharField(max_length=3, blank=True, null=True)
    imagen_web = models.CharField(max_length=1, blank=True, null=True)
    orden_3d = models.IntegerField(blank=True, null=True)
    imagen = models.BinaryField(blank=True, null=True)
    articulo_referencia = models.CharField(
        max_length=30, blank=True, null=True)
    fecha_mod = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "articulos_imagenes_galeria"
        verbose_name_plural = "Galeria"
        unique_together = [['empresa', 'articulo', 'numero_imagen']]


class Filtro(models.Model):
    codigo_empresa = models.CharField(max_length=5)
    codigo_portal = models.CharField(max_length=10)
    estadistico = models.IntegerField()
    nombre = models.CharField(max_length=50)
    desde_nivel = models.IntegerField(blank=True, null=True)
    hasta_nivel = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "ecom_filtros"
        verbose_name_plural = "Filtros"
        unique_together = [['codigo_empresa', 'codigo_portal', 'estadistico']]


class ArticulosDescripcionWeb(models.Model):
    codigo_empresa = models.CharField(max_length=5)
    codigo_articulo = models.CharField(max_length=30)
    idioma = models.CharField(max_length=2)
    descripcion_web = models.TextField(blank=True, null=True)
    descripcion_web_ampliada = models.TextField(blank=True, null=True)
    descripcion_grupo = models.TextField(blank=True, null=True)
    modelo = models.CharField(max_length=40, blank=True, null=True)
    descripcion_web_reducida = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "articulos_descripcion_web"
        verbose_name_plural = "Descripciones"
        unique_together = [['codigo_empresa', 'codigo_articulo', 'idioma']]


class EcomArticulosPortales(models.Model):
    codigo_empresa = models.CharField(max_length=5)
    codigo_portal = models.CharField(max_length=10)
    codigo_articulo = models.CharField(max_length=30)
    activo = models.CharField(max_length=1)
    resultados_busqueda = models.CharField(max_length=1)
    novedad = models.CharField(max_length=1)
    oferta = models.CharField(max_length=1)
    id_articulo_portal = models.CharField(max_length=100, null=True)
    numero_dias_novedad = models.IntegerField(blank=True, null=True)
    novedad_fecha_desde = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "ecom_articulos_portales"
        verbose_name_plural = "Novedades y ofertas"
        unique_together = [
            ['codigo_empresa', 'codigo_portal', 'codigo_articulo']]


class EcomArticulosRelacionados(models.Model):
    codigo_empresa = models.CharField(max_length=5)
    codigo_articulo = models.CharField(max_length=30)
    codigo_articulo_relacionado = models.CharField(max_length=30)

    class Meta:
        db_table = "ecom_articulos_relacionados"
        verbose_name_plural = "Articulos relacionados"
        unique_together = [
            ['codigo_empresa', 'codigo_articulo', 'codigo_articulo_relacionado']]


class EcomFamiliasPortales(models.Model):
    codigo_empresa = models.CharField(max_length=5)
    codigo_portal = models.CharField(max_length=10)
    numero_tabla = models.CharField(max_length=50)
    codigo_familia = models.CharField(max_length=15)
    novedad = models.CharField(max_length=1)
    oferta = models.CharField(max_length=1)
    numero_dias_novedad = models.IntegerField(blank=True, null=True)
    novedad_fecha_desde = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "ecom_familias_portales"
        verbose_name_plural = "Novedades y ofertas por familias"
        unique_together = [
            ['codigo_empresa', 'codigo_portal', 'numero_tabla', 'codigo_familia']]


class EcomPalabrasClave(models.Model):
    codigo_empresa = models.CharField(max_length=5)
    codigo_portal = models.CharField(max_length=10)
    codigo_articulo = models.CharField(max_length=30)
    palabra_clave = models.CharField(max_length=100)
    manual = models.CharField(max_length=1)

    class Meta:
        db_table = "ecom_palabras_clave"
        verbose_name_plural = "Palabras clave"
        unique_together = [
            ['codigo_empresa', 'codigo_portal', 'codigo_articulo', 'palabra_clave']]
        indexes = [
            models.Index(
                fields=['palabra_clave', 'codigo_portal', 'codigo_empresa']),
        ]


class EcomArtAgrup(models.Model):
    codigo_empresa = models.CharField(max_length=5)
    codigo_portal = models.CharField(max_length=10)
    codigo_articulo = models.CharField(max_length=30)

    class Meta:
        db_table = "ecom_art_agrup"
        verbose_name_plural = "Agrupaciones de Artículos"
        unique_together = [
            ['codigo_empresa', 'codigo_portal', 'codigo_articulo']]


class EcomArtAgrupHijos(models.Model):
    codigo_empresa = models.CharField(max_length=5)
    codigo_portal = models.CharField(max_length=10)
    codigo_padre = models.CharField(max_length=30)
    codigo_articulo = models.CharField(max_length=30)

    class Meta:
        db_table = "ecom_art_agrup_hijos"
        verbose_name_plural = "Artículos Hijos"
        unique_together = [
            ['codigo_empresa', 'codigo_portal', 'codigo_padre', 'codigo_articulo']]
        indexes = [
            models.Index(fields=['codigo_articulo',
                         'codigo_portal', 'codigo_empresa'])
        ]


class EcomArtAgrupCond(models.Model):
    codigo_empresa = models.CharField(max_length=5)
    codigo_portal = models.CharField(max_length=10)
    codigo_padre = models.CharField(max_length=30)
    orden = models.IntegerField(blank=False, null=False)
    tipo = models.CharField(max_length=3, blank=False, null=False)
    numero_tabla = models.IntegerField(blank=True, null=True)
    valor = models.CharField(max_length=15, blank=False, null=False)

    class Meta:
        db_table = "ecom_art_agrup_cond"
        verbose_name_plural = "Condiciones de Agrupación"
        unique_together = [
            ['codigo_empresa', 'codigo_portal', 'codigo_padre', 'orden']]


class ClavesEstadisticasArt(models.Model):
    empresa = models.CharField(max_length=5)
    clave = models.CharField(max_length=10)
    nombre = models.CharField(max_length=50)
    numerica = models.CharField(max_length=1)
    utilidad = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = "claves_estadisticas_art"
        verbose_name_plural = "Claves Estadísticas Artículos"
        unique_together = [['empresa', 'clave']]


class ValoresClavesArt(models.Model):
    empresa = models.CharField(max_length=5)
    clave = models.CharField(max_length=10)
    valor_clave = models.CharField(max_length=10)
    nombre = models.CharField(max_length=50)
    nombre_reducido = models.CharField(max_length=15, blank=True, null=True)
    ultimo_nivel = models.CharField(max_length=1, blank=False, null=False)
    valor_padre = models.CharField(max_length=10, blank=True, null=True)
    observaciones = models.CharField(max_length=500, blank=True, null=True)
    reservado_alfa01 = models.CharField(max_length=500, blank=True, null=True)
    reservado_alfa02 = models.CharField(max_length=500, blank=True, null=True)
    reservado_alfa03 = models.CharField(max_length=500, blank=True, null=True)
    orden = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "valores_claves_art"
        verbose_name_plural = "Valores Claves Estadísticas"
        unique_together = [['empresa', 'clave', 'valor_clave']]


class ArticulosClavesEstadisticas(models.Model):
    empresa = models.CharField(max_length=5)
    codigo_articulo = models.CharField(max_length=30)
    clave = models.CharField(max_length=10)
    valor_clave = models.CharField(max_length=10, blank=True, null=True)
    valor_numerico = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)

    class Meta:
        db_table = "articulos_claves_estadisticas"
        verbose_name_plural = "Valores Claves Estadísticas de Artículo"
        unique_together = [['empresa', 'codigo_articulo', 'clave']]


class CodigoBarras(models.Model):
    codigo_empresa = models.CharField(max_length=5)
    codigo_sist_barra = models.CharField(max_length=5)
    codigo_articulo = models.CharField(max_length=30)
    numero_barras = models.CharField(max_length=40)

    class Meta:
        db_table = "codigos_barras"
        verbose_name_plural = "Codigos de barras"
        unique_together = [
            ['codigo_empresa', 'codigo_sist_barra', 'numero_barras']]
        indexes = [
            models.Index(fields=['numero_barras']),
            models.Index(fields=['numero_barras', 'codigo_empresa']),
            models.Index(fields=['codigo_articulo'])
        ]


class EcomArticulosProvincias(models.Model):

    empresa = models.CharField(max_length=5)
    portal = models.CharField(max_length=10)
    estado = models.CharField(max_length=5)
    provincia = models.CharField(max_length=10)
    articulo = models.CharField(max_length=30)
    fecha_baja = models.DateField(blank=True, null=True)
    observacion = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        db_table = "ecom_articulos_provincias"
        verbose_name_plural = "Artículos por provincias"
        unique_together = [
            ['empresa', 'portal', 'estado', 'provincia', 'articulo']]


class ArticulosDoc(models.Model):
    codigo_empresa = models.CharField(max_length=5, blank=False, null=False)
    codigo_articulo = models.CharField(max_length=30, blank=False, null=False)
    numero_doc = models.IntegerField(blank=False, null=False)
    tipo = models.CharField(max_length=1, blank=True, null=True)
    descripcion = models.CharField(max_length=50, blank=True, null=True)
    txt = models.CharField(max_length=2000, blank=True, null=True)
    nombre_fichero = models.CharField(max_length=500, blank=True, null=True)
    id_archivo = models.IntegerField(blank=True, null=True)
    archivo = models.BinaryField(blank=True, null=True)

    def __str__(self):
        return self.descripcion

    class Meta:
        db_table = "articulos_doc"
        verbose_name_plural = "Documentos de artículos"
        unique_together = [['numero_doc', 'codigo_articulo', 'codigo_empresa']]

        indexes = [
            models.Index(fields=['codigo_articulo']),
            models.Index(fields=['numero_doc', 'codigo_articulo'])
        ]


class ArticulosAux(models.Model):
    codigo_empresa = models.CharField(max_length=5, blank=False, null=False)
    codigo_articulo = models.CharField(max_length=30, blank=False, null=False)
    auxiliar_1 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_2 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_3 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_4 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_5 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_6 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_n1 = models.IntegerField(blank=True, null=True)
    auxiliar_n2 = models.IntegerField(blank=True, null=True)
    auxiliar_n3 = models.IntegerField(blank=True, null=True)
    auxiliar_n4 = models.IntegerField(blank=True, null=True)
    auxiliar_n5 = models.IntegerField(blank=True, null=True)
    auxiliar_n6 = models.IntegerField(blank=True, null=True)
    auxiliar_7 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_8 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_9 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_10 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_11 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_12 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_13 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_14 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_15 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_21 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_22 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_23 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_24 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_25 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_26 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_27 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_28 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_29 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_30 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_n7 = models.IntegerField(blank=True, null=True)
    auxiliar_n8 = models.IntegerField(blank=True, null=True)
    auxiliar_n9 = models.IntegerField(blank=True, null=True)
    auxiliar_n10 = models.IntegerField(blank=True, null=True)
    auxiliar_n11 = models.IntegerField(blank=True, null=True)
    auxiliar_n12 = models.IntegerField(blank=True, null=True)
    auxiliar_n13 = models.IntegerField(blank=True, null=True)
    auxiliar_n14 = models.IntegerField(blank=True, null=True)
    auxiliar_n15 = models.IntegerField(blank=True, null=True)
    auxiliar_n16 = models.IntegerField(blank=True, null=True)
    auxiliar_n17 = models.IntegerField(blank=True, null=True)
    auxiliar_n18 = models.IntegerField(blank=True, null=True)
    auxiliar_n19 = models.IntegerField(blank=True, null=True)
    auxiliar_n20 = models.IntegerField(blank=True, null=True)
    auxiliar_f1 = models.DateField(blank=True, null=True)
    auxiliar_f2 = models.DateField(blank=True, null=True)
    auxiliar_f3 = models.DateField(blank=True, null=True)
    auxiliar_f4 = models.DateField(blank=True, null=True)
    auxiliar_f5 = models.DateField(blank=True, null=True)
    auxiliar_f6 = models.DateField(blank=True, null=True)
    auxiliar_f7 = models.DateField(blank=True, null=True)
    auxiliar_f8 = models.DateField(blank=True, null=True)
    auxiliar_f9 = models.DateField(blank=True, null=True)
    auxiliar_f10 = models.DateField(blank=True, null=True)
    auxiliar_check_01 = models.CharField(max_length=1, blank=True, null=True)
    auxiliar_check_02 = models.CharField(max_length=1, blank=True, null=True)
    auxiliar_check_03 = models.CharField(max_length=1, blank=True, null=True)
    auxiliar_check_04 = models.CharField(max_length=1, blank=True, null=True)
    auxiliar_check_05 = models.CharField(max_length=1, blank=True, null=True)
    auxiliar_check_06 = models.CharField(max_length=1, blank=True, null=True)
    auxiliar_check_07 = models.CharField(max_length=1, blank=True, null=True)
    auxiliar_check_08 = models.CharField(max_length=1, blank=True, null=True)
    auxiliar_check_09 = models.CharField(max_length=1, blank=True, null=True)
    auxiliar_check_10 = models.CharField(max_length=1, blank=True, null=True)
    auxiliar_16 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_17 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_18 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_19 = models.CharField(max_length=40, blank=True, null=True)
    auxiliar_20 = models.CharField(max_length=40, blank=True, null=True)

    class Meta:
        db_table = "articulos_aux"
        verbose_name_plural = "Informacion auxiliar articulos"
        unique_together = [['codigo_articulo', 'codigo_empresa']]

        indexes = [
            models.Index(fields=['codigo_articulo'])
        ]


class EcomSubPresentaciones(models.Model):
    codigo_empresa = models.CharField(max_length=5, blank=False, null=False)
    codigo_portal = models.CharField(max_length=10, blank=False, null=False)
    codigo_articulo = models.CharField(max_length=30, blank=False, null=False)
    subpresentacion = models.CharField(max_length=500, blank=False, null=False)
    unidad_consumo = models.CharField(max_length=5, blank=True, null=True)
    factor_conversion = models.DecimalField(
        max_digits=19, decimal_places=4, blank=False, null=False)

    class Meta:
        db_table = "ecom_sub_presentaciones"
        verbose_name_plural = "Subpresentaciones de artículos"
        unique_together = [
            ['subpresentacion', 'codigo_articulo', 'codigo_portal', 'codigo_empresa']]


class ArticulosEquivalentes(models.Model):
    codigo_empresa = models.CharField(max_length=5, blank=False, null=False)
    codigo_articulo = models.CharField(max_length=30, blank=False, null=False)
    codigo_articulo_equ = models.CharField(
        max_length=30, blank=False, null=False)

    class Meta:
        db_table = "articulos_equivalentes"
        verbose_name_plural = "Artículos equivalentes"
        unique_together = [
            ['codigo_articulo_equ', 'codigo_articulo', 'codigo_empresa']]

        indexes = [
            models.Index(fields=['codigo_articulo', 'codigo_empresa'])
        ]


class FamiliasImagenes(models.Model):

    codigo_empresa = models.CharField(max_length=5, blank=False, null=False)
    numero_tabla = models.IntegerField(blank=False, null=False)
    codigo_familia = models.CharField(max_length=15, blank=False, null=False)
    codigo_imagen = models.CharField(max_length=10, blank=False, null=False)
    imagen = models.BinaryField(blank=True, null=True)
    imagen_principal = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        db_table = "familias_imagenes"
        verbose_name_plural = "Imágenes de familias"
        unique_together = [
            ['codigo_imagen', 'codigo_familia', 'numero_tabla', 'codigo_empresa']]

        indexes = [
            models.Index(fields=['codigo_familia',
                                 'numero_tabla', 'codigo_empresa'])
        ]


class CadenaLogistica(models.Model):

    codigo_empresa = models.CharField(max_length=5, blank=False, null=False)
    codigo_articulo = models.CharField(max_length=30, blank=False, null=False)
    tipo_cadena = models.CharField(max_length=4, blank=False, null=False)
    cod_presen_u_con = models.CharField(max_length=5, blank=True, null=True)
    cod_presen_u_sub = models.CharField(max_length=5, blank=True, null=True)
    cod_presen_u_sob = models.CharField(max_length=5, blank=True, null=True)
    cod_presen_u_dis = models.CharField(max_length=5, blank=True, null=True)
    cod_presen_u_exp = models.CharField(max_length=5, blank=True, null=True)
    convers_u_con = models.FloatField(blank=True, null=True)
    convers_u_sub = models.FloatField(blank=True, null=True)
    convers_u_sob = models.FloatField(blank=True, null=True)
    convers_u_dis = models.FloatField(blank=True, null=True)
    convers_u_exp = models.FloatField(blank=True, null=True)
    peso_n_u_con = models.FloatField(blank=True, null=True)
    peso_b_u_con = models.FloatField(blank=True, null=True)
    peso_n_u_sub = models.FloatField(blank=True, null=True)
    peso_b_u_sub = models.FloatField(blank=True, null=True)
    peso_n_u_sob = models.FloatField(blank=True, null=True)
    peso_b_u_sob = models.FloatField(blank=True, null=True)
    peso_n_u_dis = models.FloatField(blank=True, null=True)
    peso_b_u_dis = models.FloatField(blank=True, null=True)
    peso_n_u_exp = models.FloatField(blank=True, null=True)
    peso_b_u_exp = models.FloatField(blank=True, null=True)
    multiplo_pedido_tv_con = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = "cadena_logistica"
        verbose_name_plural = "Cadenas logísticas"
        unique_together = [
            ['tipo_cadena', 'codigo_articulo', 'codigo_empresa']]


class ArticulosFamilias(models.Model):

    codigo_empresa = models.CharField(max_length=5, blank=False, null=False)
    codigo_articulo = models.CharField(max_length=30, blank=False, null=False)
    numero_tabla = models.IntegerField(blank=False, null=False)
    codigo_familia = models.CharField(max_length=15, blank=False, null=False)

    class Meta:
        db_table = "articulos_familias"
        verbose_name_plural = "Articulos familias"
        unique_together = [
            ['codigo_familia', 'numero_tabla', 'codigo_articulo', 'codigo_empresa']]

        indexes = [
            models.Index(fields=['codigo_familia',
                                 'numero_tabla', 'codigo_empresa'])
        ]


class Presentaciones(models.Model):
    codigo = models.CharField(max_length=5, blank=False, null=False)
    descripcion = models.CharField(max_length=40, blank=True, null=True)
    medida_1 = models.DecimalField(
        max_digits=9, decimal_places=4, blank=True, null=True)
    medida_2 = models.DecimalField(
        max_digits=9, decimal_places=4, blank=True, null=True)
    medida_3 = models.DecimalField(
        max_digits=9, decimal_places=4, blank=True, null=True)
    control_palet = models.CharField(max_length=1, blank=True, null=True)
    especial = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        db_table = "presentaciones"
        verbose_name_plural = "Presentaciones"
        unique_together = [
            ['codigo']]


class PresenArticulo(models.Model):
    codigo_empresa = models.CharField(max_length=5, blank=False, null=False)
    codigo_articulo = models.CharField(max_length=30, blank=False, null=False)
    presentacion = models.CharField(max_length=5, blank=False, null=False)
    factor_conversion = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)

    class Meta:
        db_table = "presen_articulo"
        unique_together = [
            ['codigo_articulo', 'presentacion', 'codigo_empresa']]


class FiltroClaveEstadistica(models.Model):
    codigo_empresa = models.CharField(max_length=5, blank=False, null=False)
    codigo_portal = models.CharField(max_length=10, blank=False, null=False)
    clave_estadistica = models.CharField(
        max_length=10, blank=False, null=False)
    nombre = models.CharField(max_length=50)

    class Meta:
        db_table = "ecom_filtros_clv_est"
        verbose_name_plural = "Filtros por claves estadisticas"
        unique_together = [
            ['codigo_empresa', 'codigo_portal', 'clave_estadistica']]


class ArticulosIdiomas(models.Model):
    codigo_empresa = models.CharField(max_length=5, blank=False, null=False)
    codigo_articulo = models.CharField(max_length=30, blank=False, null=False)
    codigo_idioma = models.CharField(max_length=2, blank=False, null=False)
    descripcion_2 = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = "articulos_idiomas"
        verbose_name_plural = "Articulos idiomas"
        unique_together = [
            ['codigo_idioma', 'codigo_articulo', 'codigo_empresa']]


class NombresCientificos(models.Model):
    codigo = models.CharField(max_length=3, blank=False, null=False)
    nombre_cientifico = models.CharField(
        max_length=500, blank=False, null=False)

    class Meta:
        db_table = "nombres_cientificos"
        verbose_name_plural = "Nombres científicos"
        unique_together = [
            ['codigo']]


class AlmacenesArticulos(models.Model):
    codigo_empresa = models.CharField(max_length=5, blank=False, null=False)
    codigo_articulo = models.CharField(max_length=30, blank=False, null=False)
    codigo_almacen = models.CharField(max_length=5, blank=False, null=False)
    bloqueo_ventas = models.CharField(max_length=1, blank=False, null=False)

    class Meta:
        db_table = "almacenes_articulos"
        verbose_name_plural = "Articulos por almacen"
        unique_together = [
            ['codigo_articulo', 'codigo_almacen', 'codigo_empresa']]


class ArticulosProveedor(models.Model):
    codigo_empresa = models.CharField(max_length=5, blank=False, null=False)
    organizacion_compras = models.CharField(
        max_length=5, blank=False, null=False)
    codigo_articulo = models.CharField(max_length=30, blank=False, null=False)
    codigo_proveedor = models.CharField(max_length=15, blank=False, null=False)
    referencia_proveedor = models.CharField(
        max_length=30, blank=True, null=True)
    descrip_proveedor_1 = models.CharField(
        max_length=500, blank=True, null=True)
    descrip_proveedor_2 = models.CharField(
        max_length=500, blank=True, null=True)
    proveedor_habitual = models.CharField(max_length=1, blank=True, null=True)
    nombre_proveedor = models.CharField(max_length=40, blank=True, null=True)

    class Meta:
        db_table = "articulos_proveedor"
        verbose_name_plural = "Articulos Proveedor"
        unique_together = [
            ['codigo_proveedor', 'codigo_articulo', 'organizacion_compras', 'codigo_empresa']]


class DetalleListaReferencias(models.Model):
    empresa = models.CharField(max_length=5)
    codigo_lista = models.CharField(max_length=5)
    codigo_articulo = models.CharField(max_length=30)
    codigo_subreferencia = models.CharField(max_length=30)

    class Meta:
        db_table = "detalle_lista_rfcas"
        verbose_name_plural = "Referencias de clientes"
        unique_together = [
            ['codigo_subreferencia', 'codigo_articulo', 'codigo_lista', 'empresa']]
        indexes = [
            models.Index(fields=['codigo_subreferencia']),
            models.Index(fields=['codigo_subreferencia',
                         'codigo_lista', 'empresa']),
            models.Index(fields=['codigo_subreferencia',
                                 'empresa']),
            models.Index(fields=['codigo_lista', 'empresa']),
            models.Index(fields=['codigo_articulo'])
        ]


class PesoPalabrasBusqueda(models.Model):
    codigo_empresa = models.CharField(max_length=5)
    codigo_portal = models.CharField(max_length=10)
    palabra = models.CharField(max_length=200)
    peso = models.CharField(max_length=30)

    class Meta:
        db_table = "peso_palabras_busqueda"
        verbose_name_plural = "Peso de las palabras de búsqueda de artículos por texto"
        unique_together = [
            ['palabra', 'codigo_portal', 'codigo_empresa']]
