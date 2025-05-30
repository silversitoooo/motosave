"""
Simplified factory for creating the recommendation adapter
"""
import logging

# Configurar logging
logger = logging.getLogger(__name__)

def create_adapter(app=None, use_mock_data=False):
    """
    Crea un adaptador simplificado para la aplicación.
    
    Args:
        app: Aplicación Flask (opcional)
        use_mock_data: Si es True, usa datos simulados
        
    Returns:
        None (simplified version)
    """
    try:
        # Por ahora solo crear un objeto mock básico
        class SimpleAdapter:
            def __init__(self):
                self.use_mock_data = True
                self.driver = None
                self.logger = logger
                
            def connect_to_neo4j(self):
                return False
                
            def load_data(self):
                return True
        
        adapter = SimpleAdapter()
        if app:
            app.logger.info("Adaptador simplificado creado")
        return adapter
        
    except Exception as e:
        if app:
            app.logger.error(f"Error creating simple adapter: {str(e)}")
        return None
