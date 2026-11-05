# Runbook de incidencias — EST-01

Qué hacer ante cada alerta de la línea. Este texto es ficticio y solo vive en el laboratorio.
El agente de incidencias lee la sección de la alerta que salta y la usa para proponer la acción.
Las acciones las ejecuta siempre una persona.

## ArchivadorCaido

El archivador no responde. La estación sigue fabricando y sus registros no se guardan en el histórico.
Acción: arrancar el archivador (docker compose start archivador) y conciliar después cuántas carcasas se quedaron sin registro.
Avisar a calidad si la pérdida supera 30 carcasas, porque ese tramo no tendrá trazabilidad.

## HistoricoSinDatos

El archivador está vivo pero no guarda registros. Causa habitual: el broker se reinició y el archivador no renovó su suscripción.
Acción: reiniciar el archivador (docker compose restart archivador) y comprobar que vuelve a guardar.
Si se repite, corregir la reconexión del archivador.

## RegistrosPerdidos

La estación fabrica más carcasas de las que llegan al histórico.
Acción: comprobar que el broker y el archivador están en marcha y que el archivador guarda. Conciliar la pérdida.

## EstacionCaida

La estación no responde. No hay producción o no se puede medir.
Acción: avisar al operario de la estación para que compruebe si la máquina está parada.

## TemperaturaHusilloAlta

El husillo supera el margen del procedimiento.
Acción: avisar al operario. Revisar refrigeración y estado de la herramienta. No modificar consignas desde el puesto de datos.
