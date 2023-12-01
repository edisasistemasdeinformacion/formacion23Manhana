from django.db import models


class WebPedidos(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    codigo_empresa = models.CharField(max_length=5)
    pedido_cliente = models.CharField(max_length=15, blank=True, null=True)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    codigo_cliente = models.CharField(max_length=15, blank=True, null=True)
    domicilio_envio = models.CharField(max_length=5, blank=True, null=True)
    forma_envio = models.CharField(max_length=4, blank=True, null=True)
    texto_forma_envio = models.CharField(max_length=50, blank=True, null=True)
    domicilio_cobro = models.CharField(max_length=2, blank=True, null=True)
    servir_completo = models.CharField(max_length=1, blank=True, null=True)
    pendiente_autorizar = models.CharField(max_length=1, blank=True, null=True)
    origen_pedido = models.CharField(max_length=8, blank=True, null=True)
    observaciones = models.CharField(max_length=500, blank=True, null=True)
    estado_pedido = models.CharField(max_length=1, blank=True, null=True)
    organizacion_comercial = models.CharField(
        max_length=5, blank=True, null=True)
    numero_pedido = models.IntegerField(blank=True, null=True)
    numero_serie = models.CharField(max_length=3, blank=True, null=True)
    ejercicio = models.IntegerField(blank=True, null=True)
    persona_pedido = models.CharField(max_length=40, blank=True, null=True)
    tipo_pedido = models.CharField(max_length=3, blank=True, null=True)
    numero_pres = models.IntegerField(blank=True, null=True)
    numero_serie_pres = models.CharField(max_length=3, blank=True, null=True)
    id_pedido_padre = models.IntegerField(blank=True, null=True)
    status_pedido = models.CharField(max_length=4, blank=True, null=True)
    status_pres = models.CharField(max_length=4, blank=True, null=True)
    tip_reserva = models.CharField(max_length=1, blank=True, null=True)
    importe_cobrado = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    importe_portes = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    divisa = models.CharField(max_length=4, blank=True, null=True)
    fecha_entrega = models.DateTimeField(blank=True, null=True)
    forma_pago = models.CharField(max_length=4, blank=True, null=True)
    fecha_valor = models.DateField(blank=True, null=True)
    almacen = models.CharField(max_length=5, blank=True, null=True)
    transportista = models.CharField(max_length=15, blank=True, null=True)
    hash_usuario = models.TextField(blank=True, null=True)
    id_pedido_libra = models.CharField(max_length=15, blank=True, null=True)
    nombre_dom_envio = models.CharField(max_length=50, blank=True, null=True)
    direccion_dom_envio = models.CharField(
        max_length=50, blank=True, null=True)
    localidad_dom_envio = models.CharField(
        max_length=50, blank=True, null=True)
    estado_dom_envio = models.CharField(max_length=4, blank=True, null=True)
    provincia_dom_envio = models.CharField(max_length=4, blank=True, null=True)
    cod_postal_dom_envio = models.CharField(
        max_length=15, blank=True, null=True)
    tipo_portes_dom_envio = models.CharField(
        max_length=1, blank=True, null=True)
    zona_dom_envio = models.CharField(
        max_length=10, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.id_pedido

    class Meta:
        db_table = "web_pedidos"
        verbose_name_plural = "Pedidos"


class WebPedidosLin(models.Model):
    id_pedido = models.ForeignKey(
        WebPedidos, to_field='id_pedido', db_column='id_pedido', related_name='lineas', on_delete=models.CASCADE)
    numero_linea = models.IntegerField()
    articulo = models.CharField(max_length=30, blank=True, null=True)
    numero_lote_int = models.CharField(max_length=20, blank=True, null=True)
    catalogo = models.CharField(max_length=1, blank=True, null=True)
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    cantidad1 = models.IntegerField(blank=True, null=True)
    cantidad2 = models.IntegerField(blank=True, null=True)
    precio_venta = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    observaciones = models.CharField(max_length=500, blank=True, null=True)
    estado_linea = models.CharField(max_length=2, blank=True, null=True)
    texto_error = models.CharField(max_length=100, blank=True, null=True)
    tipo_articulo = models.CharField(max_length=12, blank=True, null=True)
    cantidad_pedida = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    presentacion_pedido = models.CharField(
        max_length=5, blank=True, null=True)
    fecha_grabacion = models.DateField(
        auto_now_add=True, blank=True, null=True)
    tipo_linea = models.CharField(max_length=1, blank=True, null=True)
    dto_1 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    dto_2 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    dto_3 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    dto_4 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    dto_5 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    dto_6 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    dto_7 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    dto_8 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    dto_9 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    dtos_acumulados_resto1 = models.CharField(max_length=1, default='N')
    dtos_acumulados_resto2 = models.CharField(max_length=1, default='N')
    dtos_acumulados_resto3 = models.CharField(max_length=1, default='N')
    precio_neto = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    importe_bruto_lin = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    importe_neto_lin = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    tipo_uni_cad_log = models.CharField(max_length=3, blank=True, null=True)
    silo = models.CharField(max_length=5, blank=True, null=True)
    estado_preparacion = models.CharField(max_length=1, blank=True, null=True)
    unidad_minima_vta = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    categoria = models.CharField(max_length=3, blank=True, null=True)
    version_estru = models.CharField(max_length=3, blank=True, null=True)
    proveedor_mezcla = models.CharField(max_length=15, blank=True, null=True)
    codigo_org_planta = models.CharField(max_length=15, blank=True, null=True)
    unidades_reservadas = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    uni_resalm = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    idto_1 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    idto_2 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    idto_3 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    idto_4 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    idto_5 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    idto_6 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    idto_7 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    idto_8 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    idto_9 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    fecha_entrega = models.DateField(blank=True, null=True)
    id_articulo = models.IntegerField(blank=True, null=True)
    numero_linea_origen = models.IntegerField(blank=True, null=True)
    precio_manual = models.CharField(
        max_length=1, blank=True, null=True, default='N')
    sub_pres = models.CharField(max_length=500, blank=True, null=True)
    sub_pres_cant = models.IntegerField(blank=True, null=True)
    sub_pres_fc = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    pres_fc = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    presentacion_escogida = models.CharField(
        max_length=5, blank=True, null=True)
    clave_actuacion = models.CharField(
        max_length=3, blank=True, null=True)

    def __str__(self):
        return self.numero_linea

    class Meta:
        db_table = "web_pedidos_lin"
        verbose_name_plural = "Líneas Pedido"
        unique_together = [['id_pedido', 'numero_linea']]
        indexes = [
            models.Index(fields=['id_pedido', 'id_articulo', 'tipo_linea']),
            models.Index(fields=['id_pedido', 'tipo_articulo']),
            models.Index(fields=['id_pedido', 'tipo_linea']),
        ]


class TiposPedidoVta(models.Model):
    codigo_empresa = models.CharField(max_length=5)
    organizacion_comercial = models.CharField(max_length=5)
    tipo_pedido = models.CharField(max_length=3)
    descripcion = models.CharField(max_length=40)

    def __str__(self):
        return self.descripcion

    class Meta:
        db_table = "tipos_pedido_vta"
        verbose_name_plural = "Tipos de pedido de ventas"
        unique_together = [
            ['codigo_empresa', 'organizacion_comercial', 'tipo_pedido']]


class TextosVentas(models.Model):
    codigo_empresa = models.CharField(max_length=5, blank=False, null=False)
    organizacion_comercial = models.CharField(
        max_length=5, blank=False, null=False)
    idioma = models.CharField(max_length=2, blank=False, null=False)
    presupuesto = models.CharField(max_length=1, blank=True, null=True)
    desde_fecha = models.DateField(blank=False, null=False)
    hasta_fecha = models.DateField(blank=False, null=False)
    texto = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        db_table = "textos_ventas"
        verbose_name_plural = "Textos de ventas"


class DescuentosTramosHorariosCliente(models.Model):
    codigo_empresa = models.CharField(max_length=5, blank=False, null=False)
    organizacion_comercial = models.CharField(
        max_length=5, blank=False, null=False)
    tipo_pedido = models.CharField(max_length=2, blank=False, null=False)
    cliente = models.CharField(max_length=15, blank=False, null=False)
    fecha_validez = models.DateTimeField(blank=True, null=True)
    desde_hora = models.DateTimeField(blank=True, null=True)
    hasta_hora = models.DateTimeField(blank=True, null=True)
    porc_adc_tipo_pedido = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    dcto_global = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)

    class Meta:
        db_table = "b2b_dtos_tramo_horario_cliente"
        verbose_name_plural = "Descuentos tramos horarios por cliente"

        unique_together = [
            ['codigo_empresa', 'organizacion_comercial', 'tipo_pedido', 'cliente', 'fecha_validez', 'desde_hora']]


class EcomFormasEnvioTarifas(models.Model):
    codigo_empresa = models.CharField(max_length=5, blank=False, null=False)
    codigo_portal = models.CharField(
        max_length=10, blank=False, null=False)
    forma_envio = models.CharField(max_length=4, blank=False, null=False)
    estado = models.CharField(max_length=4, blank=False, null=False)
    provincia = models.CharField(max_length=4, blank=False, null=False)
    peso_max_pagados = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    importe_min_pagados = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True)
    importe = models.DecimalField(
        max_digits=19, decimal_places=4, blank=False, null=False)
    articulo = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        db_table = "ecom_formas_envio_tarifas"
        verbose_name_plural = "Tarifas de formas envio"

        unique_together = [
            ['codigo_empresa', 'codigo_portal', 'forma_envio', 'estado', 'provincia']]

class Divisas(models.Model):
    codigo = models.CharField(max_length=4, blank=False, null=False)
    nombre = models.CharField(max_length=40, blank=True, null=True)
    cod_iso4217a = models.CharField(max_length=3, blank=True, null=True)
    decimales_significativos = models.IntegerField(blank=True, null=True)
    decimales_precios = models.IntegerField(blank=True, null=True)
    decimales_pvp = models.IntegerField(blank=True, null=True)


    class Meta:
        db_table = "divisas"
        verbose_name_plural = "Divisas Libra-ISO"

        unique_together = [['codigo']]
