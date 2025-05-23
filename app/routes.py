import logging
import traceback
import time
import random
from flask import Blueprint, render_template, request, redirect, url_for, session, json, jsonify, current_app, flash, g

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MotoMatch.Routes")

main = Blueprint('main', __name__, template_folder='templates')

# El adaptador ahora se obtiene de app.config
def get_adapter():
    return current_app.config.get('MOTO_RECOMMENDER')

# Simulación de base de datos
motos_populares = [
    {"modelo": "CBR 600RR", "marca": "Honda", "precio": 75000, "estilo": "Deportiva", "likes": 22, "imagen":"https://img.remediosdigitales.com/2fe8cb/honda-cbr600rr-2021-5-/1366_2000.jpeg"},
    {"modelo": "Duke 390", "marca": "KTM", "precio": 46000, "estilo": "Naked", "likes": 18, "imagen":"https://www.ktm.com/ktmgroup-storage/PHO_BIKE_90_RE_390-Duke-orange-MY22-Front-Right-49599.png"},
    {"modelo": "V-Strom 650", "marca": "Suzuki", "precio": 68000, "estilo": "Adventure", "likes": 25, "imagen":"https://suzukicycles.com/content/dam/public/SuzukiCycles/Models/Bikes/Adventure/2023/DL650XAM3_YU1_RIGHT.png"},
    {"modelo": "R nineT", "marca": "BMW", "precio": 115000, "estilo": "Clásica", "likes": 30, "imagen": "https://cdp.azureedge.net/products/USA/BM/2023/MC/STANDARD/R_NINE_T/50/BLACKSTORM_METALLIC-BRUSHED_ALUMINUM/2000000001.jpg"}
]

usuarios = {
    'admin': 'admin123',
    'maria': 'clave',
    'pedro': '1234'
}

amigos_por_usuario = {
    'admin': ['maria']
}

likes_por_usuario = {
    'maria': 'Yamaha R3',
    'pedro': 'Ducati Monster',
    'admin': 'Suzuki GSX-R750'
}

# Almacena las motos ideales por usuario
motos_ideales = {
    'admin': {"modelo": "Ninja ZX-10R", "marca": "Kawasaki", "precio": 92000, "estilo": "Deportiva", "imagen": "https://www.motofichas.com/images/phocagallery/Kawasaki/ninja-zx-10r-2021/01-kawasaki-ninja-zx-10r-2024-performance-estudio-verde.jpg", "descripcion": "Alta velocidad, deportiva de competición."}
}

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/recomendaciones')
def recomendaciones():
    """Muestra recomendaciones personalizadas basadas en los datos del test."""
    if 'username' not in session:
        return redirect(url_for('main.login'))
    
    username = session.get('username')
    user_id = username  # Using username as user_id
    
    # Obtener datos del test de la sesión
    test_data = session.get('test_data', {})
    motos_recomendadas = []
    
    if not test_data:
        flash("No hay datos de test disponibles. Por favor completa el test primero.", "warning")
        return redirect(url_for('main.test'))
    
    try:
        # Obtener el adaptador de recomendación
        adapter = current_app.config.get('MOTO_RECOMMENDER')
        
        if not adapter:
            flash("Sistema de recomendación no disponible", "error")
            logger.error("Adaptador de recomendaciones no disponible")
            return render_template('recomendaciones.html', motos_recomendadas=[])
        
        # Log detailed info about what we're sending to the adapter
        logger.info(f"Generando recomendaciones para {username} usando adaptador {type(adapter).__name__}")
        logger.info(f"Datos del test: {test_data}")
        
        # Obtener recomendaciones basadas en los datos del test - LIMITADO A TOP 4
        recommendations = adapter.get_recommendations(
            user_id=user_id,
            algorithm='hybrid', 
            top_n=4,
            user_preferences=test_data
        )
        
        # Verificar si hubo problemas con las recomendaciones
        if not recommendations:
            logger.warning(f"El adaptador no generó recomendaciones para {username}")
            flash("No se pudieron generar recomendaciones. Por favor, intenta de nuevo.", "warning")
            return render_template('recomendaciones.html', motos_recomendadas=[])
        
        # Procesar las recomendaciones para la plantilla
        logger.info(f"Obtenidas {len(recommendations)} recomendaciones del adaptador")
        
        for moto_info in recommendations:
            if isinstance(moto_info, tuple) and len(moto_info) >= 2:
                moto_id, score = moto_info[0], moto_info[1]
                reasons = moto_info[2] if len(moto_info) > 2 else []
                
                try:
                    # Buscar datos completos de la moto con manejo de errores
                    moto_data = None
                    if hasattr(adapter, 'get_moto_by_id'):
                        moto_data = adapter.get_moto_by_id(moto_id)
                    elif hasattr(adapter, 'motos_df') and adapter.motos_df is not None:
                        moto_rows = adapter.motos_df[adapter.motos_df['moto_id'] == moto_id]
                        if not moto_rows.empty:
                            moto_data = moto_rows.iloc[0].to_dict()
                    
                    # Si no se encontraron datos, crear un objeto mínimo
                    if not moto_data:
                        logger.warning(f"No se encontraron datos para la moto {moto_id}, usando valores por defecto")
                        moto_data = {
                            'moto_id': moto_id,
                            'marca': 'Desconocida',
                            'modelo': f'Moto {moto_id}',
                            'tipo': 'standard',
                            'cilindrada': 0,
                            'potencia': 0,
                            'precio': 0,
                            'imagen': '/static/images/default-moto.jpg'
                        }
                    
                    # Asegurar que todos los campos necesarios existan
                    moto_recomendada = {
                        'moto_id': moto_id,
                        'marca': moto_data.get('marca', 'Desconocida'),
                        'modelo': moto_data.get('modelo', f"Moto {moto_id}"),
                        'tipo': moto_data.get('tipo', 'Estándar'),
                        'estilo': moto_data.get('tipo', 'Estándar'),
                        'cilindrada': moto_data.get('cilindrada', 0),
                        'potencia': moto_data.get('potencia', 0),
                        'precio': moto_data.get('precio', 0),
                        'imagen': moto_data.get('imagen', '/static/images/default-moto.jpg'),
                        'anio': moto_data.get('anio', 'N/D'),
                        'score': float(score),
                        'reasons': reasons
                    }
                    motos_recomendadas.append(moto_recomendada)
                except Exception as e:
                    logger.error(f"Error al procesar la moto {moto_id}: {str(e)}")
                    # Continuar con la siguiente moto en lugar de fallar completamente
        
        # Registrar información sobre las recomendaciones generadas
        logger.info(f"Generadas {len(motos_recomendadas)} recomendaciones para {username} basadas en test")
        
        # Asegurarse de pasar la lista de motos a la plantilla, incluso si está vacía
        return render_template('recomendaciones.html', 
                              motos_recomendadas=motos_recomendadas,
                              test_data=test_data)
                              
    except Exception as e:
        logger.error(f"Error al generar recomendaciones: {str(e)}")
        logger.error(traceback.format_exc())
        flash("Ocurrió un error al generar tus recomendaciones.", "error")
        # No redirigir al dashboard, mostrar la página de error en recomendaciones
        return render_template('recomendaciones.html', 
                              motos_recomendadas=[],
                              error=str(e))

@main.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión."""
    # Si ya hay sesión activa, ir directo al dashboard
    if 'username' in session:
        logger.info(f"Sesión activa detectada para {session['username']}, redirigiendo a dashboard")
        return redirect(url_for('main.dashboard'))
    
    error = None
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        logger.info(f"Intento de login para usuario: {username}")
        
        if not username or not password:
            error = 'Por favor, ingresa un nombre de usuario y contraseña.'
            return render_template('login.html', error=error)
        
        # Usuarios de prueba para desarrollo
        development_users = {
            'admin': 'admin',
            'user': 'user',
            'test': 'test'
        }
        
        # Verificar primero en usuarios de desarrollo
        if username in development_users and password == development_users[username]:
            logger.info(f"Login exitoso para usuario de desarrollo: {username}")
            session['username'] = username
            session['user_id'] = username  # Usar username como ID para simplificar
            session.permanent = True  # Hacer la sesión permanente
            return redirect(url_for('main.dashboard'))
        
        # Si no es usuario de desarrollo, intentar verificar en Neo4j
        adapter = current_app.config.get('MOTO_RECOMMENDER')
        
        if adapter and hasattr(adapter, 'users_df') and adapter.users_df is not None:
            try:
                # Verificar usuario en el dataframe de usuarios
                user_rows = adapter.users_df[adapter.users_df['username'] == username]
                
                if not user_rows.empty:
                    # Verificar contraseña (en desarrollo, sin hash)
                    if 'password' in user_rows.columns and user_rows.iloc[0]['password'] == password:
                        user_id = user_rows.iloc[0].get('user_id', username)
                        session['username'] = username
                        session['user_id'] = user_id
                        session.permanent = True
                        logger.info(f"Login exitoso para usuario de base de datos: {username}")
                        return redirect(url_for('main.dashboard'))
            except Exception as e:
                logger.error(f"Error al verificar usuario en Neo4j: {str(e)}")
                logger.error(traceback.format_exc())
        
        error = 'Usuario o contraseña incorrectos'
    
    return render_template('login.html', error=error)

@main.route('/logout')
def logout():
    """Cierra la sesión del usuario"""
    # Guardamos el nombre para logging
    username = session.get('username', 'Usuario desconocido')
    
    # Limpiar completamente la sesión
    session.clear()
    
    logger.info(f"Sesión cerrada para usuario: {username}")
    return redirect(url_for('main.home'))

@main.route('/dashboard')
def dashboard():
    """Página principal después de iniciar sesión"""
    if 'username' not in session:
        return redirect(url_for('main.login'))
    
    username = session.get('username', 'Usuario')
    return render_template('dashboard.html', username=username)

@main.route('/friends')
def friends():
    username = session.get('username')
    if not username:
        return redirect(url_for('main.login'))
    # Simular estructura de amigos y sugerencias
    amigos = amigos_por_usuario.get(username, [])
    sugerencias = [u for u in usuarios.keys() if u != username and u not in amigos]
    # Datos de likes por usuario para mostrar en el popup
    motos_likes = likes_por_usuario
    return render_template('friends.html',
                          amigos=amigos,
                          sugerencias=sugerencias,
                          motos_likes=motos_likes)

@main.route('/agregar_amigo', methods=['POST'])
def agregar_amigo():
    username = session.get('username')
    nuevo_amigo = request.form.get('amigo')
    if username and nuevo_amigo and nuevo_amigo != username:
        amigos_por_usuario.setdefault(username, []).append(nuevo_amigo)
    return redirect(url_for('main.friends'))

@main.route('/eliminar_amigo', methods=['POST'])
def eliminar_amigo():
    username = session.get('username')
    amigo_a_eliminar = request.form.get('amigo')
    if username and amigo_a_eliminar and amigo_a_eliminar in amigos_por_usuario.get(username, []):
        amigos_por_usuario[username].remove(amigo_a_eliminar)
    return redirect(url_for('main.friends'))

@main.route('/populares')
def populares():
    import random
    # Obtener parámetro de recarga
    should_shuffle = request.args.get('shuffle', 'false') == 'true'
    
    # Intentar obtener motos populares de la base de datos
    motos_db = get_populares_motos(top_n=8)
    
    # Si hay motos en la base de datos, usarlas
    if motos_db:
        motos_lista = motos_db
    else:
        # Si no hay motos en la base de datos, usar datos simulados
        motos_lista = motos_populares.copy()
    
    # Aleatorizar el orden si se solicitó (cuando se usa el botón de recarga)
    if should_shuffle:
        random.shuffle(motos_lista)
    
    # Asegurarnos de enviar exactamente 4 motos
    motos_para_mostrar = motos_lista[:4]
    return render_template('populares.html', motos_populares=motos_para_mostrar)

@main.route('/test')
def test_preferencias():
    """Página de test para recopilar preferencias del usuario."""
    username = session.get('username')
    if not username:
        return redirect(url_for('main.login'))
    
    # Limpiar cualquier dato anterior del test en la sesión
    if 'test_data' in session:
        session.pop('test_data')
    
    # Pasar timestamp para evitar caché del navegador y datos estáticos
    import time, json
    timestamp = int(time.time())
    
    # Datos estáticos para el test
    estilos = ["Deportiva", "Naked", "Adventure", "Cruiser", "Touring", 
              "Scooter", "Custom", "Trail", "Enduro", "Clásica"]
    
    marcas = ["Honda", "Yamaha", "Kawasaki", "Suzuki", "BMW", "KTM", 
             "Ducati", "Triumph", "Harley-Davidson", "Royal Enfield", 
             "Aprilia", "Vespa", "Moto Guzzi", "Indian", "Husqvarna"]
    
    return render_template('test.html', 
                          cache_bust=timestamp,
                          estilos_json=json.dumps(estilos),
                          marcas_json=json.dumps(marcas))

@main.route('/recomendaciones_test', methods=['GET', 'POST'])
def recomendaciones_test():
    username = session.get('username')
    if not username:
        return redirect(url_for('main.login'))
    
    # Inicializar variables
    test_data = {}  # Inicializar test_data como diccionario vacío
    
    if request.method == 'POST':
        # Capturar datos del formulario
        test_data = {
            'experiencia': request.form.get('experiencia', 'principiante'),
            'presupuesto': request.form.get('presupuesto', '8000'),
            'uso': request.form.get('uso', 'urbano')
        }
        
        # Log para depuración
        logger.info(f"Datos del test de {username}: {test_data}")
        
        try:
            # Guardar preferencias usando la función de utils
            success = store_user_test_results(username, test_data)
            
            if success:
                logger.info(f"Preferencias guardadas correctamente para {username}")
                # flash solo funciona si has configurado app.secret_key
                if hasattr(current_app, 'secret_key'):
                    flash("Test completado. Aquí están tus recomendaciones personalizadas.", "success")
                # Redirigir a la página moto_ideal
                return redirect(url_for('main.moto_ideal'))
            else:
                logger.warning(f"Error al guardar preferencias para {username}")
                if hasattr(current_app, 'secret_key'):
                    flash("Hubo un problema al procesar tus preferencias.", "warning")
        except Exception as e:
            logger.error(f"Error al procesar el test: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    # Si no se recibieron datos del POST o hubo un error, redirigir al test
    return redirect(url_for('main.test_preferencias'))

@main.route('/like_moto', methods=['POST'])
def like_moto():
    """Ruta para registrar un like a una moto"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Debes iniciar sesión para dar like'})
    
    data = request.get_json()
    
    if not data or 'moto_id' not in data:
        return jsonify({'success': False, 'message': 'Datos incompletos'})
    
    moto_id = data['moto_id']
    
    # Obtener el adaptador
    adapter = current_app.config.get('MOTO_RECOMMENDER')
    if not adapter:
        return jsonify({'success': False, 'message': 'Error del servidor: adaptador no disponible'})
    
    try:
        # Registrar el like usando el adaptador
        success, likes_count = adapter.register_like(current_user.id, moto_id)
        
        if success:
            return jsonify({'success': True, 'likes': likes_count})
        else:
            return jsonify({'success': False, 'message': 'No se pudo registrar el like'})
            
    except Exception as e:
        app.logger.error(f"Error al registrar like: {str(e)}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'})

@main.route('/set_ideal_moto', methods=['POST'])
def set_ideal_moto():
    """Ruta para establecer una moto como la ideal para el usuario"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Debes iniciar sesión para guardar tu moto ideal'})
    
    data = request.get_json()
    
    if not data or 'moto_id' not in data:
        return jsonify({'success': False, 'message': 'Datos incompletos'})
    
    username = session.get('username')
    moto_id = data['moto_id']
    
    # Obtener el adaptador
    adapter = current_app.config.get('MOTO_RECOMMENDER')
    if not adapter:
        return jsonify({'success': False, 'message': 'Error del servidor: adaptador no disponible'})
    
    try:        # Registrar la moto como ideal para el usuario
        success = adapter.set_ideal_moto(username, moto_id)
        
        # Obtener los detalles de la moto
        moto_detail = None
        try:
            moto_detail = adapter.get_moto_by_id(moto_id)
        except Exception as e:
            logger.error(f"Error al obtener detalles de la moto {moto_id}: {str(e)}")
        
        # Guardar también en la sesión para acceso rápido
        session['ideal_moto_id'] = moto_id
        
        if success:# Respuesta con datos de la moto para mostrar en notificación
            response_data = {
                'success': True,
                'message': 'Moto ideal guardada correctamente',
                'moto_id': moto_id
            }
            
            # Añadir detalles si están disponibles
            if moto_detail:
                marca = moto_detail.get('marca', 'Marca desconocida')
                modelo = moto_detail.get('modelo', 'Modelo desconocido')
                response_data.update({
                    'marca': marca,
                    'modelo': modelo,
                    'message': f'¡{marca} {modelo} guardada como tu moto ideal!'
                })
            
            # Registrar también en la variable global motos_ideales
            if username not in motos_ideales and moto_detail:
                motos_ideales[username] = {
                    "modelo": moto_detail.get('modelo', 'Modelo desconocido'),
                    "marca": moto_detail.get('marca', 'Marca desconocida'),
                    "precio": moto_detail.get('precio', 0),
                    "estilo": moto_detail.get('tipo', moto_detail.get('estilo', 'Estilo desconocido')),
                    "imagen": moto_detail.get('imagen', '/static/images/default-moto.jpg'),
                    "descripcion": "Seleccionada como tu moto ideal"
                }
            
            logger.info(f"Usuario {username} guardó como ideal la moto {moto_id}")
            return jsonify(response_data)
        else:
            logger.warning(f"Error al guardar moto ideal {moto_id} para usuario {username}")
            return jsonify({'success': False, 'message': 'No se pudo guardar la moto ideal'})
    except Exception as e:
        logger.error(f"Error al establecer moto ideal: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'})

@main.route('/moto_ideal', methods=['GET', 'POST'])
def moto_ideal():
    """Página de moto ideal con soporte para GET y POST"""
    if 'username' not in session:
        flash('Debes iniciar sesión para ver tu moto ideal', 'warning')
        return redirect(url_for('main.login'))
    
    username = session.get('username')
    
    # Si es POST, procesar datos y luego redirigir
    if request.method == 'POST':
        # Procesar los datos del formulario
        test_data = {
            'experiencia': request.form.get('experiencia', 'principiante'),
            'presupuesto': request.form.get('presupuesto', '8000'),
            'uso': request.form.get('uso', ''),
            'reset_recommendation': request.form.get('reset_recommendation', 'true')
        }
        
        logger.info(f"Datos del test recibidos en moto_ideal: {test_data}")
        
        # Guardar datos
        try:
            from app.utils import store_user_test_results
            success = store_user_test_results(username, test_data)
            
            if success:
                flash("Preferencias guardadas correctamente", "success")
            else:
                flash("No se pudieron guardar las preferencias", "warning")
                
        except Exception as e:
            logger.error(f"Error al guardar preferencias: {str(e)}")
            flash(f"Error al guardar preferencias: {str(e)}", "error")
        
        # Redirigir a la versión GET con reset
        return redirect(url_for('main.moto_ideal', reset='true'))
    
    # Si es GET, mostrar la moto ideal del usuario
    try:
        # Verificar si se solicitó reset (desde el test)
        reset_requested = request.args.get('reset') == 'true'
        
        # Intentar obtener el ID de la moto ideal desde la sesión o la base de datos
        moto_id = session.get('ideal_moto_id')
        
        # Obtener el adaptador
        adapter = current_app.config.get('MOTO_RECOMMENDER')
        
        # Obtener datos de la moto ideal si está disponible
        moto_data = None
        
        if adapter and moto_id:
            try:
                if hasattr(adapter, 'get_moto_by_id'):
                    moto_data = adapter.get_moto_by_id(moto_id)
            except Exception as e:
                logger.error(f"Error al obtener moto ideal: {str(e)}")
        
        # Si tenemos datos de la moto, mostrarlos
        if moto_data:
            return render_template('moto_ideal.html', moto=moto_data)
        
        # Si no hay moto ideal o hay reset, intentar obtener recomendaciones
        if reset_requested or not moto_id:
            try:
                from app.utils import get_moto_ideal
                recomendaciones = get_moto_ideal(username, force_random=reset_requested)
                
                # Si hay recomendaciones, mostrar la primera
                if recomendaciones and len(recomendaciones) > 0:
                    return render_template('moto_ideal.html', moto=recomendaciones[0])
            except Exception as e:
                logger.error(f"Error al obtener recomendaciones: {str(e)}")
        
        # Obtener listas de marcas y estilos disponibles
        marcas = ["Honda", "Yamaha", "Kawasaki", "Suzuki"]
        estilos = ["Naked", "Deportiva", "Adventure", "Scooter"]
        
        if adapter and hasattr(adapter, 'motos_df') and adapter.motos_df is not None:
            try:
                marcas = adapter.motos_df['marca'].unique().tolist()
                estilos = adapter.motos_df['tipo'].unique().tolist()
            except Exception:
                pass
        
        # Mostrar mensaje si no hay moto ideal
        return render_template('moto_ideal.html',
                              error="No se pudo generar una recomendación personalizada. ¡Completa el test!",
                              marcas=marcas,
                              estilos=estilos)
                              
    except Exception as e:
        logger.error(f"Error al mostrar moto ideal: {str(e)}")
        logger.error(traceback.format_exc())
        
        return render_template('moto_ideal.html',
                              error="Ocurrió un error al procesar tu recomendación. Inténtalo de nuevo.",
                              marcas=["Honda", "Yamaha", "Kawasaki", "Suzuki"],
                              estilos=["Naked", "Deportiva", "Adventure", "Scooter"])

@main.route('/guardar-preferencias', methods=['POST'])
def guardar_preferencias():
    """
    Guarda las preferencias del usuario en la base de datos.
    Esta ruta recibe datos de preferencias de motos (estilos, marcas, etc.)
    y los almacena en Neo4j para usarlos en futuras recomendaciones.
    """
    username = session.get('username')
    if not username:
        return jsonify({"success": False, "message": "Usuario no autenticado"}), 401
    
    try:
        # Obtener datos del formulario
        preferences = {
            'estilos': {},
            'marcas': {},
            'experiencia': request.form.get('experiencia', 'Intermedio')
        }
        
        # Procesar estilos
        estilos_str = request.form.get('estilos', '{}')
        try:
            preferences['estilos'] = json.loads(estilos_str.replace("'", '"'))
        except:
            current_app.logger.error("Error al procesar JSON de estilos")
            
        # Procesar marcas
        marcas_str = request.form.get('marcas', '{}')
        try:
            preferences['marcas'] = json.loads(marcas_str.replace("'", '"'))
        except:
            current_app.logger.error("Error al procesar JSON de marcas")
        
        # Guardar en la sesión
        session['test_data'] = preferences
        
        # Guardar en Neo4j usando la función mejorada
        result = store_user_test_results(username, preferences)
        
        if result:
            current_app.logger.info(f"Preferencias guardadas correctamente para {username}")
            return jsonify({"success": True, "message": "Preferencias guardadas correctamente"})
        else:
            current_app.logger.warning(f"No se pudieron guardar las preferencias para {username}")
            return jsonify({"success": False, "message": "No se pudieron guardar las preferencias en la base de datos"}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error al guardar preferencias: {str(e)}")
        return jsonify({"success": False, "message": f"Error al procesar la solicitud: {str(e)}"}), 500

@main.route('/recomendaciones-amigos')
def recomendaciones_amigos():
    """
    Muestra recomendaciones de motos basadas en los gustos de los amigos del usuario.
    Utiliza el algoritmo de propagación de etiquetas para generar recomendaciones.
    """
    username = session.get('username')
    if not username:
        return redirect(url_for('main.login'))
    
    try:
        # Obtener recomendaciones basadas en amigos
        friend_recommendations = get_friend_recommendations(username, top_n=4)
        
        if not friend_recommendations:
            # Si no hay recomendaciones de la base de datos, usar datos simulados
            friend_recommendations = [
                {"modelo": "R3", "marca": "Yamaha", "precio": 48000, "estilo": "Deportiva", 
                 "imagen": "https://yamaha-motor.com.ar/uploads/product_images/R3.png",
                 "score": 0.85, "amigo": "maria"},
                {"modelo": "Monster", "marca": "Ducati", "precio": 89000, "estilo": "Naked", 
                 "imagen": "https://www.motofichas.com/images/phocagallery/Ducati/monster-2021/01-ducati-monster-2021-estudio-rojo.jpg",
                 "score": 0.78, "amigo": "pedro"},
                {"modelo": "Street Triple", "marca": "Triumph", "precio": 85000, "estilo": "Naked", 
                 "imagen": "https://www.motofichas.com/images/phocagallery/Triumph/street-triple-765-rs-2023/01-triumph-street-triple-765-rs-2023-estudio-gris.jpg",
                 "score": 0.72, "amigo": "jose"},
                {"modelo": "Z900", "marca": "Kawasaki", "precio": 82000, "estilo": "Naked", 
                 "imagen": "https://www.motofichas.com/images/phocagallery/Kawasaki/z900-2023/01-kawasaki-z900-2023-estudio-verde.jpg",
                 "score": 0.65, "amigo": "maria"}
            ]
        
        return render_template('recomendaciones_amigos.html', 
                              recomendaciones=friend_recommendations,
                              username=username)
    
    except Exception as e:
        current_app.logger.error(f"Error al obtener recomendaciones de amigos: {str(e)}")
        # En caso de error, mostrar un mensaje
        return render_template('error.html', 
                              error="No se pudieron cargar las recomendaciones basadas en amigos",
                              username=username)

@main.route('/recomendador')
def recomendador():
    """
    Ruta para mostrar recomendaciones usando el nuevo sistema corregido,
    con fallback al sistema antiguo en caso de error.
    """
    # Verificar si el usuario está logueado
    if 'username' not in session:
        return redirect(url_for('main.login'))
    
    usuario = session.get('username')
    
    try:
        # Usar el nuevo sistema de recomendaciones corregido
        logger.info(f"Generando recomendaciones para {usuario} con el sistema corregido")
        recomendaciones = get_recommendations_for_user(current_app, usuario, top_n=5)
        motos_recomendadas = format_recommendations_for_display(recomendaciones)
        
        # Si no hay recomendaciones, usar el método alternativo
        if not motos_recomendadas:
            logger.warning(f"Sin recomendaciones del nuevo sistema para {usuario}, usando alternativo")
            # Usar el sistema antiguo como fallback
            recomendaciones = get_moto_ideal(usuario, top_n=5)
            motos_recomendadas = []
            for moto in recomendaciones:
                motos_recomendadas.append({
                    'id': moto.get('moto_id', ''),
                    'modelo': moto.get('modelo', f"Moto {moto.get('moto_id')}"),
                    'marca': moto.get('marca', 'Desconocida'),
                    'estilo': moto.get('tipo', 'Estándar'),
                    'precio': moto.get('precio', 0),
                    'imagen': moto.get('imagen', 'https://www.motofichas.com/images/phocagallery/Kawasaki/ninja-zx-10r-2021/01-kawasaki-ninja-zx-10r-2024-performance-estudio-verde.jpg'),
                    'score': moto.get('score', 0),
                    'razones': moto.get('reasons', [])
                })
        
        return render_template('recomendaciones.html', 
                               usuario=usuario,
                               motos_recomendadas=motos_recomendadas,
                               test_data={})
    except Exception as e:
        logger.error(f"Error en recomendador: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Mostrar página con mensaje de error
        return render_template('recomendaciones.html', 
                               usuario=usuario,
                               error="Hubo un problema al generar recomendaciones. Inténtalo más tarde.",
                               motos_recomendadas=[],
                               test_data={})

@main.route('/test_moto_ideal', methods=['GET', 'POST'])
def test_moto_ideal():
    """Página de test para encontrar la moto ideal y generar recomendaciones."""
    if 'username' not in session:
        return redirect(url_for('main.login'))
    
    username = session.get('username')
    user_id = session.get('user_id')
    
    # Si es POST, procesar formulario
    if request.method == 'POST':
        try:
            # Recopilar datos del formulario
            experiencia = request.form.get('experiencia', 'principiante')
            presupuesto = request.form.get('presupuesto', '8000')
            uso = request.form.get('uso', 'urbano')
            reset_recommendation = request.form.get('reset_recommendation', 'false') == 'true'
            
            # Crear diccionario de preferencias
            test_data = {
                'experiencia': experiencia,
                'presupuesto': presupuesto,
                'uso': uso,
                'reset': reset_recommendation
            }
            
            # Guardar en sesión
            session['test_data'] = test_data
            
            # Registrar datos
            current_app.logger.info(f"Test completado por {username}: {test_data}")
            
            # Enviar usuario a página de recomendaciones donde se usarán estos datos
            return redirect(url_for('main.recomendaciones'))
            
        except Exception as e:
            current_app.logger.error(f"Error al procesar test: {str(e)}")
            flash("Ocurrió un error al procesar tus respuestas. Por favor intenta nuevamente.", "error")
    
    # Si es GET, mostrar página de test
    return render_template('test_moto_ideal.html')

@main.route('/moto_ideal', methods=['GET', 'POST'])
def moto_ideal():
    """Página de moto ideal con soporte para GET y POST"""
    if 'username' not in session:
        flash('Debes iniciar sesión para ver tu moto ideal', 'warning')
        return redirect(url_for('main.login'))
    
    username = session.get('username')
    
    # Si es POST, procesar datos y luego redirigir
    if request.method == 'POST':
        # Procesar los datos del formulario
        test_data = {
            'experiencia': request.form.get('experiencia', 'principiante'),
            'presupuesto': request.form.get('presupuesto', '8000'),
            'uso': request.form.get('uso', ''),
            'reset_recommendation': request.form.get('reset_recommendation', 'true')
        }
        
        logger.info(f"Datos del test recibidos en moto_ideal: {test_data}")
        
        # Guardar datos
        try:
            from app.utils import store_user_test_results
            success = store_user_test_results(username, test_data)
            
            if success:
                flash("Preferencias guardadas correctamente", "success")
            else:
                flash("No se pudieron guardar las preferencias", "warning")
                
        except Exception as e:
            logger.error(f"Error al guardar preferencias: {str(e)}")
            flash(f"Error al guardar preferencias: {str(e)}", "error")
        
        # Redirigir a la versión GET con reset
        return redirect(url_for('main.moto_ideal', reset='true'))
    
    # Si es GET, mostrar la moto ideal del usuario
    try:
        # Verificar si se solicitó reset (desde el test)
        reset_requested = request.args.get('reset') == 'true'
        
        # Intentar obtener el ID de la moto ideal desde la sesión o la base de datos
        moto_id = session.get('ideal_moto_id')
        
        # Obtener el adaptador
        adapter = current_app.config.get('MOTO_RECOMMENDER')
        
        # Obtener datos de la moto ideal si está disponible
        moto_data = None
        
        if adapter and moto_id:
            try:
                if hasattr(adapter, 'get_moto_by_id'):
                    moto_data = adapter.get_moto_by_id(moto_id)
            except Exception as e:
                logger.error(f"Error al obtener moto ideal: {str(e)}")
        
        # Si tenemos datos de la moto, mostrarlos
        if moto_data:
            return render_template('moto_ideal.html', moto=moto_data)
        
        # Si no hay moto ideal o hay reset, intentar obtener recomendaciones
        if reset_requested or not moto_id:
            try:
                from app.utils import get_moto_ideal
                recomendaciones = get_moto_ideal(username, force_random=reset_requested)
                
                # Si hay recomendaciones, mostrar la primera
                if recomendaciones and len(recomendaciones) > 0:
                    return render_template('moto_ideal.html', moto=recomendaciones[0])
            except Exception as e:
                logger.error(f"Error al obtener recomendaciones: {str(e)}")
        
        # Obtener listas de marcas y estilos disponibles
        marcas = ["Honda", "Yamaha", "Kawasaki", "Suzuki"]
        estilos = ["Naked", "Deportiva", "Adventure", "Scooter"]
        
        if adapter and hasattr(adapter, 'motos_df') and adapter.motos_df is not None:
            try:
                marcas = adapter.motos_df['marca'].unique().tolist()
                estilos = adapter.motos_df['tipo'].unique().tolist()
            except Exception:
                pass
        
        # Mostrar mensaje si no hay moto ideal
        return render_template('moto_ideal.html',
                              error="No se pudo generar una recomendación personalizada. ¡Completa el test!",
                              marcas=marcas,
                              estilos=estilos)
                              
    except Exception as e:
        logger.error(f"Error al mostrar moto ideal: {str(e)}")
        logger.error(traceback.format_exc())
        
        return render_template('moto_ideal.html',
                              error="Ocurrió un error al procesar tu recomendación. Inténtalo de nuevo.",
                              marcas=["Honda", "Yamaha", "Kawasaki", "Suzuki"],
                              estilos=["Naked", "Deportiva", "Adventure", "Scooter"])

@main.route('/guardar-preferencias', methods=['POST'])
def guardar_preferencias():
    """
    Guarda las preferencias del usuario en la base de datos.
    Esta ruta recibe datos de preferencias de motos (estilos, marcas, etc.)
    y los almacena en Neo4j para usarlos en futuras recomendaciones.
    """
    username = session.get('username')
    if not username:
        return jsonify({"success": False, "message": "Usuario no autenticado"}), 401
    
    try:
        # Obtener datos del formulario
        preferences = {
            'estilos': {},
            'marcas': {},
            'experiencia': request.form.get('experiencia', 'Intermedio')
        }
        
        # Procesar estilos
        estilos_str = request.form.get('estilos', '{}')
        try:
            preferences['estilos'] = json.loads(estilos_str.replace("'", '"'))
        except:
            current_app.logger.error("Error al procesar JSON de estilos")
            
        # Procesar marcas
        marcas_str = request.form.get('marcas', '{}')
        try:
            preferences['marcas'] = json.loads(marcas_str.replace("'", '"'))
        except:
            current_app.logger.error("Error al procesar JSON de marcas")
        
        # Guardar en la sesión
        session['test_data'] = preferences
        
        # Guardar en Neo4j usando la función mejorada
        result = store_user_test_results(username, preferences)
        
        if result:
            current_app.logger.info(f"Preferencias guardadas correctamente para {username}")
            return jsonify({"success": True, "message": "Preferencias guardadas correctamente"})
        else:
            current_app.logger.warning(f"No se pudieron guardar las preferencias para {username}")
            return jsonify({"success": False, "message": "No se pudieron guardar las preferencias en la base de datos"}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error al guardar preferencias: {str(e)}")
        return jsonify({"success": False, "message": f"Error al procesar la solicitud: {str(e)}"}), 500

@main.route('/recomendaciones-amigos')
def recomendaciones_amigos():
    """
    Muestra recomendaciones de motos basadas en los gustos de los amigos del usuario.
    Utiliza el algoritmo de propagación de etiquetas para generar recomendaciones.
    """
    username = session.get('username')
    if not username:
        return redirect(url_for('main.login'))
    
    try:
        # Obtener recomendaciones basadas en amigos
        friend_recommendations = get_friend_recommendations(username, top_n=4)
        
        if not friend_recommendations:
            # Si no hay recomendaciones de la base de datos, usar datos simulados
            friend_recommendations = [
                {"modelo": "R3", "marca": "Yamaha", "precio": 48000, "estilo": "Deportiva", 
                 "imagen": "https://yamaha-motor.com.ar/uploads/product_images/R3.png",
                 "score": 0.85, "amigo": "maria"},
                {"modelo": "Monster", "marca": "Ducati", "precio": 89000, "estilo": "Naked", 
                 "imagen": "https://www.motofichas.com/images/phocagallery/Ducati/monster-2021/01-ducati-monster-2021-estudio-rojo.jpg",
                 "score": 0.78, "amigo": "pedro"},
                {"modelo": "Street Triple", "marca": "Triumph", "precio": 85000, "estilo": "Naked", 
                 "imagen": "https://www.motofichas.com/images/phocagallery/Triumph/street-triple-765-rs-2023/01-triumph-street-triple-765-rs-2023-estudio-gris.jpg",
                 "score": 0.72, "amigo": "jose"},
                {"modelo": "Z900", "marca": "Kawasaki", "precio": 82000, "estilo": "Naked", 
                 "imagen": "https://www.motofichas.com/images/phocagallery/Kawasaki/z900-2023/01-kawasaki-z900-2023-estudio-verde.jpg",
                 "score": 0.65, "amigo": "maria"}
            ]
        
        return render_template('recomendaciones_amigos.html', 
                              recomendaciones=friend_recommendations,
                              username=username)
    
    except Exception as e:
        current_app.logger.error(f"Error al obtener recomendaciones de amigos: {str(e)}")
        # En caso de error, mostrar un mensaje
        return render_template('error.html', 
                              error="No se pudieron cargar las recomendaciones basadas en amigos",
                              username=username)

@main.route('/recomendador')
def recomendador():
    """
    Ruta para mostrar recomendaciones usando el nuevo sistema corregido,
    con fallback al sistema antiguo en caso de error.
    """
    # Verificar si el usuario está logueado
    if 'username' not in session:
        return redirect(url_for('main.login'))
    
    usuario = session.get('username')
    
    try:
        # Usar el nuevo sistema de recomendaciones corregido
        logger.info(f"Generando recomendaciones para {usuario} con el sistema corregido")
        recomendaciones = get_recommendations_for_user(current_app, usuario, top_n=5)
        motos_recomendadas = format_recommendations_for_display(recomendaciones)
        
        # Si no hay recomendaciones, usar el método alternativo
        if not motos_recomendadas:
            logger.warning(f"Sin recomendaciones del nuevo sistema para {usuario}, usando alternativo")
            # Usar el sistema antiguo como fallback
            recomendaciones = get_moto_ideal(usuario, top_n=5)
            motos_recomendadas = []
            for moto in recomendaciones:
                motos_recomendadas.append({
                    'id': moto.get('moto_id', ''),
                    'modelo': moto.get('modelo', f"Moto {moto.get('moto_id')}"),
                    'marca': moto.get('marca', 'Desconocida'),
                    'estilo': moto.get('tipo', 'Estándar'),
                    'precio': moto.get('precio', 0),
                    'imagen': moto.get('imagen', 'https://www.motofichas.com/images/phocagallery/Kawasaki/ninja-zx-10r-2021/01-kawasaki-ninja-zx-10r-2024-performance-estudio-verde.jpg'),
                    'score': moto.get('score', 0),
                    'razones': moto.get('reasons', [])
                })
        
        return render_template('recomendaciones.html', 
                               usuario=usuario,
                               motos_recomendadas=motos_recomendadas,
                               test_data={})
    except Exception as e:
        logger.error(f"Error en recomendador: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Mostrar página con mensaje de error
        return render_template('recomendaciones.html', 
                               usuario=usuario,
                               error="Hubo un problema al generar recomendaciones. Inténtalo más tarde.",
                               motos_recomendadas=[],
                               test_data={})

@main.route('/test_moto_ideal', methods=['GET', 'POST'])
def test_moto_ideal():
    """Página de test para encontrar la moto ideal y generar recomendaciones."""
    if 'username' not in session:
        return redirect(url_for('main.login'))
    
    username = session.get('username')
    user_id = session.get('user_id')
    
    # Si es POST, procesar formulario
    if request.method == 'POST':
        try:
            # Recopilar datos del formulario
            experiencia = request.form.get('experiencia', 'principiante')
            presupuesto = request.form.get('presupuesto', '8000')
            uso = request.form.get('uso', 'urbano')
            reset_recommendation = request.form.get('reset_recommendation', 'false') == 'true'
            
            # Crear diccionario de preferencias
            test_data = {
                'experiencia': experiencia,
                'presupuesto': presupuesto,
                'uso': uso,
                'reset': reset_recommendation
            }
            
            # Guardar en sesión
            session['test_data'] = test_data
            
            # Registrar datos
            current_app.logger.info(f"Test completado por {username}: {test_data}")
            
            # Enviar usuario a página de recomendaciones donde se usarán estos datos
            return redirect(url_for('main.recomendaciones'))
            
        except Exception as e:
            current_app.logger.error(f"Error al procesar test: {str(e)}")
            flash("Ocurrió un error al procesar tus respuestas. Por favor intenta nuevamente.", "error")
    
    # Si es GET, mostrar página de test
    return render_template('test_moto_ideal.html')

@main.route('/moto_ideal', methods=['GET', 'POST'])
def moto_ideal():
    """Página de moto ideal con soporte para GET y POST"""
    if 'username' not in session:
        flash('Debes iniciar sesión para ver tu moto ideal', 'warning')
        return redirect(url_for('main.login'))
    
    username = session.get('username')
    
    # Si es POST, procesar datos y luego redirigir
    if request.method == 'POST':
        # Procesar los datos del formulario
        test_data = {
            'experiencia': request.form.get('experiencia', 'principiante'),
            'presupuesto': request.form.get('presupuesto', '8000'),
            'uso': request.form.get('uso', ''),
            'reset_recommendation': request.form.get('reset_recommendation', 'true')
        }
        
        logger.info(f"Datos del test recibidos en moto_ideal: {test_data}")
        
        # Guardar datos
        try:
            from app.utils import store_user_test_results
            success = store_user_test_results(username, test_data)
            
            if success:
                flash("Preferencias guardadas correctamente", "success")
            else:
                flash("No se pudieron guardar las preferencias", "warning")
                
        except Exception as e:
            logger.error(f"Error al guardar preferencias: {str(e)}")
            flash(f"Error al guardar preferencias: {str(e)}", "error")
        
        # Redirigir a la versión GET con reset
        return redirect(url_for('main.moto_ideal', reset='true'))
    
    # Si es GET, mostrar la moto ideal del usuario
    try:
        # Verificar si se solicitó reset (desde el test)
        reset_requested = request.args.get('reset') == 'true'
        
        # Intentar obtener el ID de la moto ideal desde la sesión o la base de datos
        moto_id = session.get('ideal_moto_id')
        
        # Obtener el adaptador
        adapter = current_app.config.get('MOTO_RECOMMENDER')
        
        # Obtener datos de la moto ideal si está disponible
        moto_data = None
        
        if adapter and moto_id:
            try:
                if hasattr(adapter, 'get_moto_by_id'):
                    moto_data = adapter.get_moto_by_id(moto_id)
            except Exception as e:
                logger.error(f"Error al obtener moto ideal: {str(e)}")
        
        # Si tenemos datos de la moto, mostrarlos
        if moto_data:
            return render_template('moto_ideal.html', moto=moto_data)
        
        # Si no hay moto ideal o hay reset, intentar obtener recomendaciones
        if reset_requested or not moto_id:
            try:
                from app.utils import get_moto_ideal
                recomendaciones = get_moto_ideal(username, force_random=reset_requested)
                
                # Si hay recomendaciones, mostrar la primera
                if recomendaciones and len(recomendaciones) > 0:
                    return render_template('moto_ideal.html', moto=recomendaciones[0])
            except Exception as e:
                logger.error(f"Error al obtener recomendaciones: {str(e)}")
        
        # Obtener listas de marcas y estilos disponibles
        marcas = ["Honda", "Yamaha", "Kawasaki", "Suzuki"]
        estilos = ["Naked", "Deportiva", "Adventure", "Scooter"]
        
        if adapter and hasattr(adapter, 'motos_df') and adapter.motos_df is not None:
            try:
                marcas = adapter.motos_df['marca'].unique().tolist()
                estilos = adapter.motos_df['tipo'].unique().tolist()
            except Exception:
                pass
        
        # Mostrar mensaje si no hay moto ideal
        return render_template('moto_ideal.html',
                              error="No se pudo generar una recomendación personalizada. ¡Completa el test!",
                              marcas=marcas,
                              estilos=estilos)
                              
    except Exception as e:
        logger.error(f"Error al mostrar moto ideal: {str(e)}")
        logger.error(traceback.format_exc())
        
        return render_template('moto_ideal.html',
                              error="Ocurrió un error al procesar tu recomendación. Inténtalo de nuevo.",
                              marcas=["Honda", "Yamaha", "Kawasaki", "Suzuki"],
                              estilos=["Naked", "Deportiva", "Adventure", "Scooter"])

@main.route('/guardar-preferencias', methods=['POST'])
def guardar_preferencias():
    """
    Guarda las preferencias del usuario en la base de datos.
    Esta ruta recibe datos de preferencias de motos (estilos, marcas, etc.)
    y los almacena en Neo4j para usarlos en futuras recomendaciones.
    """
    username = session.get('username')
    if not username:
        return jsonify({"success": False, "message": "Usuario no autenticado"}), 401
    
    try:
        # Obtener datos del formulario
        preferences = {
            'estilos': {},
            'marcas': {},
            'experiencia': request.form.get('experiencia', 'Intermedio')
        }
        
        # Procesar estilos
        estilos_str = request.form.get('estilos', '{}')
        try:
            preferences['estilos'] = json.loads(estilos_str.replace("'", '"'))
        except:
            current_app.logger.error("Error al procesar JSON de estilos")
            
        # Procesar marcas
        marcas_str = request.form.get('marcas', '{}')
        try:
            preferences['marcas'] = json.loads(marcas_str.replace("'", '"'))
        except:
            current_app.logger.error("Error al procesar JSON de marcas")
        
        # Guardar en la sesión
        session['test_data'] = preferences
        
        # Guardar en Neo4j usando la función mejorada
        result = store_user_test_results(username, preferences)
        
        if result:
            current_app.logger.info(f"Preferencias guardadas correctamente para {username}")
            return jsonify({"success": True, "message": "Preferencias guardadas correctamente"})
        else:
            current_app.logger.warning(f"No se pudieron guardar las preferencias para {username}")
            return jsonify({"success": False, "message": "No se pudieron guardar las preferencias en la base de datos"}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error al guardar preferencias: {str(e)}")
        return jsonify({"success": False, "message": f"Error al procesar la solicitud: {str(e)}"}), 500

@main.route('/recomendaciones-amigos')
def recomendaciones_amigos():
    """
    Muestra recomendaciones de motos basadas en los gustos de los amigos del usuario.
    Utiliza el algoritmo de propagación de etiquetas para generar recomendaciones.
    """
    username = session.get('username')
    if not username:
        return redirect(url_for('main.login'))
    
    try:
        # Obtener recomendaciones basadas en amigos
        friend_recommendations = get_friend_recommendations(username, top_n=4)
        
        if not friend_recommendations:
            # Si no hay recomendaciones de la base de datos, usar datos simulados
            friend_recommendations = [
                {"modelo": "R3", "marca": "Yamaha", "precio": 48000, "estilo": "Deportiva", 
                 "imagen": "https://yamaha-motor.com.ar/uploads/product_images/R3.png",
                 "score": 0.85, "amigo": "maria"},
                {"modelo": "Monster", "marca": "Ducati", "precio": 89000, "estilo": "Naked", 
                 "imagen": "https://www.motofichas.com/images/phocagallery/Ducati/monster-2021/01-ducati-monster-2021-estudio-rojo.jpg",
                 "score": 0.78, "amigo": "pedro"},
                {"modelo": "Street Triple", "marca": "Triumph", "precio": 85000, "estilo": "Naked", 
                 "imagen": "https://www.motofichas.com/images/phocagallery/Triumph/street-triple-765-rs-2023/01-triumph-street-triple-765-rs-2023-estudio-gris.jpg",
                 "score": 0.72, "amigo": "jose"},
                {"modelo": "Z900", "marca": "Kawasaki", "precio": 82000, "estilo": "Naked", 
                 "imagen": "https://www.motofichas.com/images/phocagallery/Kawasaki/z900-2023/01-kawasaki-z900-2023-estudio-verde.jpg",
                 "score": 0.65, "amigo": "maria"}
            ]
        
        return render_template('recomendaciones_amigos.html', 
                              recomendaciones=friend_recommendations,
                              username=username)
    
    except Exception as e:
        current_app.logger.error(f"Error al obtener recomendaciones de amigos: {str(e)}")
        # En caso de error, mostrar un mensaje
        return render_template('error.html', 
                              error="No se pudieron cargar las recomendaciones basadas en amigos",
                              username=username)

@main.route('/recomendador')
def recomendador():
    """
    Ruta para mostrar recomendaciones usando el nuevo sistema corregido,
    con fallback al sistema antiguo en caso de error.
    """
    # Verificar si el usuario está logueado
    if 'username' not in session:
        return redirect(url_for('main.login'))
    
    usuario = session.get('username')
    
    try:
        # Usar el nuevo sistema de recomendaciones corregido
        logger.info(f"Generando recomendaciones para {usuario} con el sistema corregido")
        recomendaciones = get_recommendations_for_user(current_app, usuario, top_n=5)
        motos_recomendadas = format_recommendations_for_display(recomendaciones)
        
        # Si no hay recomendaciones, usar el método alternativo
        if not motos_recomendadas:
            logger.warning(f"Sin recomendaciones del nuevo sistema para {usuario}, usando alternativo")
            # Usar el sistema antiguo como fallback
            recomendaciones = get_moto_ideal(usuario, top_n=5)
            motos_recomendadas = []
            for moto in recomendaciones:
                motos_recomendadas.append({
                    'id': moto.get('moto_id', ''),
                    'modelo': moto.get('modelo', f"Moto {moto.get('moto_id')}"),
                    'marca': moto.get('marca', 'Desconocida'),
                    'estilo': moto.get('tipo', 'Estándar'),
                    'precio': moto.get('precio', 0),
                    'imagen': moto.get('imagen', 'https://www.motofichas.com/images/phocagallery/Kawasaki/ninja-zx-10r-2021/01-kawasaki-ninja-zx-10r-2024-performance-estudio-verde.jpg'),
                    'score': moto.get('score', 0),
                    'razones': moto.get('reasons', [])
                })
        
        return render_template('recomendaciones.html', 
                               usuario=usuario,
                               motos_recomendadas=motos_recomendadas,
                               test_data={})
    except Exception as e:
        logger.error(f"Error en recomendador: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Mostrar página con mensaje de error
        return render_template('recomendaciones.html', 
                               usuario=usuario,
                               error="Hubo un problema al generar recomendaciones. Inténtalo más tarde.",
                               motos_recomendadas=[],
                               test_data={})

@main.route('/test_moto_ideal', methods=['GET', 'POST'])
def test_moto_ideal():
    """Página de test para encontrar la moto ideal y generar recomendaciones."""
    if 'username' not in session:
        return redirect(url_for('main.login'))
    
    username = session.get('username')
    user_id = session.get('user_id')
    
    # Si es POST, procesar formulario
    if request.method == 'POST':
        try:
            # Recopilar datos del formulario
            experiencia = request.form.get('experiencia', 'principiante')
            presupuesto = request.form.get('presupuesto', '8000')
            uso = request.form.get('uso', 'urbano')
            reset_recommendation = request.form.get('reset_recommendation', 'false') == 'true'
            
            # Crear diccionario de preferencias
            test_data = {
                'experiencia': experiencia,
                'presupuesto': presupuesto,
                'uso': uso,
                'reset': reset_recommendation
            }
            
            # Guardar en sesión
            session['test_data'] = test_data
            
            # Registrar datos
            current_app.logger.info(f"Test completado por {username}: {test_data}")
            
            # Enviar usuario a página de recomendaciones donde se usarán estos datos
            return redirect(url_for('main.recomendaciones'))
            
        except Exception as e:
            current_app.logger.error(f"Error al procesar test: {str(e)}")
            flash("Ocurrió un error al procesar tus respuestas. Por favor intenta nuevamente.", "error")
    
    # Si es GET, mostrar página de test
    return render_template('test_moto_ideal.html')

@main.route('/moto_ideal', methods=['GET', 'POST'])
def moto_ideal():
    """Página de moto ideal con soporte para GET y POST"""
    if 'username' not in session:
        flash('Debes iniciar sesión para ver tu moto ideal', 'warning')
        return redirect(url_for('main.login'))
    
    username = session.get('username')
    
    # Si es POST, procesar datos y luego redirigir
    if request.method == 'POST':
        # Procesar los datos del formulario
        test_data = {
            'experiencia': request.form.get('experiencia', 'principiante'),
            'presupuesto': request.form.get('presupuesto', '8000'),
            'uso': request.form.get('uso', ''),
            'reset_recommendation': request.form.get('reset_recommendation', 'true')
        }
        
        logger.info(f"Datos del test recibidos en moto_ideal: {test_data}")
        
        # Guardar datos
        try:
            from app.utils import store_user_test_results
            success = store_user_test_results(username, test_data)
            
            if success:
                flash("Preferencias guardadas correctamente", "success")
            else:
                flash("No se pudieron guardar las preferencias", "warning")
                
        except Exception as e:
            logger.error(f"Error al guardar preferencias: {str(e)}")
            flash(f"Error al guardar preferencias: {str(e)}", "error")
        
        # Redirigir a la versión GET con reset
        return redirect(url_for('main.moto_ideal', reset='true'))
    
    # Si es GET, mostrar la moto ideal del usuario
    try:
        # Verificar si se solicitó reset (desde el test)
        reset_requested = request.args.get('reset') == 'true'
        
        # Intentar obtener el ID de la moto ideal desde la sesión o la base de datos
        moto_id = session.get('ideal_moto_id')
        
        # Obtener el adaptador
        adapter = current_app.config.get('MOTO_RECOMMENDER')
        
        # Obtener datos de la moto ideal si está disponible
        moto_data = None
        
        if adapter and moto_id:
            try:
                if hasattr(adapter, 'get_moto_by_id'):
                    moto_data = adapter.get_moto_by_id(moto_id)
            except Exception as e:
                logger.error(f"Error al obtener moto ideal: {str(e)}")
        
        # Si tenemos datos de la moto, mostrarlos
        if moto_data:
            return render_template('moto_ideal.html', moto=moto_data)
        
        # Si no hay moto ideal o hay reset, intentar obtener recomendaciones
        if reset_requested or not moto_id:
            try:
                from app.utils import get_moto_ideal
                recomendaciones = get_moto_ideal(username, force_random=reset_requested)
                
                # Si hay recomendaciones, mostrar la primera
                if recomendaciones and len(recomendaciones) > 0:
                    return render_template('moto_ideal.html', moto=recomendaciones[0])
            except Exception as e:
                logger.error(f"Error al obtener recomendaciones: {str(e)}")
        
        # Obtener listas de marcas y estilos disponibles
        marcas = ["Honda", "Yamaha", "Kawasaki", "Suzuki"]
        estilos = ["Naked", "Deportiva", "Adventure", "Scooter"]
        
        if adapter and hasattr(adapter, 'motos_df') and adapter.motos_df is not None:
            try:
                marcas = adapter.motos_df['marca'].unique().tolist()
                estilos = adapter.motos_df['tipo'].unique().tolist()
            except Exception:
                pass
        
        # Mostrar mensaje si no hay moto ideal
        return render_template('moto_ideal.html',
                              error="No se pudo generar una recomendación personalizada. ¡Completa el test!",
                              marcas=marcas,
                              estilos=estilos)
                              
    except Exception as e:
        logger.error(f"Error al mostrar moto ideal: {str(e)}")
        logger.error(traceback.format_exc())
        
        return render_template('moto_ideal.html',
                              error="Ocurrió un error al procesar tu recomendación. Inténtalo de nuevo.",
                              marcas=["Honda", "Yamaha", "Kawasaki", "Suzuki"],
                              estilos=["Naked", "Deportiva", "Adventure", "Scooter"])

@main.route('/guardar-preferencias', methods=['POST'])
def guardar_preferencias():
    """
    Guarda las preferencias del usuario en la base de datos.
    Esta ruta recibe datos de preferencias de motos (estilos, marcas, etc.)
    y los almacena en Neo4j para usarlos en futuras recomendaciones.
    """
    username = session.get('username')
    if not username:
        return jsonify({"success": False, "message": "Usuario no autenticado"}), 401
    
    try:
        # Obtener datos del formulario
        preferences = {
            'estilos': {},
            'marcas': {},
            'experiencia': request.form.get('experiencia', 'Intermedio')
        }
        
        # Procesar estilos
        estilos_str = request.form.get('estilos', '{}')
        try:
            preferences['estilos'] = json.loads(estilos_str.replace("'", '"'))
        except:
            current_app.logger.error("Error al procesar JSON de estilos")
            
        # Procesar marcas
        marcas_str = request.form.get('marcas', '{}')
        try:
            preferences['marcas'] = json.loads(marcas_str.replace("'", '"'))
        except:
            current_app.logger.error("Error al procesar JSON de marcas")
        
        # Guardar en la sesión
        session['test_data'] = preferences
        
        # Guardar en Neo4j usando la función mejorada
        result = store_user_test_results(username, preferences)
        
        if result:
            current_app.logger.info(f"Preferencias guardadas correctamente para {username}")
            return jsonify({"success": True, "message": "Preferencias guardadas correctamente"})
        else:
            current_app.logger.warning(f"No se pudieron guardar las preferencias para {username}")
            return jsonify({"success": False, "message": "No se pudieron guardar las preferencias en la base de datos"}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error al guardar preferencias: {str(e)}")
        return jsonify({"success": False, "message": f"Error al procesar la solicitud: {str(e)}"}), 500

@main.route('/recomendaciones-amigos')
def recomendaciones_amigos():
    """
    Muestra recomendaciones de motos basadas en los gustos de los amigos del usuario.
    Utiliza el algoritmo de propagación de etiquetas para generar recomendaciones.
    """
    username = session.get('username')
    if not username:
        return redirect(url_for('main.login'))
    
    try:
        # Obtener recomendaciones basadas en amigos
        friend_recommendations = get_friend_recommendations(username, top_n=4)
        
        if not friend_recommendations:
            # Si no hay recomendaciones de la base de datos, usar datos simulados
            friend_recommendations = [
                {"modelo": "R3", "marca": "Yamaha", "precio": 48000, "estilo": "Deportiva", 
                 "imagen": "https://yamaha-motor.com.ar/uploads/product_images/R3.png",
                 "score": 0.85, "amigo": "maria"},
                {"modelo": "Monster", "marca": "Ducati", "precio": 89000, "estilo": "Naked", 
                 "imagen": "https://www.motofichas.com/images/phocagallery/Ducati/monster-2021/01-ducati-monster-2021-estudio-rojo.jpg",
                 "score": 0.78, "amigo": "pedro"},
                {"modelo": "Street Triple", "marca": "Triumph", "precio": 85000, "estilo": "Naked", 
                 "imagen": "https://www.motofichas.com/images/phocagallery/Triumph/street-triple-765-rs-2023/01-triumph-street-triple-765-rs-2023-estudio-gris.jpg",
                 "score": 0.72, "amigo": "jose"},
                {"modelo": "Z900", "marca": "Kawasaki", "precio": 82000, "estilo": "Naked", 
                 "imagen": "https://www.motofichas.com/images/phocagallery/Kawasaki/z900-2023/01-kawasaki-z900-2023-estudio-verde.jpg",
                 "score": 0.65, "amigo": "maria"}
            ]
        
        return render_template('recomendaciones_amigos.html', 
                              recomendaciones=friend_recommendations,
                              username=username)
    
    except Exception as e:
        current_app.logger.error(f"Error al obtener recomendaciones de amigos: {str(e)}")
        # En caso de error, mostrar un mensaje
        return render_template('error.html', 
                              error="No se pudieron cargar las recomendaciones basadas en amigos",
                              username=username)

@main.route('/recomendador')
def recomendador():
    """
    Ruta para mostrar recomendaciones usando el nuevo sistema corregido,
    con fallback al sistema antiguo en caso de error.
    """
    # Verificar si el usuario está logueado
    if 'username' not in session:
        return redirect(url_for('main.login'))
    
    usuario = session.get('username')
    
    try:
        # Usar el nuevo sistema de recomendaciones corregido
        logger.info(f"Generando recomendaciones para {usuario} con el sistema corregido")
        recomendaciones = get_recommendations_for_user(current_app, usuario, top_n=5)
        motos_recomendadas = format_recommendations_for_display(recomendaciones)
        
        # Si no hay recomendaciones, usar el método alternativo
        if not motos_recomendadas:
            logger.warning(f"Sin recomendaciones del nuevo sistema para {usuario}, usando alternativo")
            # Usar el sistema antiguo como fallback
            recomendaciones = get_moto_ideal(usuario, top_n=5)
            motos_recomendadas = []
            for moto in recomendaciones:
                motos_recomendadas.append({
                    'id': moto.get('moto_id', ''),
                    'modelo': moto.get('modelo', f"Moto {moto.get('moto_id')}"),
                    'marca': moto.get('marca', 'Desconocida'),
                    'estilo': moto.get('tipo', 'Estándar'),
                    'precio': moto.get('precio', 0),
                    'imagen': moto.get('imagen', 'https://www.motofichas.com/images/phocagallery/Kawasaki/ninja-zx-10r-2021/01-kawasaki-ninja-zx-10r-2024-performance-estudio-verde.jpg'),
                    'score': moto.get('score', 0),
                    'razones': moto.get('reasons', [])
                })
        
        return render_template('recomendaciones.html', 
                               usuario=usuario,
                               motos_recomendadas=motos_recomendadas,
                               test_data={})
    except Exception as e:
        logger.error(f"Error en recomendador: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Mostrar página con mensaje de error
        return render_template('recomendaciones.html', 
                               usuario=usuario,
                               error="Hubo un problema al generar recomendaciones. Inténtalo más tarde.",
                               motos_recomendadas=[],
                               test_data={})

@main.route('/test_moto_ideal', methods=['GET', 'POST'])
def test_moto_ideal():
    """Página de test para encontrar la moto ideal y generar recomendaciones."""
    if 'username' not in session:
        return redirect(url_for('main.login'))
    
    username = session.get('username')
    user_id = session.get('user_id')
    
    # Si es POST, procesar formulario
    if request.method == 'POST':
        try:
            # Recopilar datos del formulario
            experiencia = request.form.get('experiencia', 'principiante')
            presupuesto = request.form.get('presupuesto', '8000')
            uso = request.form.get('uso', 'urbano')
            reset_recommendation = request.form.get('reset_recommendation', 'false') == 'true'
            
            # Crear diccionario de preferencias
            test_data = {
                'experiencia': experiencia,
                'presupuesto': presupuesto,
                'uso': uso,
                'reset': reset_recommendation
            }
            
            # Guardar en sesión
            session['test_data'] = test_data
            
            # Registrar datos
            current_app.logger.info(f"Test completado por {username}: {test_data}")
            
            # Enviar usuario a página de recomendaciones donde se usarán estos datos
            return redirect(url_for('main.recomendaciones'))
            
        except Exception as e:
            current_app.logger.error(f"Error al procesar test: {str(e)}")
            flash("Ocurrió un error al procesar tus respuestas. Por favor intenta nuevamente.", "error")
    
    # Si es GET, mostrar página de test
    return render_template('test_moto_ideal.html')