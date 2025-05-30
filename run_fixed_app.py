"""
Script para ejecutar la aplicación
"""
import os
import sys
import logging
import traceback
from flask import Flask, render_template, session, render_template_string, redirect, url_for, jsonify, request
from neo4j import GraphDatabase

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agregar la ruta del proyecto al path para importaciones
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def main():
    """Función principal para ejecutar la aplicación"""
    logger.info("Iniciando aplicación MotoMatch simplificada...")
    
    # Crear aplicación Flask básica
    app = Flask(__name__, 
                template_folder='app/templates',
                static_folder='app/static')
    
    # Configuración básica
    app.secret_key = 'clave-super-secreta'
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    
    # Configurar Neo4j (opcional)
    app.config['NEO4J_CONFIG'] = {
        'uri': 'bolt://localhost:7687',
        'user': 'neo4j',
        'password': '22446688'
    }
    
    # Configuración de sesión
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600
    
    # Context processor para fix de URLs
    @app.context_processor
    def inject_url_prefix():
        def url_for_with_prefix(endpoint, **kwargs):
            if '.' not in endpoint and endpoint != 'static':
                endpoint = 'main.' + endpoint
            return url_for(endpoint, **kwargs)
        return dict(url_for=url_for_with_prefix)
    
    # Registrar rutas básicas
    try:
        from app.routes_fixed import fixed_routes
        app.register_blueprint(fixed_routes)
        logger.info("✅ Rutas básicas registradas")
    except ImportError as e:
        logger.warning(f"No se pudieron cargar las rutas: {e}")
        
        # Crear ruta básica de fallback
        @app.route('/')
        def home():
            return "<h1>MotoMatch</h1><p>Aplicación iniciada en modo simplificado</p>"
    
    # Intentar crear adaptador simplificado (opcional)
    try:
        from app.adapter_factory_simple import create_adapter
        adapter = create_adapter(app, use_mock_data=True)
        app.config['MOTO_RECOMMENDER'] = adapter
        logger.info("✅ Adaptador simplificado creado")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo crear adaptador: {str(e)}")
        app.config['MOTO_RECOMMENDER'] = None
    
    logger.info("✅ Aplicación MotoMatch iniciada en modo simplificado")
    return app

def run_server(app=None, suppress_warnings=False):
    """Ejecutar el servidor Flask con opciones de configuración"""
    if app is None:
        app = main()
    
    if suppress_warnings:
        # Suprimir advertencias del servidor de desarrollo
        import warnings
        warnings.filterwarnings('ignore', message='This is a development server.*')
        warnings.filterwarnings('ignore', message='.*WARNING.*development server.*')
        
        # Configurar logging de Werkzeug para suprimir advertencias
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.ERROR)
        
        logger.info("🌐 Servidor iniciado SIN advertencias en http://localhost:5000")
    else:
        logger.info("🌐 Servidor iniciado en http://localhost:5000")
    
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True,
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"Error al iniciar el servidor: {str(e)}")
        print(f"\n❌ Error al iniciar el servidor Flask: {str(e)}")
        print("Verifica que el puerto 5000 no esté siendo usado por otra aplicación.")
        print("Puedes cambiar el puerto modificando el valor en app.run(port=XXXX)")
    except KeyboardInterrupt:
        logger.info("Servidor detenido por el usuario")
        print("\n✅ Servidor detenido correctamente")

def run_production_server():
    """Ejecutar el servidor en modo producción usando Waitress"""
    try:
        import waitress
        app = main()
        if app:
            logger.info("🚀 Iniciando servidor de producción con Waitress en http://0.0.0.0:5000")
            waitress.serve(app, host='0.0.0.0', port=5000)
    except ImportError:
        logger.warning("⚠️ Waitress no está instalado. Para usar un servidor de producción ejecute:")
        logger.warning("   pip install waitress")
        # Fallback to development server
        run_server(main(), suppress_warnings=True)

# Modify your if __name__ == "__main__" block:
if __name__ == "__main__":
    import sys
    
    # Check for production mode
    if len(sys.argv) > 1 and sys.argv[1] == "--production":
        run_production_server()
    elif len(sys.argv) > 1 and sys.argv[1] == "--no-warnings":
        app = main()
        if app:
            run_server(app, suppress_warnings=True)
    else:
        # Original behavior
        app = main()
        if app:
            run_server(app, suppress_warnings=False)