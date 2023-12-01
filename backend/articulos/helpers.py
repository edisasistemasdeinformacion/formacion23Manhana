def procesaFamilia(familia):
    return{
        "codigo_familia": familia.codigo_familia,
        "numero_tabla": familia.numero_tabla,
        "codigo_empresa": familia.codigo_empresa,
        "codigo_padre": familia.codigo_padre,
        "descripcion": familia.descripcion,
        "ultimo_nivel": familia.ultimo_nivel,
        "sufijo_contable": familia.sufijo_contable,
        "tipo_impuesto": familia.tipo_impuesto,
        "valor_homologacion": familia.valor_homologacion,
        "desc_abreviada": familia.desc_abreviada,
        "agrupacion_packing_list": familia.agrupacion_packing_list,
        "control_disponibilidad": familia.control_disponibilidad,
        "sistema_reserva": familia.sistema_reserva,
        "periodo_variacion_precios": familia.periodo_variacion_precios,
        "num_periodos_a_restar": familia.num_periodos_a_restar,
        "sufijo_contable2": familia.sufijo_contable2,
        "reservado_number_1": familia.reservado_number_1,
        "reservado_number_2": familia.reservado_number_2,
        "farma_real_decreto": familia.farma_real_decreto,
        "reservado_alfa_1": familia.reservado_alfa_1,
        "reservado_alfa_2": familia.reservado_alfa_2,
        "reservado_alfa_3": familia.reservado_alfa_3,
        "reservado_alfa_4": familia.reservado_alfa_4,
        "presentacion_servicios_frio": familia.presentacion_servicios_frio,
        "articulo_servicios_frio": familia.articulo_servicios_frio,
        "crmdepartamento": familia.crmdepartamento,
        "intervalo": familia.intervalo
    }


def procesaFiltro(filtro):
     return{
        "codigo_empresa": filtro.codigo_empresa,
        "codigo_portal":  filtro.codigo_portal,
        "estadistico": filtro.estadistico,
        "nombre": filtro.nombre
     }