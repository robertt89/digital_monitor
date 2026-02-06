# Documentación de Estructura JSON - LED Display Monitoring System

## Versión: 1.0
## Fecha: 2026-02-04

---

## Estructura General
```json
{
  "ts": "2026-02-04T14:30:00Z",
  "sys": { ... },
  "snds": [ ... ],
  "bds": [ ... ]
}
```

---

## Campos Raíz

### `ts` (timestamp)
- **Tipo:** String (ISO 8601 format)
- **Descripción:** Marca de tiempo UTC de cuando se recolectó la información del sistema LED
- **Formato:** `YYYY-MM-DDTHH:mm:ssZ`
- **Ejemplo:** `"2026-02-04T14:30:00Z"`
- **Obligatorio:** Sí

---

## Objeto `sys` (System Information)

Información general del sistema de control LED.

### Campos:

#### `port`
- **Tipo:** String
- **Descripción:** Nombre del puerto COM usado para la comunicación con el sistema de control
- **Ejemplo:** `"COM3"`, `"COM1"`
- **Rango:** Cualquier nombre de puerto COM válido
- **Obligatorio:** Sí

#### `scr` (screen_count)
- **Tipo:** Integer
- **Descripción:** Número total de pantallas LED configuradas en el sistema
- **Ejemplo:** `2`
- **Rango:** 0 - 200 (según SDK)
- **Obligatorio:** Sí

#### `snd` (sender_count)
- **Tipo:** Integer
- **Descripción:** Número total de tarjetas enviadoras (sending cards) conectadas al sistema
- **Ejemplo:** `1`
- **Rango:** 0 - 255
- **Obligatorio:** Sí

#### `init` (is_initialized)
- **Tipo:** Boolean (0 o 1)
- **Descripción:** Indica si el SDK está correctamente inicializado y comunicándose con el hardware
- **Valores:**
  - `1` (true): SDK inicializado correctamente
  - `0` (false): SDK no inicializado o error de comunicación
- **Obligatorio:** Sí

### Ejemplo completo:
```json
"sys": {
  "port": "COM3",
  "scr": 2,
  "snd": 1,
  "init": 1
}
```

---

## Array `snds` (Sending Cards)

Lista de tarjetas enviadoras (sending cards/controllers) y su estado.

### Estructura de cada elemento:
Cada elemento es un objeto con los siguientes campos:

#### `i` (sender_index)
- **Tipo:** Integer
- **Descripción:** Índice único de la tarjeta enviadora
- **Ejemplo:** `0`
- **Rango:** 0 - 254 (255 es dirección de broadcast)
- **Obligatorio:** Sí

#### `dvi` (dvi_status)
- **Tipo:** Boolean (0 o 1)
- **Descripción:** Estado de la señal DVI/HDMI de entrada
- **Valores:**
  - `1` (true): Señal DVI/HDMI presente y válida
  - `0` (false): Sin señal DVI/HDMI o señal inválida
- **Obligatorio:** Sí
- **SDK Reference:** `GetOneSenderDVIStatus()`

#### `vid` (is_video_ok)
- **Tipo:** Boolean (0 o 1)
- **Descripción:** Estado general de la fuente de video
- **Valores:**
  - `1` (true): Fuente de video OK
  - `0` (false): Error en fuente de video
- **Obligatorio:** Sí
- **SDK Reference:** `IsVodeoOk()`

### Ejemplo completo:
```json
"snds": [
  {
    "i": 0,
    "dvi": 1,
    "vid": 1
  },
  {
    "i": 1,
    "dvi": 0,
    "vid": 0
  }
]
```

---

## Array `bds` (Scan Boards / Receiving Cards)

Lista de tarjetas receptoras (scan boards/receiving cards) y sus parámetros de monitoreo.

### Estructura de cada elemento:
Cada elemento es un **array** con 6 valores en el siguiente orden:
```
[sender_index, port_index, scan_board_index, status, temperature, voltage]
```

### Posición 0: `sender_index`
- **Tipo:** Integer
- **Descripción:** Índice de la tarjeta enviadora a la que está conectada esta scan board
- **Ejemplo:** `0`
- **Rango:** 0 - 254
- **Obligatorio:** Sí

### Posición 1: `port_index`
- **Tipo:** Integer
- **Descripción:** Índice del puerto Ethernet de la tarjeta enviadora
- **Ejemplo:** `0`, `1`
- **Rango:** 
  - MSD300: 0 - 1 (2 puertos)
  - MCTRL500: 0 - 3 (4 puertos)
- **Obligatorio:** Sí

### Posición 2: `scan_board_index`
- **Tipo:** Integer
- **Descripción:** Índice de la scan board conectada al puerto Ethernet especificado
- **Ejemplo:** `0`, `15`, `128`
- **Rango:** 0 - 65535
- **Obligatorio:** Sí

### Posición 3: `status`
- **Tipo:** String
- **Descripción:** Estado operacional de la scan board
- **Valores posibles:**
  - `"OK"`: Funcionando correctamente
  - `"E"`: Error (Error)
  - `"U"`: Desconocido (Unknown)
- **Obligatorio:** Sí
- **SDK Reference:** `IsScanBoardWorkOK()`

### Posición 4: `temperature`
- **Tipo:** Float o null
- **Descripción:** Temperatura actual de la scan board en grados Celsius
- **Ejemplo:** `45.5`, `52.3`, `null`
- **Rango:** Típicamente 0 - 100°C
- **null cuando:** La lectura no está disponible o no es válida
- **Obligatorio:** Sí (puede ser null)
- **SDK Reference:** `GetScanBoardTemperature()`

### Posición 5: `voltage`
- **Tipo:** Float o null
- **Descripción:** Voltaje actual de la scan board en voltios
- **Ejemplo:** `5.2`, `4.9`, `null`
- **Rango:** Típicamente 4.5 - 5.5V (para sistemas de 5V)
- **null cuando:** La lectura no está disponible o no es válida
- **Obligatorio:** Sí (puede ser null)
- **SDK Reference:** `GetScanBoardVoltage()`

### Ejemplo completo:
```json
"bds": [
  [0, 0, 0, "OK", 45.5, 5.2],
  [0, 0, 1, "OK", 46.2, 5.1],
  [0, 1, 0, "E", 52.8, 4.9],
  [0, 1, 1, "OK", 44.8, 5.3],
  [0, 1, 2, "U", null, null]
]
```

### Interpretación del ejemplo:
1. **Board [0,0,0]**: Sender 0, Puerto 0, Board 0 - OK, 45.5°C, 5.2V
2. **Board [0,0,1]**: Sender 0, Puerto 0, Board 1 - OK, 46.2°C, 5.1V
3. **Board [0,1,0]**: Sender 0, Puerto 1, Board 0 - Error, 52.8°C, 4.9V (alta temperatura)
4. **Board [0,1,1]**: Sender 0, Puerto 1, Board 1 - OK, 44.8°C, 5.3V
5. **Board [0,1,2]**: Sender 0, Puerto 1, Board 2 - Unknown, sin lecturas

---

## Ejemplo JSON Completo
```json
{
  "ts": "2026-02-04T14:30:00Z",
  "sys": {
    "port": "COM3",
    "scr": 2,
    "snd": 1,
    "init": 1
  },
  "snds": [
    {
      "i": 0,
      "dvi": 1,
      "vid": 1
    }
  ],
  "bds": [
    [0, 0, 0, "OK", 45.5, 5.2],
    [0, 0, 1, "OK", 46.2, 5.1],
    [0, 1, 0, "E", 52.8, 4.9],
    [0, 1, 1, "OK", 44.8, 5.3],
    [0, 1, 2, "U", null, null]
  ]
}
```

---

## Casos Especiales

### Sistema no inicializado
```json
{
  "ts": "2026-02-04T14:30:00Z",
  "sys": {
    "port": "COM3",
    "scr": 0,
    "snd": 0,
    "init": 0
  },
  "snds": [],
  "bds": []
}
```

### Sin señal DVI
```json
{
  "ts": "2026-02-04T14:30:00Z",
  "sys": {
    "port": "COM3",
    "scr": 1,
    "snd": 1,
    "init": 1
  },
  "snds": [
    {
      "i": 0,
      "dvi": 0,
      "vid": 0
    }
  ],
  "bds": [
    [0, 0, 0, "OK", 45.5, 5.2]
  ]
}
```

### Lecturas no disponibles
```json
"bds": [
  [0, 0, 0, "U", null, null],
  [0, 0, 1, "OK", null, 5.1],
  [0, 0, 2, "OK", 46.2, null]
]
```

---

## Notas de Implementación

### Parseo de `bds` en diferentes lenguajes:

#### JavaScript/Node.js
```javascript
const data = JSON.parse(jsonString);

data.bds.forEach(board => {
  const [senderIdx, portIdx, boardIdx, status, temp, voltage] = board;
  console.log(`Board ${senderIdx}-${portIdx}-${boardIdx}: ${status}, ${temp}°C, ${voltage}V`);
});
```

#### Python
```python
import json

data = json.loads(json_string)

for board in data['bds']:
    sender_idx, port_idx, board_idx, status, temp, voltage = board
    print(f"Board {sender_idx}-{port_idx}-{board_idx}: {status}, {temp}°C, {voltage}V")
```

#### PHP
```php
$data = json_decode($jsonString, true);

foreach ($data['bds'] as $board) {
    [$senderIdx, $portIdx, $boardIdx, $status, $temp, $voltage] = $board;
    echo "Board $senderIdx-$portIdx-$boardIdx: $status, {$temp}°C, {$voltage}V\n";
}
```

#### C#
```csharp
var data = JsonSerializer.Deserialize<JsonDocument>(jsonString);

foreach (var board in data.RootElement.GetProperty("bds").EnumerateArray()) {
    var senderIdx = board[0].GetInt32();
    var portIdx = board[1].GetInt32();
    var boardIdx = board[2].GetInt32();
    var status = board[3].GetString();
    var temp = board[4].ValueKind == JsonValueKind.Null ? null : board[4].GetDouble();
    var voltage = board[5].ValueKind == JsonValueKind.Null ? null : board[5].GetDouble();
}
```

---

## Validación de Datos

### Reglas de validación:

1. **Timestamp (`ts`)**:
   - Debe ser un string válido en formato ISO 8601
   - Debe incluir zona horaria (UTC preferido)

2. **System (`sys`)**:
   - `init` debe ser 0 o 1
   - Si `init` es 0, `snds` y `bds` deberían estar vacíos

3. **Sending Cards (`snds`)**:
   - No debe haber índices duplicados (`i`)
   - `dvi` y `vid` deben ser 0 o 1

4. **Scan Boards (`bds`)**:
   - No debe haber combinaciones duplicadas de [sender, port, board]
   - `status` debe ser "OK", "E" o "U"
   - `temperature` y `voltage` pueden ser null o números

---

## Límites y Restricciones

| Campo | Valor Mínimo | Valor Máximo | Notas |
|-------|-------------|--------------|-------|
| `sys.scr` | 0 | 200 | Según documentación SDK |
| `sys.snd` | 0 | 255 | 255 es broadcast |
| `snds[].i` | 0 | 254 | - |
| `bds[][0]` (sender) | 0 | 254 | - |
| `bds[][1]` (port) | 0 | 3 | Depende del modelo |
| `bds[][2]` (board) | 0 | 65535 | - |
| `bds[][4]` (temp) | null o 0 | null o 100 | °C, típico |
| `bds[][5]` (voltage) | null o 4.5 | null o 5.5 | V, para sistemas 5V |

---

## Tamaño Estimado del JSON

### Cálculo aproximado:

- **Base (sin boards):** ~150 bytes
- **Por sending card:** ~35 bytes
- **Por scan board:** ~25 bytes

### Ejemplos:
- 1 sender, 10 boards: ~400 bytes
- 1 sender, 100 boards: ~2.7 KB
- 2 senders, 500 boards: ~12.8 KB

### Con compresión gzip:
- Reducción típica: 60-75%
- 500 boards: ~3-5 KB comprimido

---

## Historial de Versiones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-02-04 | Versión inicial del protocolo |

---

## Contacto y Soporte

Para preguntas sobre esta especificación, contactar al equipo de desarrollo.
