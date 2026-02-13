# Documentation / Documentación

This directory contains comprehensive documentation for integrating the Ditto TalkingHead project with LiveKit Agents Framework.

Este directorio contiene documentación completa para integrar el proyecto Ditto TalkingHead con LiveKit Agents Framework.

---

## 📄 Available Documents / Documentos Disponibles

### English Version
- **[Virtual Avatar LiveKit Analysis (EN)](./virtual_avatar_livekit_analysis_en.md)**
  - Complete analysis of the Ditto TalkingHead project
  - Key features needed for LiveKit integration
  - Proposed architecture and implementation
  - Code examples and best practices
  - Implementation roadmap

### Versión en Español
- **[Análisis Avatar Virtual LiveKit (ES)](./analisis_avatar_virtual_livekit_es.md)**
  - Análisis completo del proyecto Ditto TalkingHead
  - Características clave necesarias para integración con LiveKit
  - Arquitectura e implementación propuesta
  - Ejemplos de código y mejores prácticas
  - Roadmap de implementación

### Visual Assets / Recursos Visuales
- **[Architecture Comparison Table](./architecture_comparison_table.png)**
  - Visual comparison between current and LiveKit architectures
  - Comparación visual entre arquitectura actual y LiveKit

---

## 🎯 Document Purpose / Propósito del Documento

These documents provide a comprehensive guide for:
- Understanding the current Ditto TalkingHead architecture
- Identifying components needed for LiveKit integration
- Creating a custom LiveKit plugin for Ditto
- Implementing real-time avatar video streaming
- Optimizing performance and synchronization

Estos documentos proporcionan una guía completa para:
- Entender la arquitectura actual de Ditto TalkingHead
- Identificar componentes necesarios para integración con LiveKit
- Crear un plugin personalizado de LiveKit para Ditto
- Implementar streaming de video de avatar en tiempo real
- Optimizar rendimiento y sincronización

---

## 🚀 Quick Start / Inicio Rápido

### For Developers / Para Desarrolladores

1. **Read the analysis document** in your preferred language
   - **Lee el documento de análisis** en tu idioma preferido

2. **Review the current project structure**
   - **Revisa la estructura actual del proyecto**
   - `realtime_avatar.py` - Current implementation
   - `stream_pipeline_online.py` - Video generation pipeline
   - `gemini_realtime.py` - Audio processing

3. **Study LiveKit documentation**
   - **Estudia la documentación de LiveKit**
   - [LiveKit Agents](https://docs.livekit.io/agents/)
   - [Virtual Avatars](https://docs.livekit.io/agents/models/avatar/)

4. **Follow the implementation roadmap**
   - **Sigue el roadmap de implementación**
   - Phase 1: Basic Plugin
   - Phase 2: Optimization
   - Phase 3: Advanced Features
   - Phase 4: Production

---

## 📊 Key Concepts / Conceptos Clave

### Current Architecture / Arquitectura Actual
```
User → PyAudio → Gemini API → Ditto SDK → OpenCV
```

### Proposed LiveKit Architecture / Arquitectura Propuesta con LiveKit
```
User → WebRTC → LiveKit Room → AgentSession → AvatarSession → Ditto SDK
```

---

## 🔗 Related Resources / Recursos Relacionados

### LiveKit
- [Official Documentation](https://docs.livekit.io/)
- [Python Agents SDK](https://github.com/livekit/agents)
- [Avatar Plugin Examples](https://github.com/livekit-examples/python-agents-examples/tree/main/complex-agents/avatars)

### Ditto TalkingHead
- [GitHub Repository](https://github.com/antgroup/ditto-talkinghead)
- [Research Paper](https://arxiv.org/abs/2411.19509)
- [HuggingFace Models](https://huggingface.co/digital-avatar/ditto-talkinghead)

---

## 📝 Contributing / Contribuir

If you find issues or have suggestions for improving this documentation:
- Open an issue in the project repository
- Submit a pull request with improvements
- Contact the development team

Si encuentras problemas o tienes sugerencias para mejorar esta documentación:
- Abre un issue en el repositorio del proyecto
- Envía un pull request con mejoras
- Contacta al equipo de desarrollo

---

## 📅 Last Updated / Última Actualización

**Date / Fecha**: February 13, 2026

**Version / Versión**: 1.0.0

**Based on / Basado en**:
- Ditto TalkingHead v0.4.0
- LiveKit Agents v0.12.0
- Python 3.10

---

## 📧 Contact / Contacto

For questions or support regarding this documentation:
- Review the main project README
- Check LiveKit community forums
- Consult the official documentation

Para preguntas o soporte sobre esta documentación:
- Revisa el README principal del proyecto
- Consulta los foros de la comunidad LiveKit
- Consulta la documentación oficial
