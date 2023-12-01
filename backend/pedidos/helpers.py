def procesa_linea(linea):
    if linea.estado_linea not in ('A','B','C','D','H'):
        c = 'Pendiente revisión carnet. '
        rO = 'Receta adjunta. '
        r1 = 'No dispongo de receta. '
        r2 = 'Dispongo de receta electrónica. '
        r3 = 'Dispongo de receta en papel. '
       
        # Validacion carnet
        if linea.estado_linea == 'C':
            linea.observaciones = c + linea.observaciones
        
        # Validacion recetas
        if linea.estado_linea == 'AX':
            linea.observaciones = rO + linea.observaciones
        if linea.estado_linea == 'A1':
            linea.observaciones = r1 + linea.observaciones
        if linea.estado_linea == 'A2':
            linea.observaciones = r2 + \
                linea.observaciones
        if linea.estado_linea == 'A3':
            linea.observaciones = r3 + \
                linea.observaciones
        if linea.estado_linea == 'C0':
            linea.observaciones = c + rO + linea.observaciones
        if linea.estado_linea == 'C1':
            linea.observaciones = c + r1 + linea.observaciones
        if linea.estado_linea == 'C2':
            linea.observaciones = c + r2 + linea.observaciones
        if linea.estado_linea == 'C3':
            linea.observaciones = c + r3 + linea.observaciones

        linea.estado_linea = 'A'
       
    return {
        "articulo": linea.articulo,
        "numero_lote_int": linea.numero_lote_int,
        "catalogo": linea.catalogo,
        "descripcion": linea.descripcion,
        "cantidad1": linea.cantidad1,
        "cantidad2": linea.cantidad2,
        "precio_venta": linea.precio_venta,
        "observaciones": linea.observaciones,
        "estado_linea": linea.estado_linea,
        "silo": linea.silo,
        "estado_preparacion": linea.estado_preparacion,
        "unidad_minima_vta": linea.unidad_minima_vta,
        "tipo_articulo": linea.tipo_articulo,
        "cantidad_pedida": linea.cantidad_pedida,
        "presentacion_pedido": linea.presentacion_pedido,
        "fecha_grabacion": linea.fecha_grabacion,
        "categoria": linea.categoria,
        "version_estru": linea.version_estru,
        "proveedor_mezcla": linea.proveedor_mezcla,
        "codigo_org_planta": linea.codigo_org_planta,
        "tipo_linea": linea.tipo_linea,
        "unidades_reservadas": linea.unidades_reservadas,
        "uni_resalm": linea.uni_resalm,
        "dto_1": linea.dto_1,
        "dto_2": linea.dto_2,
        "dto_3": linea.dto_3,
        "dto_4": linea.dto_4,
        "dto_5": linea.dto_5,
        "dto_6": linea.dto_6,
        "dto_7": linea.dto_7,
        "dto_8": linea.dto_8,
        "dto_9": linea.dto_9,
        "idto_1": linea.idto_1,
        "idto_2": linea.idto_2,
        "idto_3": linea.idto_3,
        "idto_4": linea.idto_4,
        "idto_5": linea.idto_5,
        "idto_6": linea.idto_6,
        "idto_7": linea.idto_7,
        "idto_8": linea.idto_8,
        "idto_9": linea.idto_9,
        "dtos_acumulados_resto1": linea.dtos_acumulados_resto1,
        "dtos_acumulados_resto2": linea.dtos_acumulados_resto2,
        "dtos_acumulados_resto3": linea.dtos_acumulados_resto3,
        "precio_neto": linea.precio_neto,
        "importe_bruto_lin": linea.importe_bruto_lin,
        "importe_neto_lin": linea.importe_neto_lin,
        "tipo_uni_cad_log": linea.tipo_uni_cad_log,
        "fecha_entrega": linea.fecha_entrega,
        "numero_linea_origen": linea.numero_linea_origen,
        "precio_manual": linea.precio_manual if linea.precio_manual is not None else 'N',
        "sub_pres": linea.sub_pres,
        "sub_pres_cant": linea.sub_pres_cant,
        "sub_pres_fc": linea.sub_pres_fc,
        "presentacion_escogida": linea.presentacion_escogida,
        "clave_actuacion": linea.clave_actuacion
    }


# , domicilio, observaciones, forma_envio):
def procesa_pedido(codigo_portal, usuario_web, pedido):
    return {
        "codigo_empresa": pedido.codigo_empresa,
        "codigo_portal": codigo_portal,
        "usuario_web": usuario_web,
        "id_pedido": pedido.id_pedido,
        "pedido_cliente": pedido.pedido_cliente,
        "fecha_pedido": pedido.fecha_pedido.strftime('%Y-%m-%d %H:%M:%S') if pedido.fecha_pedido is not None else None,
        "texto_forma_envio": pedido.texto_forma_envio,
        "servir_completo": pedido.servir_completo,
        "tip_reserva": pedido.tip_reserva,
        "pendiente_autorizar": pedido.pendiente_autorizar,
        "observaciones": pedido.observaciones,
        "persona_pedido": pedido.persona_pedido,
        "tipo_pedido": pedido.tipo_pedido,
        "status_pedido": pedido.status_pedido,
        "estado_pedido": pedido.estado_pedido,
        "importe_cobrado": pedido.importe_cobrado,
        "importe_portes": pedido.importe_portes,
        "fecha_entrega": pedido.fecha_entrega.strftime('%Y-%m-%d %H:%M:%S') if pedido.fecha_entrega is not None else None,
        "forma_pago": pedido.forma_pago,
        "fecha_valor": pedido.fecha_valor,
        "domicilio_envio": pedido.domicilio_envio,
        "forma_envio": pedido.forma_envio,
        "almacen": pedido.almacen,
        "transportista": pedido.transportista,
        "nombre_dom_envio": pedido.nombre_dom_envio,
        "direccion_dom_envio": pedido.direccion_dom_envio,
        "localidad_dom_envio": pedido.localidad_dom_envio,
        "estado_dom_envio": pedido.estado_dom_envio,
        "provincia_dom_envio": pedido.provincia_dom_envio,
        "cod_postal_dom_envio": pedido.cod_postal_dom_envio,
        "tipo_portes_dom_envio": pedido.tipo_portes_dom_envio,
        "zona_dom_envio": pedido.zona_dom_envio,
        "email": pedido.email
    }
