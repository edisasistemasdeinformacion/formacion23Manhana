from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers
from django.contrib.auth import authenticate
from pedidos.models import WebPedidos, WebPedidosLin, TiposPedidoVta, TextosVentas, DescuentosTramosHorariosCliente, EcomFormasEnvioTarifas, Divisas
from django.db import models
from django.apps import apps
from articulos.models import Articulo

if apps.is_installed("articulos_extrusion"):
    from articulos_extrusion.models import Perfil

# Pedidos Serializer


class WebPedidosLinSerializer(serializers.ModelSerializer):

    class Meta:
        model = WebPedidosLin
        fields = '__all__'

    def to_representation(self, instance):

        data = super(WebPedidosLinSerializer,
                     self).to_representation(instance)

        if apps.is_installed("articulos_extrusion"):
            self.ampliar_info_linea_extrusion(data)

        self.ampliar_info_linea(data)

        return data

    def ampliar_info_linea(self, linea):

        articulo = linea.get('id_articulo')
        datos_articulo = Articulo.objects.filter(
            id=articulo).values()
        linea.update(datos_articulo=datos_articulo)

    def ampliar_info_linea_extrusion(self, linea):

        portal = self.context['request'].session['portal']

        perfil = linea.get('articulo')[:5]
        datos_perfil = Perfil.objects.filter(
            codigo_empresa=portal['codigo_empresa'], codigo_perfil=perfil).values()
        linea.update(datos_perfil=datos_perfil)


class WebPedidosSerializer(serializers.ModelSerializer):
    lineas = WebPedidosLinSerializer(many=True)

    class Meta:
        model = WebPedidos
        fields = '__all__'


class IntegraPedidoSerializer(serializers.Serializer):
    resultado = serializers.CharField(read_only=True)
    error = serializers.CharField(read_only=True)

    def get(self, data):
        return "GET"

    def post(self, data):
        return "POST"


class TiposPedidoVtaSerializer(serializers.ModelSerializer):

    class Meta:
        model = TiposPedidoVta
        fields = '__all__'


class TextosVentasSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextosVentas
        fields = '__all__'


class DescuentosTramosHorariosClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DescuentosTramosHorariosCliente
        fields = '__all__'


class EcomFormasEnvioTarifasSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcomFormasEnvioTarifas
        fields = '__all__'


class DivisasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Divisas
        fields = '__all__'
