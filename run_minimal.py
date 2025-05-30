"""
Script mínimo para ejecutar la aplicación MotoMatch
"""
import os
import sys
import logging
from flask import Flask

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agregar la ruta del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def create_minimal_app():
    """Crear una aplicación Flask mínima"""
    app = Flask(__name__, 
                template_folder='app/templates',
                static_folder='app/static')
    
    # Configuración básica
    app.secret_key = 'clave-super-secreta'
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    
    # Neo4j config (opcional)
    app.config['NEO4J_CONFIG'] = {
        'uri': 'bolt://localhost:7687',
        'user': 'neo4j',
        'password': '22446688'
    }
    
    # Desactivar datos mock
    app.config['USE_MOCK_DATA'] = False
    
    # Registrar rutas básicas
    try:
        from app.routes_fixed import fixed_routes
        app.register_blueprint(fixed_routes)
        logger.info("Rutas básicas registradas")
    except ImportError as e:
        logger.warning(f"No se pudieron cargar las rutas: {e}")
        
        # Crear una ruta básica de fallback
        @app.route('/')
        def home():
            return "<h1>MotoMatch</h1><p>Aplicación iniciada en modo mínimo</p>"
    
    return app

def main():
    """Función principal"""
    logger.info("Iniciando MotoMatch en modo mínimo...")
    
    app = create_minimal_app()
    
    return app

def run_server(app=None, suppress_warnings=False):
    """Ejecutar el servidor Flask"""
    if app is None:
        app = main()
    
    if suppress_warnings:
        import warnings
        warnings.filterwarnings('ignore', message='This is a development server.*')
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
    except KeyboardInterrupt:
        logger.info("Servidor detenido por el usuario")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--no-warnings":
        app = main()
        if app:
            run_server(app, suppress_warnings=True)
    else:
        app = main()
        if app:
            run_server(app, suppress_warnings=False)
