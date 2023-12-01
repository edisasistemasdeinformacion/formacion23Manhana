from articulos.models import Articulo, Familia, ArticulosImagenesGaleria, Filtro, ArticulosDescripcionWeb, EcomArticulosPortales,\
    EcomArticulosRelacionados, EcomPalabrasClave, EcomArtAgrup, EcomArtAgrupHijos, EcomArtAgrupCond, \
    ClavesEstadisticasArt, ValoresClavesArt, ArticulosClavesEstadisticas, ArticulosDoc, ArticulosAux, \
    EcomSubPresentaciones, ArticulosEquivalentes, FamiliasImagenes, CodigoBarras, CadenaLogistica, ArticulosFamilias, \
    Presentaciones, PresenArticulo, FiltroClaveEstadistica, ArticulosIdiomas, NombresCientificos, AlmacenesArticulos, ArticulosProveedor, \
    DetalleListaReferencias
from rest_framework import serializers


# Articulo Serializer


class ArticuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Articulo
        fields = '__all__'

    def to_representation(self, instance):

        data = super(ArticuloSerializer, self).to_representation(instance)

        portal = self.context['request'].session['portal']

        if ArticulosDescripcionWeb.objects.filter(codigo_empresa=data.get('codigo_empresa'), codigo_articulo=data.get('codigo_articulo'), idioma=portal['idioma']).exists():
            descripcion = ArticulosDescripcionWeb.objects.get(codigo_empresa=data.get(
                'codigo_empresa'), codigo_articulo=data.get('codigo_articulo'), idioma=portal['idioma'])

            if descripcion.descripcion_web is not None:
                data.update(descrip_comercial=descripcion.descripcion_web)

            data.update(
                descrip_web_ampliada=descripcion.descripcion_web_ampliada)
            data.update(
                descrip_web_reducida=descripcion.descripcion_web_reducida)
            data.update(
                descrip_grupo=descripcion.descripcion_grupo)

        if EcomArtAgrup.objects.filter(codigo_empresa=data.get('codigo_empresa'), codigo_portal=portal['codigo_portal'], codigo_articulo=data.get('codigo_articulo')).exists():
            data.update(tiene_agrupaciones='S')
        else:
            data.update(tiene_agrupaciones='N')

        if ArticulosEquivalentes.objects.filter(codigo_empresa=data.get('codigo_empresa'), codigo_articulo=data.get('codigo_articulo')).exists():
            data.update(tiene_equivalentes='S')
        else:
            data.update(tiene_equivalentes='N')

        if ArticulosIdiomas.objects.filter(codigo_empresa=data.get('codigo_empresa'), codigo_idioma=portal['idioma'], codigo_articulo=data.get('codigo_articulo')).exists():
            articulo_idioma = ArticulosIdiomas.objects.get(codigo_empresa=data.get(
                'codigo_empresa'), codigo_idioma=portal['idioma'], codigo_articulo=data.get('codigo_articulo'))
            data.update(descripcion_2=articulo_idioma.descripcion_2)

        proveedores = ArticulosProveedor.objects.filter(codigo_empresa=data.get(
            'codigo_empresa'), codigo_articulo=data.get('codigo_articulo')).values()

        data.update(proveedores=proveedores)

        return data


class GaleriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticulosImagenesGaleria
        fields = '__all__'


class PrecioSerializer(serializers.Serializer):
    precio = serializers.FloatField(read_only=True)

    def get(self, data):
        return 1.4


class FamiliaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Familia
        fields = '__all__'


class ImagenSerializer(serializers.Serializer):
    precio = serializers.IntegerField(read_only=True)

    def get(self, data):
       
        return 1


class FiltroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filtro
        fields = '__all__'


class EcomArticulosPortalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcomArticulosPortales
        fields = '__all__'


class EcomArticulosRelacionadosSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcomArticulosRelacionados
        fields = '__all__'


class EcomFamiliasPortalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcomArticulosRelacionados
        fields = '__all__'


class EcomPalabrasClaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcomPalabrasClave
        fields = '__all__'


class EcomArtAgrupHijosSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcomArtAgrupHijos
        fields = '__all__'

    def to_representation(self, instance):

        data = super(EcomArtAgrupHijosSerializer,
                     self).to_representation(instance)

        portal = self.context['request'].session['portal']

        articulo = Articulo.objects.get(codigo_empresa=data.get(
            'codigo_empresa'), codigo_articulo=data.get('codigo_articulo'))

        if ArticulosDescripcionWeb.objects.filter(codigo_empresa=data.get('codigo_empresa'), codigo_articulo=data.get('codigo_articulo'), idioma=portal['idioma']).exists():
            descripcion = ArticulosDescripcionWeb.objects.get(codigo_empresa=data.get(
                'codigo_empresa'), codigo_articulo=data.get('codigo_articulo'), idioma=portal['idioma'])

            if descripcion.descripcion_web is not None:
                data.update(descrip_comercial=descripcion.descripcion_web)
            else:
                data.update(descrip_comercial=articulo.descrip_comercial)
        else:
            articulo = Articulo.objects.get(codigo_empresa=data.get(
                'codigo_empresa'), codigo_articulo=data.get('codigo_articulo'))
            data.update(descrip_comercial=articulo.descrip_comercial)

        claves = ArticulosClavesEstadisticas.objects.filter(empresa=data.get(
            'codigo_empresa'), codigo_articulo=data.get('codigo_articulo')).values()

        data.update(claves=claves)

        ficha_articulo_serializada = ArticuloSerializer(
            articulo, context={'request': self.context['request']}).data

        data.update(ficha_articulo=ficha_articulo_serializada)

        return data


class EcomArtAgrupCondSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcomArtAgrupCond
        fields = '__all__'

    def to_representation(self, instance):

        data = super(EcomArtAgrupCondSerializer,
                     self).to_representation(instance)

        if data.get('tipo') == 'CLA':
            clave = ClavesEstadisticasArt.objects.filter(empresa=data.get(
                'codigo_empresa'), clave=data.get('valor')).values()[0]
            valores = ValoresClavesArt.objects.filter(empresa=data.get(
                'codigo_empresa'), clave=data.get('valor')).order_by("orden").values()

            data.update(clave=clave)
            data.update(valores=valores)

        return data


class CodigosBarrasSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodigoBarras
        fields = '__all__'


class ArticulosDocSerializer(serializers.ModelSerializer):

    class Meta:
        model = ArticulosDoc
        fields = '__all__'


class ArticulosAuxSerializer(serializers.ModelSerializer):

    class Meta:
        model = ArticulosAux
        fields = '__all__'


class EcomSubPresentacionesSerializer(serializers.ModelSerializer):

    class Meta:
        model = EcomSubPresentaciones
        fields = '__all__'


class ArticulosEquivalentesSerializer(serializers.ModelSerializer):

    class Meta:
        model = ArticulosEquivalentes
        fields = '__all__'


class FamiliasImagenesSerializer(serializers.ModelSerializer):

    class Meta:
        model = FamiliasImagenes
        fields = '__all__'


class CadenaLogisticaSerializer(serializers.ModelSerializer):

    class Meta:
        model = CadenaLogistica
        fields = '__all__'


class ArticulosFamiliasSerializer(serializers.ModelSerializer):

    class Meta:
        model = ArticulosFamilias
        fields = '__all__'


class PresentacionesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Presentaciones
        fields = '__all__'


class PresenArticuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = PresenArticulo
        fields = '__all__'

    def to_representation(self, instance):

        data = super(PresenArticuloSerializer,
                     self).to_representation(instance)

        if Presentaciones.objects.filter(
                codigo=data.get('presentacion')).exists():

            presentacion = Presentaciones.objects.get(
                codigo=data.get('presentacion'))

            data.update(descripcion=presentacion.descripcion)

        return data


class ClavesEstadisticasArtSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClavesEstadisticasArt
        fields = '__all__'


class ValoresClavesArtSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValoresClavesArt
        fields = '__all__'


class ArticulosClavesEstadisticasSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticulosClavesEstadisticas
        fields = '__all__'

    def to_representation(self, instance):

        data = super(ArticulosClavesEstadisticasSerializer,
                     self).to_representation(instance)

        portal = self.context['request'].session['portal']

        if ClavesEstadisticasArt.objects.filter(
                empresa=portal['codigo_empresa'],
                clave=data.get('clave')).exists():

            clave = ClavesEstadisticasArt.objects.get(
                empresa=portal['codigo_empresa'],
                clave=data.get('clave'))

            data.update(nombre_clave=clave.nombre)

        if ValoresClavesArt.objects.filter(empresa=portal['codigo_empresa'],
                                           clave=data.get('clave'),
                                           valor_clave=data.get('valor_clave')).exists():
            valor_clave = ValoresClavesArt.objects.get(empresa=portal['codigo_empresa'],
                                                       clave=data.get('clave'),
                                                       valor_clave=data.get('valor_clave'))

            data.update(nombre_valor_clave=valor_clave.nombre)

        return data


class FiltroClaveEstadisticaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiltroClaveEstadistica
        fields = '__all__'


class ArticulosIdiomasSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticulosIdiomas
        fields = '__all__'


class NombresCientificosSerializer(serializers.ModelSerializer):
    class Meta:
        model = NombresCientificos
        fields = '__all__'


class OfertasMultiplesSerializer(serializers.Serializer):
    ofertasMultiples = serializers.CharField(read_only=True)

    def get(self, data):
        return "1.4"


class AlmacenesArticulosSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlmacenesArticulos
        fields = '__all__'


class ArticulosProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticulosProveedor
        fields = '__all__'


class DetalleListaReferenciasSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleListaReferencias
        fields = '__all__'
