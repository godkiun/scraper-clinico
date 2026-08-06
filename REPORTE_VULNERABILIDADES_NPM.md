# Reporte de vulnerabilidades npm

**Fecha:** 2026-08-06  
**Alcance:** Proyectos en `C:\Users\52753\Desktop\PROYECTOS PERSONALES` con `package.json` y `npm audit`.

## Resumen ejecutivo

No se detectaron indicadores directos de infeccion activa por paquetes maliciosos en los archivos revisados (`package.json` / `package-lock.json`), pero si se encontraron vulnerabilidades de seguridad **high** en 3 proyectos.

## Proyectos con vulnerabilidades

| Proyecto | Paquete | Severidad | Riesgo principal | Rango vulnerable | Fix disponible |
|---|---|---|---|---|---|
| `...\APP WEB STOMALYZER\frontend` | `postcss` | high | Lectura arbitraria de archivos / path traversal via `sourceMappingURL` | `<=8.5.22` | Si |
| `...\MODELO PREDICTIVO...\frontend` | `brace-expansion` | high | DoS por expansion no acotada (OOM) | `<=1.1.17 \|\| 4.0.0 - 5.0.8` | Si |
| `...\MODELO PREDICTIVO...\frontend` | `next` | high | Multiples: bypass middleware, SSRF, cache confusion, DoS | `9.3.4-canary.0 - 16.3.0-preview.10` | Si (`next 16.3.0`) |
| `...\MODELO PREDICTIVO...\frontend` | `postcss` | high | XSS / lectura de archivos / divulgacion de informacion | `<=8.5.22` | Si (via upgrade de `next`) |
| `...\MODELO PREDICTIVO...\frontend` | `sharp` | high | Vulnerabilidades heredadas de `libvips` (CVE) | `<0.35.0` | Si (via upgrade de `next`) |
| `...\MODELO PREDICTIVO...\mcp-devops-server` | `fast-uri` | high | Host confusion por parsing de URI | `3.0.0 - 3.1.4` | Si |
| `...\MODELO PREDICTIVO...\mcp-devops-server` | `ip-address` | high | Bypass de validaciones SSRF/trust boundary | `<=10.3.0` | Si |

## Proyectos sin alertas high/critical

- `C:\Users\52753\Desktop\PROYECTOS PERSONALES\HELIOSCAN\frontend`
- `C:\Users\52753\Desktop\PROYECTOS PERSONALES\PROBAR MODELO`

## Recomendaciones inmediatas

1. Ejecutar `npm audit fix` en cada proyecto afectado.
2. Actualizar dependencias directas clave (`next`, `postcss`, `sharp`, `fast-uri`, `ip-address`) y regenerar lockfile.
3. Re-ejecutar `npm audit --audit-level=high` y confirmar cero hallazgos high/critical.
4. Rotar tokens de npm/GitHub si estuvieron expuestos en CI o archivos de configuracion.

