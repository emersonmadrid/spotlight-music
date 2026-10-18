# ⚖️ Aviso Legal, Términos y Reconocimiento de Terceros (Disclaimer)

**Spotlight Music** es un proyecto de código abierto desarrollado únicamente con fines de investigación, productividad personal y educación.

---

### 1. No Alojamiento ni Distribución de Contenido Protegido
* **Spotlight Music NO aloja, descarga, almacena, retransmite ni distribuye archivos de audio, video o material sujeto a derechos de autor (copyright) en ningún servidor.**
* La aplicación actúa exclusivamente como un **controlador de interfaz local (frontend)** que orquesta herramientas independientes instaladas por el propio usuario en su máquina.
* Toda la reproducción se realiza de forma **efímera y en tiempo real (streaming en vivo)** en el cliente local, sin que este software almacene copias fijas de las pistas en bases de datos o servidores externos.

---

### 2. Reconocimiento de Herramientas de Terceros y Licencias
Este proyecto se apoya en bibliotecas y utilidades de código abierto consolidadas, las cuales operan de manera independiente bajo sus respectivas licencias:

* **[mpv](https://mpv.io/):** Reproductor multimedia libre bajo licencia **GPLv2 / LGPLv2.1**. Spotlight Music se comunica con `mpv` a través de sockets IPC externos estándar, sin modificar su código fuente ni vulnerar los términos de la licencia.
* **[yt-dlp](https://github.com/yt-dlp/yt-dlp):** Herramienta de línea de comandos bajo licencia de dominio público **The Unlicense**. Es invocada por el motor multimedia como extractor de flujos públicos.
* **[LRCLIB](https://lrclib.net/) y [Lyrics.ovh](https://lyrics.ovh/):** APIs comunitarias y públicas consultadas en tiempo real para la obtención de texto lírico con fines de referencia personal e informativa bajo principios de uso justo (*Fair Use*).
* **[GTK3 / PyGObject](https://www.gtk.org/):** Entorno gráfico bajo licencia **LGPLv2.1+**.

---

### 3. Marcas Registradas y Derechos de Propiedad Intelectual
* Todos los nombres de canciones, nombres de artistas, marcas registradas, logotipos y carátulas de álbumes son propiedad exclusiva de sus respectivos titulares de derechos, sellos discográficos y creadores de contenido.
* El nombre *YouTube*, *YouTube Music* y marcas asociadas son propiedad de **Google LLC**. La mención de dichas plataformas en este proyecto tiene un propósito meramente descriptivo de interoperabilidad técnica y no implica respaldo, patrocinio, afiliación ni aprobación por parte de dichas entidades.

---

### 4. Responsabilidad del Usuario
El uso de esta herramienta está sujeto al cumplimiento de las leyes de propiedad intelectual de la jurisdicción de cada usuario, así como de los términos de servicio aplicables a las plataformas a las que el usuario acceda de forma voluntaria. El autor de Spotlight Music no asume responsabilidad alguna por el uso indebido o no autorizado que terceros puedan hacer de esta herramienta.
